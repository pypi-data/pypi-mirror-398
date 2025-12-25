import asyncio
import logging
from contextlib import contextmanager
from typing import Callable

import azure.functions as func

from warpzone.function.types import SingleArgumentCallable
from warpzone.monitor import logs, traces

SUBJECT_IDENTIFIER = "<Subject>"

tracer = traces.get_tracer(__name__)
logger = logs.get_logger(__name__)


def configure_monitoring():
    """
    Configure logging and tracing on Azure Function to
    - export telemetry to App Insights
    - suppress spamming logs
    """
    # disable logging for HTTP calls to avoid log spamming
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )

    # disable logging for Service Bus underlying uAMQP library to avoid log spamming
    logging.getLogger("uamqp").setLevel(logging.WARNING)

    # configure tracer provider
    traces.configure_tracing()

    # configure logger provider
    logs.configure_logging()


@contextmanager
def run_in_trace_context(context: func.Context):
    configure_monitoring()

    trace_context = context.trace_context
    with traces.set_trace_context(
        trace_context.trace_parent, trace_context.trace_state
    ):
        yield


def monitor(main: SingleArgumentCallable) -> Callable:
    """Wrap Azure function with logging and tracing
    configured for monitoring in App Insights.

    Args:
        f (SingleArgumentCallable): Azure function to be wrapped

    Returns:
        Callable: Azure function with
            - argument
                name: "arg"
                description: argument of the original function
            - argument
                name: "context"
                description: Azure function context
            - return value
                description: return value of original function
    """

    async def wrapper_async(arg, context: func.Context):
        with run_in_trace_context(context):
            result = await main(arg)
            return result

    def wrapper(arg, context: func.Context):
        with run_in_trace_context(context):
            result = main(arg)
            return result

    if asyncio.iscoroutinefunction(main):
        return wrapper_async
    else:
        return wrapper
