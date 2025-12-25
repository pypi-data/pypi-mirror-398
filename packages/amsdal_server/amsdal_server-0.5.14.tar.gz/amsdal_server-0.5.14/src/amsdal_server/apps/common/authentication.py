from typing import Any

from amsdal_utils.config.manager import AmsdalConfigManager
from starlette.authentication import AuthCredentials
from starlette.authentication import AuthenticationBackend
from starlette.authentication import BaseUser
from starlette.requests import HTTPConnection

from amsdal_server.configs.main import settings


class AmsdalBaseUser(BaseUser):
    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.permissions = []  # type: ignore[var-annotated]


class AmsdalUnauthenticatedUser(AmsdalBaseUser):
    @property
    def is_authenticated(self) -> bool:
        return False

    @property
    def display_name(self) -> str:
        return ''

    def __str__(self) -> str:
        return 'UnauthenticatedUser'

    def __repr__(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return False


class AuthenticationInfo:
    credentials: AuthCredentials
    user: AmsdalBaseUser

    def __init__(
        self,
        credentials: AuthCredentials | None = None,
        user: AmsdalBaseUser | None = None,
    ) -> None:
        self.credentials = credentials or AuthCredentials(['authenticated'])
        self.user = user or AmsdalUnauthenticatedUser()

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)


class AmsdalAuthenticationBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, AmsdalBaseUser] | None:
        from amsdal_utils.lifecycle.enum import LifecycleEvent
        from amsdal_utils.lifecycle.producer import LifecycleProducer

        authentication_info = AuthenticationInfo()

        if settings.AUTHORIZATION_HEADER in conn.headers:
            auth = conn.headers[settings.AUTHORIZATION_HEADER]

            if AmsdalConfigManager().get_config().async_mode:
                await LifecycleProducer.publish_async(
                    LifecycleEvent.ON_AUTHENTICATE,
                    auth_header=auth,
                    authentication_info=authentication_info,
                )
            else:
                LifecycleProducer.publish(
                    LifecycleEvent.ON_AUTHENTICATE,
                    auth_header=auth,
                    authentication_info=authentication_info,
                )
            conn.scope['user'] = authentication_info.user

        return authentication_info.credentials, authentication_info.user
