import unittest

from modi_plus.module.input_module.button import Button
from modi_plus.util.message_util import parse_get_property_message
from modi_plus.util.unittest_util import MockConnection, MockButton


class TestButton(unittest.TestCase):
    """Tests for 'Button' class."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.connection = MockConnection()
        mock_args = (-1, -1, self.connection)
        self.button = MockButton(*mock_args)

    def tearDown(self):
        """Tear down test fixtures, if any."""

        del self.button

    def test_get_clicked(self):
        """Test get_clicked method."""

        _ = self.button.clicked
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Button.PROPERTY_BUTTON_STATE, self.button.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_get_double_clicked(self):
        """Test get_double_clicked method."""

        _ = self.button.double_clicked
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Button.PROPERTY_BUTTON_STATE, self.button.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_get_pressed(self):
        """Test get_pressed method."""

        _ = self.button.pressed
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Button.PROPERTY_BUTTON_STATE, self.button.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_get_toggled(self):
        """Test get_toggled method."""

        _ = self.button.toggled
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Button.PROPERTY_BUTTON_STATE, self.button.prop_samp_freq)
        )
        self.assertEqual(_, False)


if __name__ == "__main__":
    unittest.main()
