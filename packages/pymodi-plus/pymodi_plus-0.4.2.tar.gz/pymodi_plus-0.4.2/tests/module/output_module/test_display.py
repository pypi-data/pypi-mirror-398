import unittest

from modi_plus.module.output_module.display import Display
from modi_plus.util.message_util import parse_set_property_message
from modi_plus.util.unittest_util import MockConnection, MockDisplay


class TestDisplay(unittest.TestCase):
    """Tests for 'Display' class."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.connection = MockConnection()
        self.mock_kwargs = [-1, -1, self.connection]
        self.display = MockDisplay(*self.mock_kwargs)

    def tearDown(self):
        """Tear down test fixtures, if any."""

        del self.display

    def test_write_text(self):
        """Test write_text method."""

        mock_text = "0123456789abcdefghijklmnopqrstuvwxyz"
        self.display.text = mock_text
        set_messages = []

        n = Display.TEXT_SPLIT_LEN
        encoding_data = str.encode(str(mock_text)) + bytes(1)
        splited_data = [encoding_data[x - n:x] for x in range(n, len(encoding_data) + n, n)]
        for index, data in enumerate(splited_data):
            set_message = parse_set_property_message(
                -1, Display.PROPERTY_DISPLAY_WRITE_TEXT,
                (("bytes", data), )
            )
            set_messages.append(set_message)

        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        for set_message in set_messages:
            self.assertTrue(set_message in sent_messages)
        self.assertEqual(self.display.text, mock_text)

    def test_write_variable_xy(self):
        """Test write_variable_xy method."""

        mock_variable = 123
        mock_position = 5
        self.display.write_variable_xy(mock_position, mock_position, mock_variable)
        set_message = parse_set_property_message(
            -1, Display.PROPERTY_DISPLAY_WRITE_VARIABLE,
            (("u8", mock_position), ("u8", mock_position),
             ("float", mock_variable), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_write_variable_line(self):
        """Test write_variable_line method."""

        mock_variable = 123
        mock_line = 2
        self.display.write_variable_line(mock_line, mock_variable)
        set_message = parse_set_property_message(
            -1, Display.PROPERTY_DISPLAY_WRITE_VARIABLE,
            (("u8", 0), ("u8", mock_line * 20),
             ("float", mock_variable), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_draw_picture(self):
        """Test draw_picture method."""

        mock_name = Display.preset_pictures()[0]
        self.display.draw_picture(mock_name)
        set_message = parse_set_property_message(
            -1, Display.PROPERTY_DISPLAY_DRAW_PICTURE,
            (("u8", 0), ("u8", 0),
             ("u8", Display.WIDTH), ("u8", Display.HEIGHT),
             ("string", Display.PRESET_PICTURE[mock_name]), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_draw_dot(self):
        """Test draw_dot method."""

        mock_dot = bytes([0 for i in range(Display.DOT_LEN)])
        self.display.draw_dot(mock_dot)
        set_messages = []

        n = Display.DOT_SPLIT_LEN
        splited_data = [mock_dot[x - n:x] for x in range(n, len(mock_dot) + n, n)]
        for index, data in enumerate(splited_data):
            send_data = bytes([index]) + data
            set_message = parse_set_property_message(
                -1, Display.PROPERTY_DISPLAY_DRAW_DOT,
                (("bytes", send_data), )
            )
            set_messages.append(set_message)

        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        for set_message in set_messages:
            self.assertTrue(set_message in sent_messages)

    def test_set_offset(self):
        """Test set_offset method."""

        mock_x = 10
        mock_y = 20
        self.display.set_offset(mock_x, mock_y)
        set_message = parse_set_property_message(
            -1, Display.PROPERTY_DISPLAY_SET_OFFSET,
            (("s8", mock_x), ("s8", mock_y), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_reset(self):
        """Test reset method."""

        self.display.reset()
        set_message = parse_set_property_message(
            -1, Display.PROPERTY_DISPLAY_RESET,
            (("u8", 0), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)


if __name__ == "__main__":
    unittest.main()
