""" Module w.r.t. Azure blob storage logic."""
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from azure.core.credentials import (
    AzureNamedKeyCredential,
    AzureSasCredential,
    TokenCredential,
)
from azure.core.exceptions import (
    HttpResponseError,
    ServiceRequestError,
    ServiceResponseError,
)
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from warpzone.healthchecks import HealthCheckResult, HealthStatus
from warpzone.transform import data


@dataclass
class BlobData:
    content: bytes
    name: str
    metadata: Optional[dict] = None

    def __post_init__(self):
        self.metadata = self.metadata if self.metadata else {}

    @classmethod
    def from_pandas(
        cls,
        df: pd.DataFrame,
        name: str,
        metadata: Optional[dict] = None,
        schema: Optional[dict] = None,
    ):
        content = data.pandas_to_parquet(df, schema=schema)
        return cls(content, name, metadata=metadata)

    def to_pandas(self) -> pd.DataFrame:
        return data.parquet_to_pandas(self.content)


class WarpzoneBlobClient:
    """Class to interact with Azure Blob Service"""

    def __init__(self, blob_service_client: BlobServiceClient):
        self._blob_service_client = blob_service_client

    @classmethod
    def from_resource_name(
        cls,
        storage_account: str,
        credential: (
            AzureNamedKeyCredential | AzureSasCredential | TokenCredential
        ) = DefaultAzureCredential(),
    ):
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=credential,
        )

        return cls(blob_service_client)

    @classmethod
    def from_connection_string(cls, conn_str: str):
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        return cls(blob_service_client)

    def download(self, container_name: str, blob_name: str) -> BlobData:
        blob_client = self._blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name,
        )
        stream_downloader = blob_client.download_blob()
        return BlobData(
            content=stream_downloader.content_as_bytes(),
            name=blob_name,
            metadata=stream_downloader.properties.metadata,
        )

    def upload(
        self,
        container_name: str,
        blob_data: BlobData,
        overwrite: bool = False,
    ):
        blob_client = self._blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_data.name,
        )
        blob_client.upload_blob(
            data=blob_data.content,
            metadata=blob_data.metadata,
            overwrite=overwrite,
        )

    def delete(self, container_name: str, blob_name: str):
        container_client = self._blob_service_client.get_container_client(
            container_name
        )
        container_client.delete_blob(blob_name)

    def list_containers(self):
        return [
            container.name for container in self._blob_service_client.list_containers()
        ]

    def list_dir(
        self,
        container_name: str,
        path: str = "",
        recursive: bool = False,
    ):
        container_client = self._blob_service_client.get_container_client(
            container=container_name,
        )

        prefix = f"{path}/" if path else ""

        subpaths = []
        if recursive:
            for item in container_client.list_blobs(name_starts_with=prefix):
                if "." in item.name:
                    subpath = item.name.rstrip("/")
                    subpaths.append(subpath)
        else:
            for item in container_client.walk_blobs(
                name_starts_with=prefix, delimiter="/"
            ):
                subpath = item.name.rstrip("/")
                subpaths.append(subpath)

        return subpaths

    def check_health(self) -> HealthCheckResult:
        """
        Pings the connection to the client's associated storage ressources in Azure.
        """
        try:
            container_iterator = self._blob_service_client.list_containers()
            next(container_iterator, None)
        except (ServiceRequestError, ServiceResponseError, HttpResponseError) as ex:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                description="Unable to connect to blob storage.",
                exception=ex,
            )

        return HealthCheckResult.healthy()
