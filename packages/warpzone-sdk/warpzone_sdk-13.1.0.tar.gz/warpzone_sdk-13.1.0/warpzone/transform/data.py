from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# This is the highest precision that Spark supports currently at v3.3.2
SUPPORTED_SPARK_PARQUET_TIMESTAMP_PRECISION = "us"
DEFAULT_TIMESTAMP_TYPE = "ns"


def convert_timestamp_type(table: pa.Table, precision: str) -> pa.Table:
    new_fields = []
    for field in table.schema:
        if isinstance(field.type, pa.TimestampType):
            field = pa.field(
                field.name,
                pa.timestamp(precision, tz=field.type.tz),
            )
        new_fields.append(field)
    new_schema = pa.schema(new_fields)
    table = table.cast(new_schema)

    return table


def parquet_to_arrow(parquet: bytes) -> pa.Table:
    """Convert parquet as bytes to pyarrow table"""
    return pq.read_table(pa.py_buffer(parquet))


def arrow_to_parquet(table: pa.Table) -> bytes:
    """Convert pyarrow table to parquet as bytes"""
    buf = pa.BufferOutputStream()
    pq.write_table(table, buf)
    return buf.getvalue().to_pybytes()


def pandas_to_arrow(
    df: pd.DataFrame, schema: Optional[dict] = None, preserve_index: bool = False
) -> pa.Table:
    df = df.copy()
    if schema:
        arrow_schema = pa.schema(schema)
    else:
        arrow_schema = None

    # Due to spark not supporting nanosecond precision, we round to microseconds
    for column in df.select_dtypes(["datetime", "datetimetz"]).columns:
        df[column] = df[column].dt.round(SUPPORTED_SPARK_PARQUET_TIMESTAMP_PRECISION)

    table = pa.Table.from_pandas(df, arrow_schema, preserve_index=preserve_index)

    # pandas may leave metadata, which we don't want
    table = table.replace_schema_metadata(None)

    # cast timestamp columns to the default timestamp type
    table = convert_timestamp_type(table, SUPPORTED_SPARK_PARQUET_TIMESTAMP_PRECISION)

    return table


def arrow_to_pandas(table: pa.Table):
    # cast timestamp columns to the default timestamp type
    table = convert_timestamp_type(table, DEFAULT_TIMESTAMP_TYPE)
    df = table.to_pandas()
    return df


def pandas_to_parquet(df: pd.DataFrame, schema: Optional[dict] = None) -> bytes:
    table = pandas_to_arrow(df, schema)
    return arrow_to_parquet(table)


def parquet_to_pandas(parquet: bytes) -> pd.DataFrame:
    table = parquet_to_arrow(parquet)
    return arrow_to_pandas(table)
