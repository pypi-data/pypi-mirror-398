import azure.functions as func

from warpzone.function import integrations
from warpzone.monitor import logs, traces
from warpzone.servicebus.events.client import EventMessage

tracer = traces.get_tracer(__name__)
logger = logs.get_logger(__name__)


class TriggerProcessor:
    """Pre-processing trigger binding

    Args:
        binding_name (str): Name of trigger binding
            as specified in `function.json`.
    """

    arg_type: object = None

    def __init__(self, binding_name: str):
        self.binding_name = binding_name

    def _process(self, value):
        """Internal method for processing trigger"""
        # NOTE: This method currently does nothing
        # but exists to align with OutputProcessor
        return self.process(value)

    def process(self, value):
        return value


class MessageTrigger(TriggerProcessor):
    def process(self, msg):
        logger.info(f"<Subject>{msg.label}")
        return msg

    arg_type = func.ServiceBusMessage


class DataMessageTrigger(MessageTrigger):
    def process(self, msg: func.ServiceBusMessage):
        self._log_data_msg(msg)

        super().process(msg)

        return integrations.func_msg_to_data(msg)

    def _log_data_msg(self, msg: func.ServiceBusMessage):
        event_msg = EventMessage.from_func_msg(msg)
        blob_name = event_msg.event["blob_name"]

        logger.info(f"<BlobName>{blob_name}")


class EventMessageTrigger(MessageTrigger):
    def process(self, msg: func.ServiceBusMessage):
        super().process(msg)
        return integrations.func_msg_to_event(msg)


class HttpTrigger(TriggerProcessor):
    arg_type = func.HttpRequest


class TimerTrigger(TriggerProcessor):
    arg_type = func.TimerRequest
