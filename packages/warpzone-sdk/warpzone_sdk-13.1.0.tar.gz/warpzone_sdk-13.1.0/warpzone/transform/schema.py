from hashlib import md5

import pandas as pd

DATE_TIME_FORMAT = "datetime64[ns, UTC]"


class SchemaValidationError(Exception):
    """Error message when schema and dataframe have different column names"""

    def __init__(self, df_columns_set: set, schema_keys_set: set) -> None:
        difference = df_columns_set.symmetric_difference(schema_keys_set)
        message = f"Mismatch between dataframe and schema in column names {difference}"
        super().__init__(message)


class SchemaCastingError(Exception):
    """Error message when the data in dataframe
    cannot be casted to the type indicated in schema"""

    def __init__(
        self,
        column_name: str,
        current_type: str,
        target_type: str,
        exception: Exception,
    ) -> None:
        message = f"Casting failed for `{column_name}`"
        message += f" from `{current_type}` to `{target_type}`"
        message += f"\nError: {exception}"
        super().__init__(message)


def generate_and_stringify_schema(df: pd.DataFrame) -> dict[str, str]:
    columns = df.dtypes.astype(str)
    return columns.to_dict()


def calculate_schema_version(schema: dict) -> str:
    """create a md5 hash of schema, used as version in messages"""
    return md5(repr(schema).encode()).hexdigest()


def cast_to_schema(df: pd.DataFrame, schema: dict[str, str]) -> pd.DataFrame:
    """Change dtypes of columns in dataframe one by one to enable debugging
    and then reorder the dataframe based on the schema"""
    df = df.copy()
    for column in df.columns.values:
        try:
            df[column] = df[column].astype(schema[column])
        except (ValueError, TypeError) as e:
            raise SchemaCastingError(
                column_name=column,
                current_type=df.dtypes[column],
                target_type=schema[column],
                exception=e,
            )

    return df[schema.keys()]


def dataframe_schema_recast(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Cast pandas DataFrame to given schema and order columns"""
    if df.empty:
        # if DataFrame is empty, return equivalent but with given schema
        df_empty = pd.DataFrame(columns=schema).astype(dtype=schema)
        return df_empty

    if set(df.columns.values) != set(schema.keys()):
        raise SchemaValidationError(set(df.columns.values), set(schema.keys()))
    df = cast_to_schema(df, schema)

    return df
