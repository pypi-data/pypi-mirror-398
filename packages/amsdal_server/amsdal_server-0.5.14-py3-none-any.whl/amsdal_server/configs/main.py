import importlib
import logging.config
from datetime import timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from amsdal_server.configs.constants import DEVELOPMENT_ENVIRONMENT
from amsdal_server.configs.constants import PRODUCTION_ENVIRONMENT
from amsdal_server.configs.constants import TESTING_ENVIRONMENT
from amsdal_server.configs.constants import check_force_test_environment


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix='AMSDAL_SERVER_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    APP_NAME: str = 'amsdal-server'
    DEBUG: bool = False
    IS_DOCS_ENABLED: bool = True
    ENVIRONMENT: str = ''

    HOST: str = '0.0.0.0'  # noqa: S104
    PORT: int = 80

    THUMBNAIL_CACHE_PATH: Path = Path('.cache-thumbnails')
    THUMBNAIL_CACHE_BITES_LIMIT: str = '2G'
    THUMBNAIL_CACHE_AGE_LIMIT: timedelta = timedelta(days=30)

    AUTHORIZATION_HEADER: str = 'Authorization'

    SLACK_WEBHOOK_URL: str | None = None
    SLACK_INCLUDE_REQUEST_BODY: bool = False

    INSTALLED_APPS: list[str] = Field(
        default=[
            'amsdal_server.apps.classes',
            'amsdal_server.apps.objects',
            'amsdal_server.apps.transactions',
            'amsdal_server.apps.common',
            'amsdal_server.apps.healthcheck',
        ]
    )

    OTLP_ENDPOINT: str | None = None

    MIDDLEWARES: list[str | tuple[str, dict[str, Any]]] = Field(
        default=[
            'amsdal_server.apps.common.middlewares.response_event.ResponseEventMiddleware',
            'amsdal_server.apps.common.middlewares.slack_middleware.SlackNotificationMiddleware',
            (
                'starlette.middleware.cors.CORSMiddleware',
                {
                    'allow_origins': ['*'],
                    'allow_methods': ['*'],
                    'allow_headers': ['*'],
                    'allow_credentials': True,
                    'expose_headers': ['X-Request-ID'],
                },
            ),
            (
                'starlette.middleware.authentication.AuthenticationMiddleware',
                {
                    'backend': 'amsdal_server.apps.common.authentication.AmsdalAuthenticationBackend',
                },
            ),
            'amsdal_server.apps.common.middlewares.logger.LoggerMiddleware',
            'asgi_correlation_id.CorrelationIdMiddleware',
        ]
    )

    LOGGING_FORMAT: str = (
        '%(levelname)-8s [%(asctime)s] %(message)s %(name)s.%(funcName)s:%(lineno)d [%(correlation_id)s]'
    )
    LOGGING_INTERNAL_LOG_LEVEL: str = 'WARNING'
    LOGGING_LOG_LEVEL: str = 'INFO'
    LOGGING_ROOT_LOG_LEVEL: str = 'INFO'
    LOGGING_HANDLERS: list[str] = Field(default=['default'])
    LOGGING: dict[str, Any] = Field(default_factory=dict)

    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, value: str | None) -> str:
        valid_environments = (
            TESTING_ENVIRONMENT,
            DEVELOPMENT_ENVIRONMENT,
            PRODUCTION_ENVIRONMENT,
        )

        if not value:
            value = DEVELOPMENT_ENVIRONMENT

        if value not in valid_environments:
            msg = f'Invalid environment. Valid environments are: {valid_environments}'
            raise ValueError(msg)

        return check_force_test_environment(default=value)

    @field_validator('INSTALLED_APPS')
    @classmethod
    def load_installed_apps(cls, values: list[str]) -> list[ModuleType]:
        return [importlib.import_module(module) for module in values]

    @model_validator(mode='after')
    def validate_logging(self) -> 'Settings':
        self.LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': self.LOGGING_FORMAT,
                    'style': '%',
                    'use_colors': True,
                },
            },
            'filters': {
                'correlation_id': {
                    '()': 'asgi_correlation_id.CorrelationIdFilter',
                    'uuid_length': 32,
                },
            },
            'handlers': {
                'default': {
                    'class': 'logging.StreamHandler',
                    'filters': ['correlation_id'],
                    'level': self.LOGGING_LOG_LEVEL,
                    'formatter': 'default',
                },
                'null': {
                    'class': 'logging.NullHandler',
                },
            },
            'loggers': {
                'httpx': {
                    'handlers': ['default'],
                    'level': self.LOGGING_INTERNAL_LOG_LEVEL,
                    'propagate': True,
                },
                'httpcore': {
                    'handlers': ['default'],
                    'level': self.LOGGING_INTERNAL_LOG_LEVEL,
                    'propagate': True,
                },
                # app logger
                'amsdal_server': {
                    'level': self.LOGGING_LOG_LEVEL,
                    'propagate': True,
                },
            },
            'root': {
                'level': self.LOGGING_ROOT_LOG_LEVEL,
                'propagate': True,
                'handlers': self.LOGGING_HANDLERS,
            },
        }

        for logger in self.LOGGING['loggers'].values():
            if 'handlers' not in logger:
                logger['handlers'] = self.LOGGING_HANDLERS

        return self


settings = Settings()
logging.config.dictConfig(settings.LOGGING)
