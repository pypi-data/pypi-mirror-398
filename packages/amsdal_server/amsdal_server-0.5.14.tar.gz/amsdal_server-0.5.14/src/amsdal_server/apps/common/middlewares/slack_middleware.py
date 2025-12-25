import asyncio
import logging
import traceback
from datetime import UTC
from datetime import datetime

import httpx
from asgi_correlation_id.context import correlation_id
from fastapi import Request
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SlackNotificationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        slack_webhook_url: str | None = None,
        environment: str = 'production',
        excluded_paths: list[str] | None = None,
        excluded_status_codes: list[int] | None = None,
        *,
        include_request_body: bool | None = None,
    ) -> None:
        super().__init__(app)

        from amsdal_server.configs.main import settings

        self.slack_webhook_url = slack_webhook_url or settings.SLACK_WEBHOOK_URL
        self.environment = environment or settings.ENVIRONMENT
        self.include_request_body = (
            include_request_body if include_request_body is not None else settings.SLACK_INCLUDE_REQUEST_BODY
        )
        self.excluded_paths = excluded_paths or ['/health', '/metrics']
        self.app_name = settings.APP_NAME
        self.excluded_status_codes = excluded_status_codes or [404]

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Skip notification for excluded paths
            if any(path in str(request.url) for path in self.excluded_paths):
                raise

            # Send notification to Slack only if webhook URL is configured
            if self.slack_webhook_url:
                asyncio.create_task(self._send_slack_notification(request, exc))  # noqa: RUF006

            raise

    async def _send_slack_notification(self, request: Request, exception: Exception) -> None:
        """Send exception notification to Slack"""
        if not self.slack_webhook_url:
            return

        try:
            # Get request body if configured
            request_body = ''
            if self.include_request_body:
                try:
                    body = await request.body()
                    request_body = body.decode('utf-8')[:1000]  # Limit to 1000 chars
                except Exception:
                    logger.exception('Failed to read request body')
                    request_body = 'Could not read request body'

            # Format exception details
            exception_details = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc(),
            }

            # Create Slack message
            slack_message = {
                'attachments': [
                    {
                        'color': 'danger',
                        'title': f'🚨 Exception in {self.app_name} [{self.environment}]',
                        'fields': [
                            {'title': 'Environment', 'value': self.environment, 'short': True},
                            {
                                'title': 'Timestamp',
                                'value': datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC'),
                                'short': True,
                            },
                            {'title': 'Method', 'value': request.method, 'short': True},
                            {'title': 'URL', 'value': str(request.url), 'short': True},
                            {'title': 'Exception Type', 'value': exception_details['type'], 'short': True},
                            {
                                'title': 'Exception Message',
                                'value': exception_details['message'][:500],  # Limit message length
                                'short': False,
                            },
                        ],
                    }
                ]
            }

            # Add request body if enabled
            if self.include_request_body and request_body:
                slack_message['attachments'][0]['fields'].append(  # type: ignore[attr-defined]
                    {'title': 'Request Body', 'value': f'```{request_body}```', 'short': False}
                )

            # Helper to safely grab and truncate headers
            def grab(hdr: str, default: str = 'unknown', max_len: int = 500) -> str:
                val = request.headers.get(hdr, default)
                return val[:max_len]

            # Determine client IP
            xff = request.headers.get('x-original-forwarded-for')
            if not xff:
                xff = request.headers.get('x-forwarded-for')

            if xff:
                # might be "client, proxy1, proxy2"
                client_ip = xff.split(',')[0].strip()
            else:
                # fallback to starlette's client info
                client_ip = getattr(request.client, 'host', 'unknown')

            # Grab other useful headers
            user_agent = grab('User-Agent')
            referer = grab('Referer', default='none')
            host_header = grab('Host', default='none')
            request_id = correlation_id.get() or 'unknown'

            slack_message['attachments'][0]['fields'].extend(  # type: ignore[attr-defined]
                [
                    {'title': 'Client IP', 'value': client_ip, 'short': True},
                    {'title': 'User-Agent', 'value': user_agent, 'short': False},
                    {'title': 'Referer', 'value': referer, 'short': False},
                    {'title': 'Host Header', 'value': host_header, 'short': True},
                    {'title': 'Request ID', 'value': request_id, 'short': True},
                ]
            )

            # Add traceback as a separate attachment
            slack_message['attachments'].append(
                {
                    'color': 'warning',
                    'title': 'Traceback',
                    'text': f'```{exception_details["traceback"][:2000]}```',  # Limit traceback length
                    'mrkdwn_in': ['text'],
                }
            )

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.slack_webhook_url, json=slack_message, headers={'Content-Type': 'application/json'}
                )
                if response.status_code != 200:  # noqa: PLR2004
                    logger.error(f'Failed to send Slack notification: {response.status_code}')

        except Exception as e:
            # Don't let notification failures break the app
            logger.exception(f'Error sending Slack notification: {e}')
