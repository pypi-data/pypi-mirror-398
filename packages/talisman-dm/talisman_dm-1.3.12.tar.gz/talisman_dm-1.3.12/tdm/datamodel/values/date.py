from dataclasses import dataclass
from typing import Optional

from tdm.abstract.datamodel.value import AbstractValue, EnsureConfidenced
from tdm.abstract.json_schema import generate_model


@dataclass(frozen=True)
class Date(object):
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None


@dataclass(frozen=True)
class Time(object):
    hour: int
    minute: int
    second: int


@dataclass(frozen=True)
class _DateTimeValue(EnsureConfidenced):
    """
    Auxiliary class for `DateTimeValue` to fix dataclass fields order.

    Represents the internal structure of a `DateTimeValue`.

    Attributes
    ----------
    date:
        Normalized date representation.
    time:
        Optional normalized time representation.
    """
    date: Date
    time: Optional[Time] = None


@generate_model
@dataclass(frozen=True)
class DateTimeValue(AbstractValue, _DateTimeValue):
    """
    Represents a normalized KB value for date and time.
    """

    @classmethod
    def from_dict(cls, value: dict) -> 'DateTimeValue':
        """
        Create a `DateTimeValue` object from a dictionary.

        Expected value scheme is as follows:

        {
          "date": {
            "year": Optional[int],
            "month": Optional[int],
            "day": Optional[int]
          },
          "time": {
            "hour": int,
            "minute": int,
            "second": int
          }
        }

        Time part could be skipped.

        :param value: The dictionary containing the DateTimeValue information.
        :return: A DateTimeValue object.
        """
        args = {
            'date': Date(**value['date'])
        }
        if 'time' in value:
            args['time'] = Time(**value['time'])
        return cls(**args)
