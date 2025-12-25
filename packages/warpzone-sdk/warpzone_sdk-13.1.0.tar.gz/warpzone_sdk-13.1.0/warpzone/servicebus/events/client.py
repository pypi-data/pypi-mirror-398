import datetime
import json
import uuid
from dataclasses import dataclass
from functools import reduce
from typing import Iterator, Optional

import typeguard
from azure.core.credentials import (
    AzureNamedKeyCredential,
    AzureSasCredential,
    TokenCredential,
)
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusError
from azure.servicebus.management import ServiceBusAdministrationClient

from warpzone.enums.topicenum import Topic
from warpzone.healthchecks import HealthCheckResult, HealthStatus
from warpzone.monitor import traces

tracer = traces.get_tracer(__name__)


@dataclass
class EventMessage:
    event: dict
    subject: str
    message_id: Optional[str] = None
    time_to_live: Optional[datetime.timedelta] = None

    def __post_init__(self):
        self.message_id = self.message_id if self.message_id else str(uuid.uuid4())

    @classmethod
    def from_func_msg(cls, msg):
        """
        Parse Azure Function Service Bus trigger binding message to an
        event message"""
        return cls(
            event=json.loads(msg.get_body()),
            message_id=msg.message_id,
            subject=msg.label,
            time_to_live=msg.time_to_live,
        )


class WarpzoneEventClient:
    """Class to interact with Azure Service Bus for events"""

    def __init__(self, service_bus_client: ServiceBusClient):
        self._service_bus_client = service_bus_client

    @classmethod
    def from_resource_name(
        cls,
        service_bus_namespace: str,
        credential: AzureNamedKeyCredential
        | AzureSasCredential
        | TokenCredential = DefaultAzureCredential(),
    ):
        service_bus_client = ServiceBusClient(
            fully_qualified_namespace=f"{service_bus_namespace}.servicebus.windows.net",
            credential=credential,
        )
        return cls(service_bus_client)

    @classmethod
    def from_connection_string(cls, conn_str: str) -> "WarpzoneEventClient":
        service_bus_client = ServiceBusClient.from_connection_string(conn_str)
        return cls(service_bus_client)

    def _get_subscription_receiver(
        self,
        topic_name: str,
        subscription_name: str,
        max_wait_time: Optional[int] = None,
    ):
        return self._service_bus_client.get_subscription_receiver(
            topic_name=topic_name,
            subscription_name=subscription_name,
            max_wait_time=max_wait_time,
        )

    def _get_topic_sender(self, topic_name: str):
        return self._service_bus_client.get_topic_sender(topic_name=topic_name)

    def _get_management_client(self):
        return ServiceBusAdministrationClient(
            fully_qualified_namespace=(
                self._service_bus_client.fully_qualified_namespace
            ),
            credential=self._service_bus_client._credential,
        )

    def receive(
        self,
        topic: Topic,
        subscription_name: str,
        max_wait_time: Optional[int] = None,
    ) -> Iterator[EventMessage]:
        typeguard.check_type(value=topic, expected_type=Topic)
        topic_name = topic.value
        with self._get_subscription_receiver(
            topic_name, subscription_name, max_wait_time
        ) as receiver:
            for az_sdk_msg in receiver:
                content_parts = az_sdk_msg.message.get_data()
                # message data can either be a generator
                # of string or bytes. We want to concatenate
                # them in either case
                content = reduce(lambda x, y: x + y, content_parts)
                yield EventMessage(
                    event=json.loads(content),
                    message_id=az_sdk_msg.message_id,
                    subject=az_sdk_msg.subject,
                )
                receiver.complete_message(az_sdk_msg)

    def send(
        self,
        topic: Topic,
        event_msg: EventMessage,
    ):
        typeguard.check_type(value=topic, expected_type=Topic)
        topic_name = topic.value
        with traces.servicebus_send_span(
            self._service_bus_client.fully_qualified_namespace, topic_name
        ):
            diagnostic_id = traces.get_current_diagnostic_id()

            az_sdk_msg = ServiceBusMessage(
                body=json.dumps(event_msg.event),
                subject=event_msg.subject,
                content_type="application/json",
                message_id=event_msg.message_id,
                application_properties={"Diagnostic-Id": diagnostic_id},
                time_to_live=event_msg.time_to_live,
            )

            with self._get_topic_sender(topic_name) as sender:
                sender.send_messages(message=az_sdk_msg)

    def list_subscriptions(
        self,
        topic: Topic,
    ):
        management_client = self._get_management_client()
        return [
            sub.name
            for sub in management_client.list_subscriptions(topic_name=topic.name)
        ]

    def check_health(self) -> HealthCheckResult:
        """
        Pings the connection to the client's associated ServiceBus topic in Azure.
        """

        try:
            topic_sender = self._get_topic_sender(Topic.EVENTS.value)

            with topic_sender:
                pass
        except ServiceBusError as ex:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                description="Unable to connect to service bus topic.",
                exception=ex,
            )

        return HealthCheckResult.healthy()
