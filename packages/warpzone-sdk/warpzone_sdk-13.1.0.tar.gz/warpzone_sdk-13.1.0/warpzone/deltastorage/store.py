import os

import deltalake as dl
import obstore as obs

from .schema import Schema
from .table import Table


class Store:
    def __init__(
        self,
        path: str,
        storage_options: dict[str, str] | None = None,
    ):
        """Class representing a store containing datasets

        Args:
            path (str): Root directory containing Delta tables
            storage_options (dict[str, str] | None, optional): Storage options used for
                remote cloud storage. For more information on available options,
                go to https://delta-io.github.io/delta-rs/integrations/object-storage/.
                Defaults to None, corresponding to the local file system.
        """
        self.path = path
        self.storage_options = storage_options
        # We use obstore to interact with remote
        # cloud storage for operations not directly
        # supported by delta-rs (e.g. listing directories)
        # We could use fsspec, but the `storage_options`
        # used by delta-rs and fsspec are not compatible
        self._obstore = obs.store.from_url(
            url=path,
            config=storage_options,
        )

    def __repr__(self):
        return f"Store('{self.path}')"

    def _get_table_uri(self, table_name: str) -> str:
        return self.path + "/" + table_name

    @staticmethod
    def _get_func_storage_options() -> dict[str, str]:
        """Get storage options.
        This differ depending on whether we are running
        in cloud or locally.
        """
        if "IDENTITY_ENDPOINT" in os.environ:
            # When running in Azure Function, the environment variable IDENTITY_ENDPOINT
            # will be set, and we use the managed identity to access the storage account
            storage_options = {"azure_msi_endpoint": os.environ["IDENTITY_ENDPOINT"]}
        else:
            # When running locally, we use the Azure CLI to authenticate.
            storage_options = {"use_azure_cli": "true"}

        return storage_options

    @classmethod
    def from_func_environment_variable(cls):
        """Create Store instance from environment variable"""
        storage_account_name = os.environ["OPERATIONAL_DATA_STORAGE_ACCOUNT"]
        path = f"abfss://datasets@{storage_account_name}.dfs.core.windows.net"

        storage_options = Store._get_func_storage_options()

        return cls(path=path, storage_options=storage_options)

    def list_tables(self) -> list[str]:
        """List all Delta tables"""
        return self._obstore.list_with_delimiter()["common_prefixes"]

    def table_exists(self, table_name: str):
        """Check if Delta table exists

        Args:
            table_name (str): Table name
        """
        return dl.DeltaTable.is_deltatable(
            table_uri=self._get_table_uri(table_name),
            storage_options=self.storage_options,
        )

    def create_table(
        self,
        table_name: str,
        schema: Schema,
        partition_by: list[str] | None = None,
    ) -> Table:
        """Create Delta table

        Args:
            table_name (str): Table name.
            schema (pl.Schema): Table schema.
            partition_by (list[str]): Partition columns.
        """
        if self.table_exists(table_name):
            raise ValueError(f"Table with name '{table_name}' already exists")

        if schema is None:
            raise ValueError("Schema must be provided when creating a new table")

        pa_schema = schema.to_arrow()

        dl.DeltaTable.create(
            table_uri=self._get_table_uri(table_name),
            schema=pa_schema,
            storage_options=self.storage_options,
            partition_by=partition_by,
            configuration={
                "delta.deletedFileRetentionDuration": "interval 2 hours",
                "delta.logRetentionDuration": "interval 4 hours",
            },
        )

        return Table(self._get_table_uri(table_name), self.storage_options)

    def get_table(self, table_name: str) -> Table:
        """Get Delta table

        Args:
            table_name (str): Table name
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table with name '{table_name}' does not exist")

        return Table(self._get_table_uri(table_name), self.storage_options)
