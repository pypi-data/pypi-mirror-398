import copy
import datetime as dt
from abc import ABC, abstractmethod
from typing import Any

import polars as pl
import pytz


class GeneratedColumn(ABC):
    """Class representing a generated column."""

    @property
    @abstractmethod
    def base_column_names(self) -> list[str]:
        ...

    @abstractmethod
    def to_metadata(self) -> dict:
        ...

    @abstractmethod
    def expression(self) -> pl.Expr:
        """Polars expression to compute the generated column."""
        ...

    @abstractmethod
    def get_generated_conditions(self, op: str, value) -> list[tuple[str, Any]]:
        """Get conditions on the generated column based on a condition
        on the base column."""
        ...

    @classmethod
    def from_metadata(cls, metadata: dict):
        if metadata["type"] == "date_bucket":
            return DateBucket(
                base_column_name=metadata["base_column_name"],
                as_tz=metadata.get("as_tz", None),
            )
        elif metadata["type"] == "concat":
            return Concat(
                base_column_names=metadata["base_column_names"],
                delimiter=metadata["delimiter"],
            )
        else:
            raise ValueError(f"Unknown generated column type: {metadata['type']}")


class DateBucket(GeneratedColumn):
    def __init__(self, base_column_name: str, as_tz: str | None = None):
        """Generated column which bins a timestamp column to a date,
        optionally converting to a specific timezone first.

        Args:
            base_column_name (str): Base column name
            as_tz (str, optional): Cast to date in this timezone.
                Defaults to None, meaning it uses the original timezone.
        """
        self.base_column_name = base_column_name
        self.as_tz = as_tz

    def __str__(self):
        if self.as_tz is not None:
            return f"date_bucket({self.base_column_name}, as_tz={self.as_tz})"
        else:
            return f"date_bucket({self.base_column_name})"

    @property
    def base_column_names(self) -> list[str]:
        return [self.base_column_name]

    def to_metadata(self) -> dict:
        metadata = {
            "type": "date_bucket",
            "base_column_name": self.base_column_name,
        }
        if self.as_tz is not None:
            metadata["as_tz"] = self.as_tz
        return metadata

    def expression(self) -> pl.Expr:
        expr = pl.col(self.base_column_name)
        if self.as_tz is not None:
            expr = expr.dt.convert_time_zone(self.as_tz)
        return expr.dt.date()

    def get_generated_conditions(
        self, op: str, value: dt.datetime
    ) -> list[tuple[str, dt.date]]:
        """Get conditions on the generated column based on a condition
        on the base column.

        Args:
            op (str): Operator
            value (dt.datetime): Value

        Returns:
            tuple[str, dt.date]: List of conditions on the generated column
        """
        timestamp = copy.copy(value)
        if self.as_tz is not None:
            timestamp = timestamp.astimezone(pytz.timezone(self.as_tz))
        date = timestamp.date()

        match op:
            case "=":
                return [("=", date)]
            case ("<" | "<="):
                return [("<=", date)]
            case (">" | ">="):
                return [(">=", date)]
            case _:
                # for other operations, we cannot make any
                # useful filters on the generated column
                return []


class Concat(GeneratedColumn):
    def __init__(self, base_column_names: list[str], delimiter: str):
        """Generated column which concats multiple columns into a single string.

        Args:
            base_column_names (str): Base column names
            delimiter (str): Delimiter used for concatenation
        """
        self._base_column_names = base_column_names
        self.delimiter = delimiter

    @property
    def base_column_names(self) -> list[str]:
        return self._base_column_names

    def __str__(self):
        base_cols_str = ", ".join(self.base_column_names)
        return f"concat([{base_cols_str}], delimiter='{self.delimiter}')"

    def to_metadata(self) -> dict:
        metadata = {
            "type": "concat",
            "base_column_names": self.base_column_names,
            "delimiter": self.delimiter,
        }
        return metadata

    def expression(self) -> pl.Expr:
        return pl.concat_str(self.base_column_names, separator=self.delimiter)

    def get_generated_conditions(self, op: str, value: Any) -> list[tuple[str, Any]]:
        # for concat generated columns, we cannot make any
        # useful filters on the generated column
        return []
