import datetime as dt
import uuid
from dataclasses import dataclass
from typing import Iterator, Optional

import pandas as pd
from azure.core.credentials import (
    AzureNamedKeyCredential,
    AzureSasCredential,
    TokenCredential,
)
from azure.identity import DefaultAzureCredential

from warpzone.blobstorage.client import BlobData, WarpzoneBlobClient
from warpzone.enums.topicenum import Topic
from warpzone.healthchecks import HealthCheckResult, check_health_of
from warpzone.servicebus.events.client import EventMessage, WarpzoneEventClient
from warpzone.transform import data
from warpzone.transform.schema import calculate_schema_version, dataframe_schema_recast

DATA_CONTAINER_NAME = "messages"
BLOB_NAME_PARAM = "blob_name"
TIMESTAMP_PARAM = "timestamp"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


@dataclass
class DataMessage:
    content: bytes
    extension: str
    subject: str
    message_id: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: Optional[dt.datetime] = None

    def __post_init__(self):
        self.message_id = self.message_id if self.message_id else str(uuid.uuid4())
        self.metadata = self.metadata if self.metadata else {}
        self.timestamp = (
            self.timestamp if self.timestamp else dt.datetime.now(tz=dt.timezone.utc)
        )

    @classmethod
    def from_pandas(
        cls,
        df: pd.DataFrame,
        subject: str,
        schema: dict,
        message_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        timestamp: Optional[dt.datetime] = None,
    ):
        if metadata is None:
            metadata = {}
        metadata["version"] = calculate_schema_version(schema)
        df = dataframe_schema_recast(df, schema)
        content = data.pandas_to_parquet(df)
        extension = "parquet"
        return cls(content, extension, subject, message_id, metadata, timestamp)

    def to_pandas(self) -> pd.DataFrame:
        return data.parquet_to_pandas(self.content)


class WarpzoneDataClient:
    """
    Class to interact with Azure Service Bus for data
    (using Azure Blob Service underneath)
    """

    def __init__(
        self,
        event_client: WarpzoneEventClient,
        blob_client: WarpzoneBlobClient,
    ):
        self._event_client = event_client
        self._blob_client = blob_client

    @classmethod
    def from_resource_names(
        cls,
        storage_account: str,
        service_bus_namespace: str,
        credential: AzureNamedKeyCredential
        | AzureSasCredential
        | TokenCredential = DefaultAzureCredential(),
    ):
        event_client = WarpzoneEventClient.from_resource_name(
            service_bus_namespace, credential
        )
        blob_client = WarpzoneBlobClient.from_resource_name(storage_account, credential)

        return cls(
            event_client,
            blob_client,
        )

    @classmethod
    def from_connection_strings(
        cls,
        service_bus_conn_str: str,
        storage_account_conn_str: str,
    ):
        event_subscription_client = WarpzoneEventClient.from_connection_string(
            service_bus_conn_str
        )
        blob_client = WarpzoneBlobClient.from_connection_string(
            storage_account_conn_str
        )
        return cls(
            event_subscription_client,
            blob_client,
        )

    @staticmethod
    def generate_blob_name(data_msg: DataMessage) -> str:
        """Generate blob name for storing data when sending data"""
        time_partiton = data_msg.timestamp.strftime("year=%Y/month=%m/day=%d/hour=%H")
        return (
            f"{data_msg.subject}/{time_partiton}"
            f"/{data_msg.message_id}.{data_msg.extension}"
        )

    def event_to_data(self, event_msg: EventMessage) -> DataMessage:
        """Convert event to data message (downloading blob behind the scenes)"""
        # 1. get <blob-name> from event message
        blob_name = event_msg.event[BLOB_NAME_PARAM]

        # 2. download blob from <blob-name> location
        blob_data = self._blob_client.download(
            container_name=DATA_CONTAINER_NAME, blob_name=blob_name
        )

        # 3. create data message
        extension = blob_name.split(".")[-1]

        return DataMessage(
            content=blob_data.content,
            extension=extension,
            message_id=event_msg.message_id,
            subject=event_msg.subject,
            metadata=blob_data.metadata,
        )

    def data_to_event(self, data_msg: DataMessage) -> EventMessage:
        """Convert data to event message (uploading blob behind the scenes)"""
        # 1. generate <blob-name>
        blob_name = self.generate_blob_name(data_msg)

        # 2. upload blob to <blob-name>
        blob_data = BlobData(
            content=data_msg.content,
            name=blob_name,
            metadata=data_msg.metadata,
        )

        self._blob_client.upload(
            blob_data=blob_data,
            container_name=DATA_CONTAINER_NAME,
        )

        # 3. create event message
        event = {
            BLOB_NAME_PARAM: blob_name,
            TIMESTAMP_PARAM: data_msg.timestamp.strftime(TIMESTAMP_FORMAT),
        }

        return EventMessage(
            event=event,
            subject=data_msg.subject,
            message_id=data_msg.message_id,
        )

    def receive(
        self,
        topic: Topic,
        subscription_name: str,
        max_wait_time: Optional[int] = None,
    ) -> Iterator[DataMessage]:
        # receive events
        for event_msg in self._event_client.receive(
            topic,
            subscription_name,
            max_wait_time=max_wait_time,
        ):
            # download blob and return data
            yield self.event_to_data(event_msg)

    def send(
        self,
        topic: Topic,
        data_msg: DataMessage,
    ):
        # upload blob and return event
        event_msg = self.data_to_event(data_msg)
        # send event
        self._event_client.send(
            event_msg=event_msg,
            topic=topic,
        )

    def list_subscriptions(
        self,
        topic: Topic,
    ):
        return self._event_client.list_subscriptions(topic)

    def check_health(self) -> HealthCheckResult:
        """
        Pings the connections to the client's associated storage and service bus
        ressources in Azure.
        """

        health_check = check_health_of(self._blob_client, self._event_client)

        return health_check
