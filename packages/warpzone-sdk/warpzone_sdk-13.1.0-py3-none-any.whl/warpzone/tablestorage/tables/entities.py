from collections import defaultdict

import pandas as pd

from .helpers import chunkify, generate_valid_table_keys


class TableEntities:
    def __init__(self, max_chunk_size: int = 100) -> None:
        self._max_chunk_size = max_chunk_size
        self._partitions = defaultdict(list)

    def add(self, entities: list[dict]) -> None:
        """Add operations you want to execute to the table storage.

        Args:
            entities (typing.List[typing.Dict]): A list of json entities.

        Raises:
            ValueError: If the enitity does not contain the required fields.
        """
        for entity in entities:
            partition_key, _ = self.validate_entity(entity)

            self._partitions[partition_key].append(entity)

    @staticmethod
    def validate_entity(entity):
        try:
            partition_key = entity.get("PartitionKey")
            row_key = entity.get("RowKey")
        except KeyError:
            raise ValueError("Entity must have a PartitionKey and RowKey property.")

        return partition_key, row_key

    @classmethod
    def from_pandas(
        cls, df: pd.DataFrame, partition_keys: list[str], row_keys: list[str]
    ):
        datetime_columns = df.select_dtypes(["datetime", "datetimetz"]).columns

        for column in datetime_columns:
            df[column] = df[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            df[f"{column}@odata.type"] = "Edm.DateTime"

        if not partition_keys:
            df["PartitionKey"] = "none"
        else:
            df["PartitionKey"] = (
                df[partition_keys]
                .astype(str)
                .agg("_".join, axis=1)
                .apply(generate_valid_table_keys)
            )
        if not row_keys:
            df["RowKey"] = "none"
        else:
            df["RowKey"] = (
                df[row_keys]
                .astype(str)
                .agg("_".join, axis=1)
                .apply(generate_valid_table_keys)
            )

        entities = cls()
        for _, partition_group in df.groupby(df["PartitionKey"]):
            entity_group = partition_group.to_dict("records")
            entities.add(entity_group)

        return entities

    def create_deletion_batches(self) -> defaultdict[str, list]:
        deletion_batches = defaultdict(list)
        for _, entities in self._partitions.items():
            for entity in entities:
                partition_key, row_key = self.validate_entity(entity)

                entity = {"PartitionKey": partition_key, "RowKey": row_key}

                deletion_batches[partition_key].append(("delete", entity))

        return deletion_batches

    def __iter__(self):
        chunks = []
        for _, entities in self._partitions.items():
            partition_chunks = chunkify(entities, self._max_chunk_size)
            chunks.extend(partition_chunks)

        return iter(chunks)

    def __len__(self):
        return sum(len(partition) for partition in self._partitions.values())
