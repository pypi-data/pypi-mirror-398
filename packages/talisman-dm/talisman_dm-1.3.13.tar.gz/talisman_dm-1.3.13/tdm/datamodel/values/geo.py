from dataclasses import dataclass
from typing import Optional, Union

from tdm.abstract.datamodel.value import AbstractValue, EnsureConfidenced
from tdm.abstract.json_schema import generate_model


@dataclass(frozen=True)
class Coordinates(object):
    latitude: Union[float, int]
    longitude: Union[float, int]


@dataclass(frozen=True)
class _GeoPointValue(EnsureConfidenced):
    """
    Auxiliary class for `GeoPointValue` to fix dataclass fields order.

    Represents the internal structure of a `GeoPointValue`.

    Attributes
    ----------
    point:
        Optional normalized geo coordinates representation.
    name:
        Optional normalized location name representation.
    """
    point: Optional[Coordinates] = None
    name: Optional[str] = None


@generate_model
@dataclass(frozen=True)
class GeoPointValue(AbstractValue, _GeoPointValue):
    """
    Represents a normalized KB value for geolocation.
    """

    @classmethod
    def from_dict(cls, value: dict) -> 'GeoPointValue':
        """
        Create a `GeoPointValue` object from a dictionary.

        Expected value scheme is as follows:

        {
          "point": {
            "latitude": float,
            "longitude": float
          },
          "name": str
        }

        Both parts could be skipped.

        :param value: The dictionary containing the GeoPointValue information.
        :return: A GeoPointValue object.
        """
        args = {}
        if 'point' in value:
            args['point'] = Coordinates(**value['point'])
        if 'name' in value:
            args['name'] = value['name']
        return cls(**args)
