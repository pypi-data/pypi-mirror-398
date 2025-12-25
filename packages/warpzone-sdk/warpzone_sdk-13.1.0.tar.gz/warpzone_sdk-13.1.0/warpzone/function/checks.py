import datamazing.pandas as pdz

from warpzone.servicebus.events.client import EventMessage


def are_all_tables_updated(
    event_msg: EventMessage,
    db: pdz.Database,
    table_names: list[str],
) -> bool:
    """
    Check if all tables are updated for the
    interval contained in the table-upsert
    event message

    Args:
        event_msg (EventMessage): Table-upsert event message
        table_names (list[str]): Tables to check
    """
    time_interval = pdz.TimeInterval(
        left=event_msg.event["start_time"],
        right=event_msg.event["end_time"],
    )

    # get created times of the specified tables in the interval
    created_times_utc = set()
    for table_name in table_names:
        df = db.query(table_name, time_interval)
        if df.empty:
            return False
        created_times_utc.add(df["created_time_utc"][0])

    if len(created_times_utc) > 1:
        # if not all created times are the same, at least one is not updated
        return False

    return True
