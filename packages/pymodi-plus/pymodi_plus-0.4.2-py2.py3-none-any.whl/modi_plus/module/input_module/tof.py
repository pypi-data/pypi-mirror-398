"""Tof module."""

import struct
from modi_plus.module.module import InputModule


class Tof(InputModule):

    PROPERTY_DISTANCE_STATE = 2

    PROPERTY_OFFSET_DISTANCE = 0

    @property
    def distance(self) -> float:
        """Returns the distance of the object between 0cm and 100cm

        :return: The tof's distance to object.
        :rtype: float
        """

        offset = Tof.PROPERTY_OFFSET_DISTANCE
        raw = self._get_property(Tof.PROPERTY_DISTANCE_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data
