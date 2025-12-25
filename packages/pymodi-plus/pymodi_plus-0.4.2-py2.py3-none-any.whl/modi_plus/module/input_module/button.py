"""Button module."""

import struct
from modi_plus.module.module import InputModule


class Button(InputModule):

    STATE_TRUE = 100
    STATE_FALSE = 0

    PROPERTY_BUTTON_STATE = 2

    PROPERTY_OFFSET_CLICKED = 0
    PROPERTY_OFFSET_DOUBLE_CLICKED = 2
    PROPERTY_OFFSET_PRESSED = 4
    PROPERTY_OFFSET_TOGGLED = 6

    @property
    def clicked(self) -> bool:
        """Returns true when button is clicked

        :return: `True` if clicked or `False`.
        :rtype: bool
        """

        offset = Button.PROPERTY_OFFSET_CLICKED
        raw = self._get_property(Button.PROPERTY_BUTTON_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Button.STATE_TRUE

    @property
    def double_clicked(self) -> bool:
        """Returns true when button is double clicked

        :return: `True` if double clicked or `False`.
        :rtype: bool
        """

        offset = Button.PROPERTY_OFFSET_DOUBLE_CLICKED
        raw = self._get_property(Button.PROPERTY_BUTTON_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Button.STATE_TRUE

    @property
    def pressed(self) -> bool:
        """Returns true while button is pressed

        :return: `True` if pressed or `False`.
        :rtype: bool
        """

        offset = Button.PROPERTY_OFFSET_PRESSED
        raw = self._get_property(Button.PROPERTY_BUTTON_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Button.STATE_TRUE

    @property
    def toggled(self) -> bool:
        """Returns true when button is toggled

        :return: `True` if toggled or `False`.
        :rtype: bool
        """

        offset = Button.PROPERTY_OFFSET_TOGGLED
        raw = self._get_property(Button.PROPERTY_BUTTON_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Button.STATE_TRUE
