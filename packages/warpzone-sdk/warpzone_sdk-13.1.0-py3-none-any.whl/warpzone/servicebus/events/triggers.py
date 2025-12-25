from dataclasses import dataclass, fields

import datamazing.pandas as pdz
import pandas as pd

from warpzone.servicebus.events.client import EventMessage


def triggerclass(input_class):
    """Make trigger class with methods
    to convert from and to event messages.

    Example
    -------
    @triggerclass
    class ForecastTrigger:
        start_time: pd.Timedelta
        end_time: pd.Timedelta
    """
    data_cls = dataclass(input_class)

    class TriggerClass(data_cls):
        @classmethod
        def from_event_msg(cls, event_msg: EventMessage):
            """Convert event message to trigger"""
            kwargs = dict()
            for field in fields(cls):
                value = event_msg.event[field.name]
                # cast the value to the type
                # of the field (e.g. if the field
                # has a timestamp type, the value
                # will be parsed to this)
                match field.type:
                    case pd.Timestamp:
                        deserialized_value = pd.Timestamp(value)
                    case pd.Timedelta:
                        deserialized_value = pd.Timedelta(value)
                    case pdz.TimeInterval:
                        deserialized_value = pdz.TimeInterval.fromisoformat(value)
                    case _:
                        deserialized_value = value
                kwargs[field.name] = deserialized_value
            return cls(**kwargs)

        def to_event_msg(
            self,
            subject: str,
            message_id: str | None = None,
            time_to_live: pd.Timedelta | None = None,
        ) -> EventMessage:
            """Convert trigger to event message"""
            event = dict()
            if time_to_live:
                time_to_live = time_to_live.to_pytimedelta()
            for field in fields(self):
                value = getattr(self, field.name)
                # cast the value to a valid JSON
                # object (e.g. timestamps are converted
                # to strings in ISO format)
                match type(value):
                    case pd.Timestamp:
                        serialized_value = value.isoformat()
                    case pd.Timedelta:
                        serialized_value = value.isoformat()
                    case pdz.TimeInterval:
                        serialized_value = value.isoformat()
                    case _:
                        serialized_value = value
                event[field.name] = serialized_value

            return EventMessage(event, subject, message_id, time_to_live)

    return TriggerClass
