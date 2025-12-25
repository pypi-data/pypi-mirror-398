import azure.functions as func

from warpzone.healthchecks.model import HealthCheckable, HealthCheckResult, HealthStatus
from warpzone.monitor import get_logger


def check_health_of(*objects_to_check: HealthCheckable) -> HealthCheckResult:
    """
    Calls the check_health method of each object in turn and returns either the first
    failing result or, if all checks pass, a standard healthy result.
    """
    for obj in objects_to_check:
        health_check = obj.check_health()

        if not health_check.passed():
            return health_check

    return HealthCheckResult.healthy()


def format_status_msg(health_check: HealthCheckResult, context_name: str) -> str:
    status_msg = (
        f"Health check failed. Reason: {health_check.description}"
        if health_check.status == HealthStatus.UNHEALTHY
        else "Health check OK."
    )

    return f"{context_name}: {status_msg}"


def create_error_log_msg(health_check: HealthCheckResult, context_name: str):
    status_msg = format_status_msg(health_check, context_name)

    return (
        None
        if health_check.status == HealthStatus.HEALTHY
        else f"""
        {status_msg}

        Exception raised: {type(health_check.exception).__name__}
        Message: {health_check.exception}
        """
    )


def create_http_response(health_check: HealthCheckResult, context_name: str):
    status_msg = format_status_msg(health_check, context_name)

    return func.HttpResponse(
        body=status_msg, status_code=200 if health_check.passed() else 500
    )


def run_health_check(context_name: str, *objects_to_check: HealthCheckable):
    """
    Checks the health of each object in turn and returns the result as a
    HTTP response indicating either success (200) or failure (500).
    """
    logger = get_logger(__name__)
    logger.info(f"{context_name}: Health check initialized.")

    health_check = check_health_of(*objects_to_check)

    if not health_check.passed():
        logger.error(create_error_log_msg(health_check, context_name))

    return create_http_response(health_check, context_name)
