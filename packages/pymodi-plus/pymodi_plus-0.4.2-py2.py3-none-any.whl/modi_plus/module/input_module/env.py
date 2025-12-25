"""Env module."""

import struct
from modi_plus.module.module import InputModule


class Env(InputModule):

    # -- Property Numbers --
    PROPERTY_ENV_STATE = 2
    PROPERTY_RGB_STATE = 3
    PROPERTY_RAW_RGB_STATE = 4

    PROPERTY_OFFSET_ILLUMINANCE = 0
    PROPERTY_OFFSET_TEMPERATURE = 2
    PROPERTY_OFFSET_HUMIDITY = 4
    PROPERTY_OFFSET_VOLUME = 6

    # RGB property offsets (only available in version 2.x and above)
    PROPERTY_OFFSET_RED = 0
    PROPERTY_OFFSET_GREEN = 2
    PROPERTY_OFFSET_BLUE = 4
    PROPERTY_OFFSET_WHITE = 6
    PROPERTY_OFFSET_BLACK = 8
    PROPERTY_OFFSET_COLOR_CLASS = 10
    PROPERTY_OFFSET_BRIGHTNESS = 11

    PROPERTY_RAW_OFFSET_RED = 0
    PROPERTY_RAW_OFFSET_GREEN = 2
    PROPERTY_RAW_OFFSET_BLUE = 4
    PROPERTY_RAW_OFFSET_WHITE = 6

    PROPERTY_ENV_SET_RECORD_VOICE = 16
    PROPERTY_ENV_SET_RGB_MODE = 17

    RGB_MODE_AMBIENT = 0
    RGB_MODE_ON = 1
    RGB_MODE_DUALSHOT = 2

    @property
    def illuminance(self) -> int:
        """Returns the value of illuminance between 0 and 100

        :return: The environment's illuminance.
        :rtype: int
        """

        offset = Env.PROPERTY_OFFSET_ILLUMINANCE
        raw = self._get_property(Env.PROPERTY_ENV_STATE)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    def temperature(self) -> int:
        """Returns the value of temperature between -10 and 60

        :return: The environment's temperature.
        :rtype: int
        """

        offset = Env.PROPERTY_OFFSET_TEMPERATURE
        raw = self._get_property(Env.PROPERTY_ENV_STATE)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    def humidity(self) -> int:
        """Returns the value of humidity between 0 and 100

        :return: The environment's humidity.
        :rtype: int
        """

        offset = Env.PROPERTY_OFFSET_HUMIDITY
        raw = self._get_property(Env.PROPERTY_ENV_STATE)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    def volume(self) -> int:
        """Returns the value of volume between 0 and 100

        :return: The environment's volume.
        :rtype: int
        """

        offset = Env.PROPERTY_OFFSET_VOLUME
        raw = self._get_property(Env.PROPERTY_ENV_STATE)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    def _is_rgb_supported(self) -> bool:
        """Check if RGB properties are supported based on app version

        RGB is supported in app version 2.x and above.
        Version 1.x does not support RGB.

        :return: True if RGB is supported, False otherwise
        :rtype: bool
        """
        if not hasattr(self, '_Module__app_version') or self._Module__app_version is None:
            return False

        # Extract major version: version >> 13
        major_version = self._Module__app_version >> 13
        return major_version >= 2

    @property
    def red(self) -> int:
        """Returns the red color value between 0 and 100

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's red color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_OFFSET_RED
        raw = self._get_property(Env.PROPERTY_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def green(self) -> int:
        """Returns the green color value between 0 and 100

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's green color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_OFFSET_GREEN
        raw = self._get_property(Env.PROPERTY_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def blue(self) -> int:
        """Returns the blue color value between 0 and 100

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's blue color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_OFFSET_BLUE
        raw = self._get_property(Env.PROPERTY_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def white(self) -> int:
        """Returns the white color value between 0 and 100

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's white color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_OFFSET_WHITE
        raw = self._get_property(Env.PROPERTY_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def black(self) -> int:
        """Returns the black color value between 0 and 100

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's black color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_OFFSET_BLACK
        raw = self._get_property(Env.PROPERTY_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def color_class(self) -> int:
        """Returns the detected color class

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The detected color class (0=unknown, 1=red, 2=green, 3=blue, 4=white, 5=black).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_OFFSET_COLOR_CLASS
        raw = self._get_property(Env.PROPERTY_RGB_STATE)
        data = struct.unpack("B", raw[offset:offset + 1])[0]
        return data

    @property
    def brightness(self) -> int:
        """Returns the brightness value between 0 and 100

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's brightness value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_OFFSET_BRIGHTNESS
        raw = self._get_property(Env.PROPERTY_RGB_STATE)
        data = struct.unpack("B", raw[offset:offset + 1])[0]
        return data

    @property
    def rgb(self) -> tuple:
        """Returns the RGB color values as a tuple (red, green, blue)

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: Tuple of (red, green, blue) values, each between 0 and 100.
        :rtype: tuple
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        return (self.red, self.green, self.blue)

    @property
    def raw_red(self) -> int:
        """Returns the raw red value between 0 and 65536

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's red color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_RAW_OFFSET_RED
        raw = self._get_property(Env.PROPERTY_RAW_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def raw_green(self) -> int:
        """Returns the raw green value between 0 and 65536

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's green color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_RAW_OFFSET_GREEN
        raw = self._get_property(Env.PROPERTY_RAW_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def raw_blue(self) -> int:
        """Returns the raw blue color between 0 and 65535

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's blue color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_RAW_OFFSET_BLUE
        raw = self._get_property(Env.PROPERTY_RAW_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def raw_white(self) -> int:
        """Returns the raw white color between 0 and 65535

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: The environment's white color value (0-100%).
        :rtype: int
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        offset = Env.PROPERTY_RAW_OFFSET_WHITE
        raw = self._get_property(Env.PROPERTY_RAW_RGB_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def raw_rgb(self) -> tuple:
        """Returns the RGB color values as a tuple (raw_red, raw_green, raw_blue, raw_white)

        Note: This property is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :return: Tuple of (red, green, blue) values, each between 0 and 100.
        :rtype: tuple
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        return (self.raw_red, self.raw_green, self.raw_blue, self.raw_white)

    def set_rgb_mode(self, mode: int, duration: int = 3) -> None:
        """Sets the RGB mode of the Env module

        Note: This method is only available in Env module version 2.x and above.
        Version 1.x does not support RGB properties.

        :param mode: RGB mode to set (0=off, 1=on)
        :type mode: int
        :return: None
        :raises AttributeError: If app version is 1.x (RGB not supported)
        """
        if not self._is_rgb_supported():
            raise AttributeError(
                "RGB properties are not supported in Env module version 1.x. "
                "Please upgrade to version 2.x or above."
            )

        self._set_property(
            destination_id=self.id,
            property_num=Env.PROPERTY_ENV_SET_RGB_MODE,
            property_values=(("u8", mode),
                             ("u16", duration), ))
