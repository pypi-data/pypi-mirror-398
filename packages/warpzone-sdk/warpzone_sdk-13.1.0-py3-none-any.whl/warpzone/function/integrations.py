import os
from typing import Optional

import azure.functions as func
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

from warpzone.blobstorage.client import BlobData, WarpzoneBlobClient
from warpzone.db.client import WarpzoneDatabaseClient as WarpzoneDeltaDatabaseClient
from warpzone.enums.topicenum import Topic
from warpzone.servicebus.data.client import DataMessage, WarpzoneDataClient
from warpzone.servicebus.events.client import EventMessage, WarpzoneEventClient
from warpzone.tablestorage.db.client import WarpzoneDatabaseClient
from warpzone.tablestorage.tables.client import WarpzoneTableClient

# Singletons for clients and credentials
_data_client = None
_db_client = None
_credential = DefaultAzureCredential()


def get_sb_client() -> ServiceBusClient:
    service_bus_namespace = os.environ["SERVICE_BUS_NAMESPACE"]

    return ServiceBusClient(
        fully_qualified_namespace=f"{service_bus_namespace}.servicebus.windows.net",
        credential=_credential,
    )


def get_data_client() -> WarpzoneDataClient:
    global _data_client

    if _data_client is None:
        _data_client = WarpzoneDataClient.from_resource_names(
            storage_account=os.environ["MESSAGE_STORAGE_ACCOUNT"],
            service_bus_namespace=os.environ["SERVICE_BUS_NAMESPACE"],
            credential=_credential,
        )
    return _data_client


def get_event_client() -> WarpzoneEventClient:
    return WarpzoneEventClient.from_resource_name(
        os.environ["SERVICE_BUS_NAMESPACE"], _credential
    )


def get_table_client() -> WarpzoneTableClient:
    return WarpzoneTableClient.from_resource_name(
        os.environ["TABLE_STORAGE_ACCOUNT"], _credential
    )


def get_db_client() -> WarpzoneDatabaseClient:
    db_client = WarpzoneDatabaseClient.from_resource_name(
        os.environ["TABLE_STORAGE_ACCOUNT"],
        credential=_credential,
    )
    return db_client


def get_delta_db_client() -> WarpzoneDeltaDatabaseClient:
    db_client = WarpzoneDeltaDatabaseClient.from_storage_account(
        os.environ["OPERATIONAL_DATA_STORAGE_ACCOUNT"],
        credential=_credential,
    )
    return db_client


def get_archive_client() -> WarpzoneBlobClient:
    return WarpzoneBlobClient.from_resource_name(
        os.environ["ARCHIVE_STORAGE_ACCOUNT"], _credential
    )


def func_msg_to_event(msg: func.ServiceBusMessage) -> EventMessage:
    event_msg = EventMessage.from_func_msg(msg)
    return event_msg


def func_msg_to_data(msg: func.ServiceBusMessage) -> DataMessage:
    data_client = get_data_client()
    event_msg = func_msg_to_event(msg)
    data_msg = data_client.event_to_data(event_msg)
    return data_msg


def func_msg_to_pandas(msg: func.ServiceBusMessage) -> pd.DataFrame:
    data_msg = func_msg_to_data(msg)
    return data_msg.to_pandas()


def send_func_msg(data_msg: ServiceBusMessage, topic: Topic):
    sb_client = get_sb_client()
    with sb_client.get_topic_sender(topic.value) as sender:
        sender.send_messages(message=data_msg)


def send_event(event_msg: EventMessage, topic: Topic) -> None:
    event_client = get_event_client()
    event_client.send(
        topic=topic,
        event_msg=event_msg,
    )


def send_data(data_msg: DataMessage, topic: Topic) -> None:
    data_client = get_data_client()
    data_client.send(
        topic=topic,
        data_msg=data_msg,
    )


def send_pandas(
    df: pd.DataFrame, topic: Topic, subject: str, schema: Optional[dict] = None
) -> None:
    data_msg = DataMessage.from_pandas(df, subject, schema=schema)
    send_data(data_msg, topic)


def read_pandas(
    table_name: str,
    time_interval: pd.Interval = None,
) -> pd.DataFrame:
    db_client = get_db_client()

    return db_client.query(table_name, time_interval)


def upload_blob(blob_data: BlobData, container_name: str) -> None:
    blob_client = get_archive_client()
    blob_client.upload(container_name=container_name, blob_data=blob_data)
