from abc import ABC, abstractmethod

import pyarrow as pa


class DataType(ABC):
    @classmethod
    def from_arrow(cls, pa_type: pa.DataType) -> "DataType":
        if pa.types.is_string(pa_type) or pa.types.is_large_string(pa_type):
            return String()
        elif pa.types.is_float64(pa_type):
            return Float()
        elif pa.types.is_int64(pa_type):
            return Int()
        elif pa.types.is_timestamp(pa_type):
            return Timestamp(tz=pa_type.tz)
        elif pa.types.is_date32(pa_type):
            return Date()
        elif pa.types.is_boolean(pa_type):
            return Boolean()
        elif pa.types.is_null(pa_type):
            return Null()
        else:
            raise ValueError(f"Unsupported data type: {pa_type}")

    @abstractmethod
    def __str__(self):
        ...

    def __eq__(self, other: "DataType") -> bool:
        return self.to_arrow() == other.to_arrow()

    @abstractmethod
    def to_arrow(self) -> pa.DataType:
        ...


class String(DataType):
    def __str__(self):
        return "string"

    def to_arrow(self) -> pa.DataType:
        return pa.string()


class Float(DataType):
    def __str__(self):
        return "float"

    def to_arrow(self) -> pa.DataType:
        return pa.float64()


class Int(DataType):
    def __str__(self):
        return "int"

    def to_arrow(self) -> pa.DataType:
        return pa.int64()


class Timestamp(DataType):
    def __str__(self):
        return f"timestamp[{self.tz}]"

    def __init__(self, tz: str):
        self.tz = tz

    def to_arrow(self) -> pa.DataType:
        return pa.timestamp("us", tz=self.tz)


class Date(DataType):
    def __str__(self):
        return "date"

    def to_arrow(self) -> pa.DataType:
        return pa.date32()


class Boolean(DataType):
    def __str__(self):
        return "boolean"

    def to_arrow(self) -> pa.DataType:
        return pa.bool_()


class Null(DataType):
    def __str__(self):
        return "null"

    def to_arrow(self) -> pa.DataType:
        return pa.null()
