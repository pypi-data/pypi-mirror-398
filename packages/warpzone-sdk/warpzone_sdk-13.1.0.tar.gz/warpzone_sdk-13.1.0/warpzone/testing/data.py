import datetime as dt
import os
from pathlib import Path
from typing import Optional

import datamazing.pandas as pdz
import pandas as pd

from warpzone.servicebus.data.client import DataMessage
from warpzone.transform.schema import generate_and_stringify_schema


def get_filepath(filename: str, subfolder: str = "data"):
    return Path(os.environ["PYTEST_CURRENT_TEST"]).parent / subfolder / filename


def read_pandas(filename: str, subfolder: str = "data") -> pd.DataFrame:
    """
    Read pandas DataFrame from test data.
    Datetimes and timedeltas are inferred automatically.

    Args:
        filename (str): CSV file with test data
        subfolder (str, optional): Subfolder relative to test being
            run currently (taken from  the environment variable PYTEST_CURRENT_TEST),
            from where to read the test data. Defaults to "data".
    """
    filepath = get_filepath(filename, subfolder)
    df = pdz.read_csv(filepath)

    return df


def read_bytes(filename: str, subfolder: str = "data") -> bytes:
    """
    Read bytes from test data.

    Args:
        filename (str): File with test data
        subfolder (str, optional): Subfolder relative to test being
            run currently (taken from  the environment variable PYTEST_CURRENT_TEST),
            from where to read the test data. Defaults to "data".
    """
    filepath = get_filepath(filename, subfolder)
    return filepath.read_bytes()


def read_data_msg(
    filename: str,
    subject: str,
    message_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    timestamp: Optional[dt.datetime] = None,
    subfolder: str = "data",
) -> DataMessage:
    suffixes = Path(filename).suffixes
    if suffixes[0] == ".df":
        df = read_pandas(filename, subfolder)
        schema = generate_and_stringify_schema(df)
        return DataMessage.from_pandas(
            df=df,
            subject=subject,
            schema=schema,
            message_id=message_id,
            metadata=metadata,
            timestamp=timestamp,
        )
    else:
        return DataMessage(
            content=read_bytes(filename, subfolder),
            extension="".join(suffixes).replace(".", "", 1),
            subject=subject,
            message_id=message_id,
            metadata=metadata,
            timestamp=timestamp,
        )
