"""Led module."""

import struct
from typing import Tuple
from modi_plus.module.module import OutputModule


class Led(OutputModule):

    PROPERTY_LED_STATE = 2

    PROPERTY_LED_SET_RGB = 16

    PROPERTY_OFFSET_RED = 0
    PROPERTY_OFFSET_GREEN = 2
    PROPERTY_OFFSET_BLUE = 4

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return self.red, self.green, self.blue

    @rgb.setter
    def rgb(self, color: Tuple[int, int, int]) -> None:
        """Sets the color of the LED light with given RGB values, and returns
        the current RGB values.

        :param color: RGB value to set
        :type color: Tuple[int, int, int]
        :return: None
        """

        self.set_rgb(color[0], color[1], color[2])

    @property
    def red(self) -> int:
        """Returns the current value of the red component of the LED

        :return: Red component
        :rtype: int
        """

        offset = Led.PROPERTY_OFFSET_RED
        raw = self._get_property(Led.PROPERTY_LED_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @red.setter
    def red(self, red: int) -> None:
        """Sets the red component of the LED light by given value

        :param red: Red component to set
        :type red: int
        :return: None
        """

        self.rgb = red, self.green, self.blue

    @property
    def green(self) -> int:
        """Returns the current value of the green component of the LED

        :return: Green component
        :rtype: int
        """

        offset = Led.PROPERTY_OFFSET_GREEN
        raw = self._get_property(Led.PROPERTY_LED_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @green.setter
    def green(self, green: int) -> None:
        """Sets the green component of the LED light by given value

        :param green: Green component to set
        :type green: int
        :return: None
        """

        self.rgb = self.red, green, self.blue

    @property
    def blue(self) -> int:
        """Returns the current value of the blue component of the LED

        :return: Blue component
        :rtype: int
        """

        offset = Led.PROPERTY_OFFSET_BLUE
        raw = self._get_property(Led.PROPERTY_LED_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @blue.setter
    def blue(self, blue: int) -> None:
        """Sets the blue component of the LED light by given value

        :param blue: Blue component to set
        :type blue: int
        :return: None
        """

        self.rgb = self.red, self.green, blue

    def set_rgb(self, red: int, green: int, blue: int) -> None:
        """Sets the color of the LED light with given RGB values, and returns
        the current RGB values.

        :param red: Red component to set
        :type red: int
        :param green: Green component to set
        :type green: int
        :param blue: Blue component to set
        :type blue: int
        :return: None
        """

        self._set_property(
            destination_id=self._id,
            property_num=Led.PROPERTY_LED_SET_RGB,
            property_values=(("u16", red),
                             ("u16", green),
                             ("u16", blue), )
        )

    #
    # Legacy Support
    #
    def turn_on(self) -> None:
        """Turn on led at maximum brightness.

        :return: RGB value of the LED set to maximum brightness
        :rtype: None
        """

        self.rgb = 100, 100, 100

    def turn_off(self) -> None:
        """Turn off led.

        :return: None
        """

        self.rgb = 0, 0, 0
