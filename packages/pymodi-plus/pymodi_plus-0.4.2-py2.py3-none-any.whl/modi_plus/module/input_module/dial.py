"""Dial module."""

import struct
from modi_plus.module.module import InputModule


class Dial(InputModule):

    PROPERTY_DIAL_STATE = 2

    PROPERTY_OFFSET_TURN = 0
    PROPERTY_OFFSET_SPEED = 2

    @property
    def turn(self) -> int:
        """Returns the angle of the dial between 0 and 100

        :return: The dial's angle.
        :rtype: int
        """

        offset = Dial.PROPERTY_OFFSET_TURN
        raw = self._get_property(Dial.PROPERTY_DIAL_STATE)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    def speed(self) -> int:
        """Returns the turn speed of the dial between -100 and 100

        :return: The dial's turn speed.
        :rtype: int
        """

        offset = Dial.PROPERTY_OFFSET_SPEED
        raw = self._get_property(Dial.PROPERTY_DIAL_STATE)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data
