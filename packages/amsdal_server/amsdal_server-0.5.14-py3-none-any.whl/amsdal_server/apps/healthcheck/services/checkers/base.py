from amsdal_server.apps.healthcheck.serializers.healthcheck_result import HealthcheckServiceResult


class BaseHealthchecker:
    async def check(self) -> HealthcheckServiceResult:
        raise NotImplementedError()
