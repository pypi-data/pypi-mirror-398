from dataclasses import dataclass
from enum import Enum, auto

import pandas as pd


class DataType(Enum):
    TIME_SERIES = auto()
    MASTER_DATA = auto()


@dataclass
class TableMetadata:
    table_name: str
    data_type: DataType
    stored_in_blob: bool
    blob_chunk_resolution: pd.Timedelta | None

    ROW_KEY = "metadata"

    @classmethod
    def from_table_entity(cls, data: dict) -> "TableMetadata":
        blob_chunk_resolution = (
            pd.Timedelta(data["blob_chunk_resolution"])
            if data["blob_chunk_resolution"]
            else None
        )
        return cls(
            table_name=data["PartitionKey"],
            data_type=DataType[data["data_type"]],
            stored_in_blob=bool(data["stored_in_blob"]),
            blob_chunk_resolution=blob_chunk_resolution,
        )

    def to_table_entity(self) -> dict:
        # Table storage does not support none, therefore we use empty string
        blob_chunk_resolution = (
            self.blob_chunk_resolution.isoformat() if self.blob_chunk_resolution else ""
        )
        return {
            "PartitionKey": self.table_name,
            "RowKey": self.ROW_KEY,
            "data_type": self.data_type.name,
            "stored_in_blob": self.stored_in_blob,
            "blob_chunk_resolution": blob_chunk_resolution,
        }
