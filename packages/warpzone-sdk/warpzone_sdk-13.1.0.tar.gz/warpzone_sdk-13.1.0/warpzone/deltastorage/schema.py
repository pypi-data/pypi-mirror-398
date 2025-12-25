import json
from typing import Optional

import polars as pl
import pyarrow as pa

from .data_types import DataType
from .generated_columns import GeneratedColumn
from .slicing import HyperSlice


class Field:
    def __init__(
        self,
        column_name: str,
        data_type: DataType,
        generated_as: Optional[GeneratedColumn] = None,
    ):
        """Class representing a table field.

        Args:
            column_name (str): Column name
            data_type (DataType): Data type
            generated_as (GeneratedColumn, optional): Generated column based on a
                regular column. Defaults to None, meaning the column is not generated.
        """
        self.column_name = column_name
        self.data_type = data_type
        self.generated_as = generated_as

    def __eq__(self, other: "Field") -> bool:
        return self.to_arrow().equals(other.to_arrow(), check_metadata=True)

    def __repr__(self):
        string = f"{self.column_name}: {self.data_type}"
        if self.generated_as is not None:
            string = f"{string} [generated as {self.generated_as}]"
        return string

    def to_arrow(self):
        """Convert to pyarrow field. Information about generated columns
        is stored as metadata."""
        pa_dtype = self.data_type.to_arrow()

        pa_metadata = None
        if self.generated_as is not None:
            pa_metadata = {
                "generated_column": json.dumps(self.generated_as.to_metadata())
            }

        return pa.field(self.column_name, pa_dtype, metadata=pa_metadata)

    @classmethod
    def from_arrow(cls, pa_field: pa.Field) -> "Field":
        """Convert from pyarrow field"""
        data_type = DataType.from_arrow(pa_field.type)

        generated_as = None

        if pa_field.metadata is not None:
            pa_metadata = {k.decode(): v.decode() for k, v in pa_field.metadata.items()}
            if "generated_column" in pa_metadata:
                gen_col_metadata = json.loads(pa_metadata["generated_column"])
                generated_as = GeneratedColumn.from_metadata(gen_col_metadata)

        return cls(pa_field.name, data_type, generated_as)


class Schema:
    def __init__(
        self,
        fields: list[Field],
    ):
        """Class representing a table schema.

        Args:
            fields (list[Field]): Schema fields
        """
        self.fields = fields

    def __eq__(self, other: "Schema") -> bool:
        return self.to_arrow().equals(other.to_arrow(), check_metadata=True)

    def __repr__(self):
        field_reprs = [repr(field) for field in self.fields]
        return "\n".join(field_reprs)

    def to_arrow(self):
        """Convert to pyarrow schema."""
        pa_fields = [field.to_arrow() for field in self.fields]
        return pa.schema(pa_fields)

    @classmethod
    def from_arrow(cls, pa_schema: pa.Schema) -> "Schema":
        """Convert from pyarrow schema"""
        fields = []
        for pa_field in pa_schema:
            field = Field.from_arrow(pa_field)
            fields.append(field)
        return cls(fields)

    def add_generated_columns(self, base_df: pl.DataFrame) -> pl.DataFrame:
        """Add additional columns to a dataframe derived
        from all generated columns in the schema.

        Args:
            base_df (pl.DataFrame): Input dataframe
        """
        generated_exprs = []
        for field in self.fields:
            if field.generated_as is not None:
                expr = field.generated_as.expression().alias(field.column_name)
                generated_exprs.append(expr)

        return base_df.with_columns(generated_exprs)

    def add_generated_filters(self, base_slice: HyperSlice) -> HyperSlice:
        """Add additional filters to a hyperslice based from
        all generated columns in the schema.

        Args:
            base_slice (HyperSlice): Input hyperslice
        """
        generated_slice = []
        for col, op, val in base_slice:
            for field in self.fields:
                if field.generated_as is None:
                    continue
                if col not in field.generated_as.base_column_names:
                    continue
                for gen_op, gen_val in field.generated_as.get_generated_conditions(
                    op, val
                ):
                    generated_slice.append((field.column_name, gen_op, gen_val))
        return HyperSlice(list(base_slice) + generated_slice)
