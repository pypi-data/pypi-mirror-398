# NOTE: OpenTelemetry logging to Azure is still in EXPERIMENTAL mode!
import logging
import os
from logging import StreamHandler

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry import _logs as logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

logger = logging.getLogger(__name__)
logger.addHandler(StreamHandler())

LOGGING_IS_CONFIGURED = False


def configure_logging():
    global LOGGING_IS_CONFIGURED
    if LOGGING_IS_CONFIGURED:
        # logging should only be set up once
        # to avoid duplicated log handling.
        # Global variables is the pattern used
        # by opentelemetry, so we use the same
        return

    # set up logger provider based on the Azure Function resource
    # (this is make sure App Insights can track the log source correctly)
    # (https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=net#set-the-cloud-role-name-and-the-cloud-role-instance)
    resource = Resource.create({SERVICE_NAME: os.getenv("WEBSITE_SITE_NAME")})
    logs.set_logger_provider(
        LoggerProvider(
            resource=resource,
        )
    )

    # setup azure monitor log exporter to send telemetry to App Insights
    try:
        log_exporter = AzureMonitorLogExporter()
    except ValueError:
        # if no App Insights instrumentation key is set (e.g. when running unit tests),
        # the exporter creation will fail. In this case we skip it
        logger.warning(
            "Cant set up logging to App Insights, as no instrumentation key is set."
        )
    else:
        log_record_processor = BatchLogRecordProcessor(log_exporter)
        logs.get_logger_provider().add_log_record_processor(log_record_processor)

    LOGGING_IS_CONFIGURED = True


def get_logger(name: str):
    # set up standard logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        # add OTEL handler
        handler = LoggingHandler()
        logger.addHandler(handler)

    return logger
