from typing import Any


class HyperSlice(list[tuple[str, str, Any]]):
    """A list of tuples representing a n-dimensional slice of a table.
    Each tuple corresponds to a filter applied on the table,
    in the form of (column, operator, value). For example, the
    following hyper slice represents all records in a table
    where the country is 'Denmark' and the date is greater than
    2000-01-01:

        [
            ("country", "=", "Denmark"),
            ("date", ">", "2000-01-01"),
        ]

    In SQL, this would be equivalent to the WHERE clause:

        country = 'Denmark' AND date > '2000-01-01'
    """

    ...
