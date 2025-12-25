"""Battery module."""

import struct
from modi_plus.module.module import SetupModule


class Battery(SetupModule):

    PROPERTY_BATTERY_STATE = 2

    PROPERTY_OFFSET_LEVEL = 0

    @property
    def level(self) -> float:
        """Returns the level value

        :return: The battery's level.
        :rtype: float
        """

        offset = Battery.PROPERTY_OFFSET_LEVEL
        raw = self._get_property(Battery.PROPERTY_BATTERY_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data
