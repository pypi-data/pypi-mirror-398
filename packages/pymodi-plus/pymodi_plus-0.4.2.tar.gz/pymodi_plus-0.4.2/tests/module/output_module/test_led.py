import unittest

from modi_plus.module.output_module.led import Led
from modi_plus.util.message_util import parse_set_property_message, parse_get_property_message
from modi_plus.util.unittest_util import MockConnection, MockLed


class TestLed(unittest.TestCase):
    """Tests for 'Led' class."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.connection = MockConnection()
        self.mock_kwargs = -1, -1, self.connection
        self.led = MockLed(*self.mock_kwargs)

    def tearDown(self):
        """Tear down test fixtures, if any."""

        del self.led

    def test_set_rgb(self):
        """Test set_rgb method with user-defined inputs."""

        mock_red, mock_green, mock_blue = 10, 20, 100
        self.led.set_rgb(mock_red, mock_green, mock_blue)
        set_message = parse_set_property_message(
            -1, Led.PROPERTY_LED_SET_RGB,
            (("u16", mock_red), ("u16", mock_green), ("u16", mock_blue), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_set_red(self):
        """Test set_red method with user-defined inputs."""

        mock_red = 10
        self.led.red = mock_red
        set_message = parse_set_property_message(
            -1, Led.PROPERTY_LED_SET_RGB,
            (("u16", mock_red), ("u16", 0), ("u16", 0), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_set_green(self):
        """Test set_green method with user-defined inputs."""

        mock_green = 10
        self.led.green = mock_green
        set_message = parse_set_property_message(
            -1, Led.PROPERTY_LED_SET_RGB,
            (("u16", 0), ("u16", mock_green), ("u16", 0), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_set_blue(self):
        """Test set_blue method with user-defined inputs."""

        mock_blue = 10
        self.led.blue = mock_blue
        set_message = parse_set_property_message(
            -1, Led.PROPERTY_LED_SET_RGB,
            (("u16", 0), ("u16", 0), ("u16", mock_blue), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_get_red(self):
        """Test get_red method with none input."""

        _ = self.led.red
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Led.PROPERTY_LED_STATE, self.led.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_get_rgb(self):
        """Test get_rgb method with none input."""

        _ = self.led.rgb
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Led.PROPERTY_LED_STATE, self.led.prop_samp_freq)
        )
        self.assertEqual(_, (0, 0, 0))

    def test_get_green(self):
        """Test set_green method with none input."""

        _ = self.led.green
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Led.PROPERTY_LED_STATE, self.led.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_get_blue(self):
        """Test get blue method with none input."""

        _ = self.led.blue
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Led.PROPERTY_LED_STATE, self.led.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_turn_on(self):
        """Test turn_on method."""

        mock_red, mock_green, mock_blue = 100, 100, 100
        self.led.turn_on()
        set_message = parse_set_property_message(
            -1, Led.PROPERTY_LED_SET_RGB,
            (("u16", mock_red), ("u16", mock_green), ("u16", mock_blue), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_turn_off(self):
        """Test turn_off method."""

        mock_red, mock_green, mock_blue = 0, 0, 0
        self.led.turn_off()
        set_message = parse_set_property_message(
            -1, Led.PROPERTY_LED_SET_RGB,
            (("u16", mock_red), ("u16", mock_green), ("u16", mock_blue), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)


if __name__ == "__main__":
    unittest.main()
