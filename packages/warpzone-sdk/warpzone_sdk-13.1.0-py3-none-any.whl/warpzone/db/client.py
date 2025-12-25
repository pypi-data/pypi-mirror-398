from typing import Optional

import datamazing.pandas as pdz
import pandas as pd
import pyarrow.compute as pc
from azure.core.credentials import (
    AzureNamedKeyCredential,
    AzureSasCredential,
    TokenCredential,
)
from azure.identity import DefaultAzureCredential

from warpzone.deltastorage.slicing import HyperSlice
from warpzone.deltastorage.store import Store


def camel_case_to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case

    Args:
        name (str): Name in CamelCase
    """
    import re

    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


class WarpzoneDatabaseClient:
    def __init__(
        self,
        path: str,
        storage_options: dict[str, str] | None = None,
    ):
        self.store = Store(
            path=path,
            storage_options=storage_options,
        )

    @classmethod
    def from_storage_account(
        cls,
        storage_account: str,
        container_name: str = "datasets",
        credential: (
            AzureNamedKeyCredential | AzureSasCredential | TokenCredential
        ) = DefaultAzureCredential(),
    ):
        path = f"abfss://{container_name}@{storage_account}.dfs.core.windows.net"
        token = credential.get_token("https://storage.azure.com/.default")
        storage_options = {
            "account_name": storage_account,
            "token": token.token,
        }

        return cls(path=path, storage_options=storage_options)

    def get_unit_and_multiple(self, timedelta: pd.Timedelta) -> tuple[str | None, int]:
        """
        Get unit and multiple of a timedelta. E.g. for a timedelta of "PT5M" then
        unit = "minute" and multiple = 5.
        NOTE: Timedelta must have one and only one non-zero component,
        i.e. "PT0S" doesnt work, and neither does "PT5M10S".

        Args:
            timedelta (pd.Timedelta): Timedelta

        Returns:
            tuple[str, int]: Unit and multiple
        """
        components = timedelta.components._asdict()

        # remove plural ending from unit, since
        # this is the standard pyarrow uses
        components = {k[:-1]: v for k, v in components.items()}

        non_zero_components = {
            unit: multiple for unit, multiple in components.items() if multiple != 0
        }

        if len(non_zero_components) == 0:
            return None, 0

        if len(non_zero_components) != 1:
            raise ValueError("Timedelta must have one and only one non-zero multiple.")

        return next(iter(non_zero_components.items()))

    def relative_time_travel_version(
        self, time_column: str, block: pd.Timedelta, horizon: pd.Timedelta
    ) -> pc.Expression:
        """
        Get value to use for filtering a relative time travel
        (i.e. the interval [valid-from, valid-to] must contain
        this value)
        """
        unit, multiple = self.get_unit_and_multiple(block)

        if multiple == 0:
            # `pc.floor_temporal` fails with multiple=0,
            # but in this case we don't need to floor
            # the time anyway
            start_of_block = pc.field("time_utc")
        else:
            start_of_block = pc.floor_temporal(
                pc.field(time_column),
                multiple=multiple,
                unit=unit,
            )

        return start_of_block - horizon.to_pytimedelta()

    def time_travel_filter(
        self,
        time_travel: pdz.TimeTravel,
        time_column: str,
        valid_from_column: str,
        valid_to_column: str,
    ) -> list[HyperSlice]:
        """Filter delta table on a time travel

        Args:
            time_travel (pdz.TimeTravel): Time travel
            time_column (str): Time column name
            valid_from_column (str): Valid-from column name
            valid_to_column (str): Valid-to column name
        """
        match time_travel.tense:
            case "absolute":
                # If the time travel is absolute, we filter
                # to entries where [valid-from, valid-to]
                # contains `as_of_time`
                version = time_travel.as_of_time.to_pydatetime()
            case "relative":
                version = self.relative_time_travel_version(
                    time_column, time_travel.block, time_travel.horizon
                )

        return [
            HyperSlice((valid_from_column, "<=", version)),
            HyperSlice((valid_to_column, ">", version)),
        ]

    def query(
        self,
        table_name: str,
        time_interval: Optional[pdz.TimeInterval] = None,
        time_travel: Optional[pdz.TimeTravel] = None,
        filters: Optional[dict[str, object]] = None,
    ) -> pd.DataFrame:
        # We do 'camelCaseToSnake_case' conversion here because the old
        # naming convention used in WarpZone was CamelCase, while the new
        # naming convention is snake_case. The goal is to remove this
        #  when the CamelCase naming convention is no longer used.
        table_name = camel_case_to_snake_case(table_name)

        table = self.store.get_table(table_name)
        hyper_slice = []

        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple, set)):
                    hyper_slice.append((key, "in", value))
                else:
                    hyper_slice.append((key, "=", value))

        if time_interval:
            hyper_slice.append(("time_utc", ">=", time_interval.left))
            hyper_slice.append(("time_utc", "<=", time_interval.right))

        if time_travel is None:
            time_travel = pdz.TimeTravel(
                as_of_time=pd.Timestamp.utcnow(),
            )

        tt_filter = self.time_travel_filter(
            time_travel,
            time_column="time_utc",
            valid_from_column="valid_from_time_utc",
            valid_to_column="valid_to_time_utc",
        )
        hyper_slice.extend(tt_filter)

        pl_df = table.read(hyper_slice=HyperSlice(hyper_slice))

        pd_df = pl_df.to_pandas()

        # We convert truncate to second, and change to nanosecond
        # precision because this was used by the old solution (Azure Table Storage)
        for col in pd_df.select_dtypes(include=["datetime", "datetimetz"]).columns:
            pd_df[col] = pd_df[col].dt.floor("s").dt.as_unit("ns")
        return pd_df
