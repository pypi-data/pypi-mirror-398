from functools import _lru_cache_wrapper, lru_cache
from typing import Optional

import datamazing.pandas as pdz
import pandas as pd
from azure.core.credentials import (
    AzureNamedKeyCredential,
    AzureSasCredential,
    TokenCredential,
)
from azure.identity import DefaultAzureCredential

from warpzone.blobstorage.client import WarpzoneBlobClient
from warpzone.healthchecks import HealthCheckResult, check_health_of
from warpzone.tablestorage.db import base_client
from warpzone.tablestorage.db.table_config import DataType, TableMetadata
from warpzone.tablestorage.tables.client import WarpzoneTableClient


class WarpzoneDatabaseClient:
    """Class to interact with Azure Table Storage for database queries
    (using Azure Blob Service underneath)
    """

    def __init__(
        self, table_client: WarpzoneTableClient, blob_client: WarpzoneBlobClient
    ):
        self._table_client = table_client
        self._blob_client = blob_client

    @classmethod
    def from_resource_name(
        cls,
        storage_account: str,
        credential: (
            AzureNamedKeyCredential | AzureSasCredential | TokenCredential
        ) = DefaultAzureCredential(),
    ):
        table_client = WarpzoneTableClient.from_resource_name(
            storage_account, credential
        )
        blob_client = WarpzoneBlobClient.from_resource_name(storage_account, credential)

        return cls(
            table_client,
            blob_client,
        )

    @classmethod
    def from_connection_string(cls, conn_str: str):
        table_client = WarpzoneTableClient.from_connection_string(conn_str)
        blob_client = WarpzoneBlobClient.from_connection_string(conn_str)

        return cls(table_client, blob_client)

    @lru_cache
    def _query_to_pandas(self, table_name: str, query: str) -> pd.DataFrame:
        records = self._table_client.query(table_name, query)
        df = base_client.generate_dataframe_from_records(records, self._blob_client)

        return df

    @lru_cache
    def get_table_metadata(self, table_name: str) -> TableMetadata:
        query = f"PartitionKey eq '{table_name}'"

        records = self._table_client.query(base_client.METADATA_TABLE_NAME, query)

        if len(records) == 0:
            raise ValueError(
                f"No metadata found for table {table_name}. "
                "This means that either the table does not exist "
                "or data has never been written to the table."
            )
        if len(records) > 1:
            raise ValueError(f"Multiple metadata records found for table {table_name}")

        metadata = TableMetadata.from_table_entity(records[0])

        return metadata

    def _query_generic(
        self,
        table_metadata: TableMetadata,
        time_interval: pdz.TimeInterval | None,
        filters: dict[str, object] | None,
        use_cache: bool,
    ) -> pd.DataFrame:
        if table_metadata.stored_in_blob:
            query = base_client.generate_query_string(time_interval)
        else:
            query = base_client.generate_query_string(time_interval, filters)

        if use_cache:
            df = self._query_to_pandas(table_metadata.table_name, query)
        else:
            # Use __wrapped__ to bypass cache
            df = self._query_to_pandas.__wrapped__(
                self, table_metadata.table_name, query
            )

        if table_metadata.stored_in_blob and filters:
            # The filter cant be applied in the query for blob stored tables
            # So we filter the dataframe after the query
            df = base_client.filter_dataframe(df, filters)

        return df

    def _query_chunked_time_series(
        self,
        table_metadata: TableMetadata,
        time_interval: pdz.TimeInterval,
        filters: dict[str, object] | None,
        use_cache: bool,
    ) -> pd.DataFrame:
        # Floor the time interval to the blob_chunk_resolution
        # This is to ensure that all the needed blobs are fetched
        query_time_interval = pdz.TimeInterval(
            time_interval.left.floor(table_metadata.blob_chunk_resolution),
            time_interval.right,
        )

        df = self._query_generic(
            table_metadata, query_time_interval, filters, use_cache
        )

        if not df.empty:
            # Filter the dataframe again for the time interval
            # This is to remove the data from the blobs that are not needed
            df = df[
                (df["time_utc"] >= time_interval.left)
                & (df["time_utc"] <= time_interval.right)
            ]

        return df

    def _query_time_series(
        self,
        table_metadata: TableMetadata,
        time_interval: pdz.TimeInterval | None,
        filters: dict[str, object] | None,
        use_cache: bool,
    ) -> pd.DataFrame:
        if time_interval and table_metadata.stored_in_blob:
            df = self._query_chunked_time_series(
                table_metadata, time_interval, filters, use_cache
            )
        else:
            df = self._query_generic(table_metadata, time_interval, filters, use_cache)

        return df

    def query(
        self,
        table_name: str,
        time_interval: Optional[pdz.TimeInterval] = None,
        filters: Optional[dict[str, object]] = None,
        use_cache: Optional[bool] = True,
    ) -> pd.DataFrame:
        table_metadata = self.get_table_metadata(table_name)

        match table_metadata.data_type:
            case DataType.TIME_SERIES:
                df = self._query_time_series(
                    table_metadata, time_interval, filters, use_cache
                )
            case _:
                if time_interval:
                    raise ValueError(
                        f"Table {table_name} is not a time series table,"
                        " and cannot be queried with a time interval."
                    )
                df = self._query_generic(table_metadata, None, filters, use_cache)

        return df

    def list_tables(self):
        return self._table_client.list_tables()

    def check_health(self) -> HealthCheckResult:
        """
        Pings the connections to the client's associated storage
        resources in Azure.
        """

        health_check = check_health_of(self._table_client)

        return health_check

    def clear_cache(self):
        """Clears the internal cache of all cached methods."""
        for method in self.__class__.__dict__.values():
            if isinstance(method, _lru_cache_wrapper):
                method.cache_clear()
