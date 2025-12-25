from typing import Optional

import pandas as pd

from warpzone.blobstorage.client import WarpzoneBlobClient

TABLE_STORAGE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATA_CONTAINER_NAME = "tables"
BLOB_NAME_COLUMN = "blob_path"
METADATA_TABLE_NAME = "tableMetadata"


def generate_query_string(
    time_interval: pd.Interval | None, filters: Optional[dict[str, object]] = None
) -> str:
    exprs = []

    if time_interval:
        start_time_str = time_interval.left.strftime(TABLE_STORAGE_TIME_FORMAT)
        end_time_str = time_interval.right.strftime(TABLE_STORAGE_TIME_FORMAT)
        exprs.append(f"PartitionKey ge '{start_time_str}'")
        exprs.append(f"PartitionKey le '{end_time_str}'")

    if filters:
        for key, value in filters.items():
            if not isinstance(value, list):
                value = [value]
            or_expr = []
            for item in value:
                or_expr.append(f"{key} eq '{item}'")
            or_query = " or ".join([f"({expr})" for expr in or_expr])
            exprs.append(or_query)

    query = " and ".join([f"({expr})" for expr in exprs])
    return query


def generate_dataframe_from_records(
    records: list[dict],
    blob_client: WarpzoneBlobClient,
) -> pd.DataFrame:
    # Return empty dataframe if the query result is empty
    if not records:
        return pd.DataFrame()

    # Download blobs and return the data stored if table entries contain blob_path
    if BLOB_NAME_COLUMN in records[0]:
        df = pd.DataFrame()
        for entity in records:
            blob_data = blob_client.download(
                DATA_CONTAINER_NAME, entity[BLOB_NAME_COLUMN]
            )
            df = pd.concat([df, blob_data.to_pandas()], ignore_index=True)
    else:
        df = pd.DataFrame.from_records(records)

    # Entities with blobs do not have RowKey and PartitionKey,
    # so we have to ignore errors.
    return df.drop(columns=["PartitionKey", "RowKey"], errors="ignore")


def filter_dataframe(df: pd.DataFrame, filters: dict[str, object]) -> pd.DataFrame:
    for key, value in filters.items():
        if key not in df.columns:
            raise KeyError(f"The column {key} is not found in the dataframe.")
        if isinstance(value, list):
            df = df[df[key].isin(value)]
        else:
            df = df[df[key] == value]

    df = df.reset_index(drop=True)

    return df
