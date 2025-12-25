from amsdal_server.apps.healthcheck.enums import StatusEnum
from amsdal_server.apps.healthcheck.serializers.healthcheck_result import HealthcheckResult
from amsdal_server.apps.healthcheck.services.checkers.base import BaseHealthchecker


class HealthcheckService:
    def __init__(self, conditions: list[BaseHealthchecker]):
        self.__conditions = conditions

    async def healthcheck(self) -> HealthcheckResult:
        results = []
        status = StatusEnum.success

        for condition in self.__conditions:
            condition_check = await condition.check()

            if condition_check.status == StatusEnum.error:
                status = StatusEnum.error

            results.append(condition_check)

        return HealthcheckResult(status=status, details=results)

    def add_condition(self, condition: BaseHealthchecker) -> None:
        self.__conditions.append(condition)
