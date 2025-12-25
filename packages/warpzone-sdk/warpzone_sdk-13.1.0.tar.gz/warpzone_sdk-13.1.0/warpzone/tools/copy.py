import re

import datamazing.pandas as pdz
import pandas as pd

from warpzone.enums.topicenum import Topic
from warpzone.servicebus.data.client import DataMessage, WarpzoneDataClient
from warpzone.tablestorage.db.client import WarpzoneDatabaseClient
from warpzone.tablestorage.db.table_config import DataType

DATA_STORAGE_BASENAME = "saenigmadata"
CORE_SERVICEBUS_NAME = "sb-enigma-core"
CHUNK_SIZE = 5000  # seems to be the most optimal size for the chunk


def create_data_message_and_send(
    df: pd.DataFrame,
    subject: str,
    df_schema: dict,
    servicebus_client: WarpzoneDataClient,
):
    data_msg = DataMessage.from_pandas(
        df=df,
        subject=subject,
        schema=df_schema,
    )

    servicebus_client.send(topic=Topic.UNIFORM, data_msg=data_msg)


def transfer_tables_between_environments(
    source: str,
    target: str,
    table_name: str,
    time_interval: pdz.TimeInterval = None,
    send_in_chunks: bool = False,
):
    """
    Copy tablestorage data from env to user sandbox environment.

    inputs:

    source: The source environment (e.g. prod)
    target: The target environment (e.g. dev)
    table_name: name of the table to copy
    time_interval: time interval to copy


    """

    storage_account_name_source = f"{DATA_STORAGE_BASENAME}{source}"
    db_client_source = WarpzoneDatabaseClient.from_resource_name(
        storage_account_name_source
    )

    table_metadata = db_client_source.get_table_metadata(table_name)

    match table_metadata.data_type:
        case DataType.TIME_SERIES:
            df = db_client_source.query(
                table_name=table_name, time_interval=time_interval
            )
        case _:
            df = db_client_source.query(table_name=table_name)

    df_schema = df.dtypes.astype(str).to_dict()
    # convert table name to subject (camelCase to snake_case)
    subject = re.sub(r"(?<!^)(?=[A-Z])", "_", table_name).lower()

    service_bus_namespace_target = f"{CORE_SERVICEBUS_NAME}-{target}"
    storage_account_name_target = f"{DATA_STORAGE_BASENAME}{target}"

    servicebus_client = WarpzoneDataClient.from_resource_names(
        storage_account=storage_account_name_target,
        service_bus_namespace=service_bus_namespace_target,
    )

    if send_in_chunks:
        for row in range(0, df.shape[0], CHUNK_SIZE):
            df_chunk = df[row : row + CHUNK_SIZE]

            create_data_message_and_send(
                df_chunk, subject, df_schema, servicebus_client
            )

    else:
        create_data_message_and_send(df, subject, df_schema, servicebus_client)
