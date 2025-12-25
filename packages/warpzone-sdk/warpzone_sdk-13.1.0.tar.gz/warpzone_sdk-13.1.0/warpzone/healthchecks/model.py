from enum import Enum
from typing import Optional, Protocol


class HealthStatus(Enum):
    HEALTHY = 1
    UNHEALTHY = 2


class HealthCheckResult:
    status: HealthStatus
    description: Optional[str]
    exception: Optional[Exception]

    def __init__(
        self,
        status: HealthStatus,
        description: Optional[str] = None,
        exception: Optional[Exception] = None,
    ) -> None:
        if exception is not None:
            assert status == HealthStatus.UNHEALTHY

        self.status = status
        self.description = description
        self.exception = exception

    def passed(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    @classmethod
    def healthy(cls):
        return HealthCheckResult(
            status=HealthStatus.HEALTHY, description="Health check OK."
        )


class HealthCheckable(Protocol):
    """
    Defines the interface of a class whose health can be checked.
    """

    def check_health(self) -> HealthCheckResult:
        """
        This method should be overridden to perform a check of the
        object's health (however that may be defined) and returning the result.
        """
        pass
