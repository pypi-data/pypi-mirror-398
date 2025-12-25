from typing import Iterable

import azure.functions as func
import typeguard
from azure.servicebus import ServiceBusMessage

from warpzone.blobstorage.client import BlobData
from warpzone.enums.topicenum import Topic
from warpzone.function import integrations
from warpzone.servicebus.data.client import DataMessage
from warpzone.servicebus.events.client import EventMessage


class OutputProcessor:
    """Post-processing output binding"""

    return_type = None

    def process(self, value):
        return value

    def _process(self, value):
        """Internal method to process output.
        If output is iterable, the processing is
        run for each item."""
        if not value:
            # None output is accepted,
            # to allow intentional function
            # breaks
            return

        if isinstance(value, Iterable):
            for item in value:
                self.process(item)
        else:
            return self.process(value)


class BlobOutput(OutputProcessor):
    def __init__(self, container_name: str):
        typeguard.check_type(container_name, str)
        self.container_name = container_name


class MessageOutput(OutputProcessor):
    def __init__(self, topic: Topic):
        typeguard.check_type(topic, Topic)
        self.topic = topic

    def process(self, data_msg: ServiceBusMessage):
        integrations.send_func_msg(data_msg, self.topic)


class DataMessageOutput(MessageOutput):
    def process(self, data_msg: DataMessage) -> None:
        integrations.send_data(data_msg, self.topic)


class EventMessageOutput(MessageOutput):
    def process(self, event_msg: EventMessage) -> None:
        integrations.send_event(event_msg, self.topic)


class HttpOutput(OutputProcessor):
    return_type = func.HttpResponse

    def process(self, resp) -> func.HttpResponse:
        return resp


class ArchiveBlobDataOutput(BlobOutput):
    def process(self, blob_data: BlobData) -> None:
        integrations.upload_blob(blob_data, self.container_name)


class NoneOutput(OutputProcessor):
    pass
