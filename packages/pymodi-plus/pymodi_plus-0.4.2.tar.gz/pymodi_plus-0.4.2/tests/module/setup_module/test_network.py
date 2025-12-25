import unittest

from modi_plus.module.setup_module.network import Network
from modi_plus.util.message_util import parse_set_property_message, parse_get_property_message
from modi_plus.util.unittest_util import MockConnection, MockNetwork


class TestNetwork(unittest.TestCase):
    """Tests for 'Network' class."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.connection = MockConnection()
        self.mock_kwargs = [-1, -1, self.connection]
        self.network = MockNetwork(*self.mock_kwargs)

    def tearDown(self):
        """Tear down test fixtures, if any."""

        del self.network

    def test_received_data(self):
        """Test received_data method."""

        _ = self.network.received_data(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_RECEIVE_DATA, self.network.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_button_pressed(self):
        """Test button_pressed method."""

        _ = self.network.button_pressed(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_BUTTON, self.network.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_button_clicked(self):
        """Test button_clicked method."""

        _ = self.network.button_clicked(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_BUTTON, self.network.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_button_double_clicked(self):
        """Test button_double_clicked method."""

        _ = self.network.button_double_clicked(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_BUTTON, self.network.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_switch_toggled(self):
        """Test switch_toggled method."""

        _ = self.network.switch_toggled(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_SWITCH, self.network.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_dial_turn(self):
        """Test dial_turn method."""

        _ = self.network.dial_turn(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_DIAL, self.network.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_joystick_direction(self):
        """Test joystick_direction method."""

        _ = self.network.joystick_direction(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_JOYSTICK, self.network.prop_samp_freq)
        )
        self.assertEqual(_, "unpressed")

    def test_slider_position(self):
        """Test slider_position method."""

        _ = self.network.slider_position(0)
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_SLIDER, self.network.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_time_up(self):
        """Test time_up method."""

        _ = self.network.time_up
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_TIMER, self.network.prop_samp_freq)
        )
        self.assertEqual(_, False)

    def test_imu_roll(self):
        """Test imu_roll method."""

        _ = self.network.imu_roll
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_IMU, self.network.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_imu_pitch(self):
        """Test imu_pitch method."""

        _ = self.network.imu_pitch
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_IMU, self.network.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_imu_yaw(self):
        """Test imu_yaw method."""

        _ = self.network.imu_yaw
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_IMU, self.network.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_imu_direction(self):
        """Test imu_direction method."""

        _ = self.network.imu_direction
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Network.PROPERTY_NETWORK_IMU_DIRECTION, self.network.prop_samp_freq)
        )
        self.assertEqual(_, "origin")

    def test_send_data(self):
        """Test send_data method."""

        data = 123
        self.network.send_data(0, data)
        set_message = parse_set_property_message(
            -1, Network.PROPERTY_NETWORK_SEND_DATA,
            (("s32", data),)
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_send_text(self):
        """Test send_text method."""

        text = "MODI+"
        self.network.send_text(text)
        set_message = parse_set_property_message(
            -1, Network.PROPERTY_NETWORK_SEND_TEXT,
            (("string", text), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_buzzer_on(self):
        """Test buzzer_on method."""

        self.network.buzzer_on()
        set_message = parse_set_property_message(
            -1, Network.PROPERTY_NETWORK_BUZZER,
            (("u8", Network.STATE_BUZZER_ON), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_buzzer_off(self):
        """Test buzzer_off method."""

        self.network.buzzer_off()
        set_message = parse_set_property_message(
            -1, Network.PROPERTY_NETWORK_BUZZER,
            (("u8", Network.STATE_BUZZER_OFF), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_take_picture(self):
        """Test take_picture method."""

        self.network.take_picture()
        set_message = parse_set_property_message(
            -1, Network.PROPERTY_NETWORK_CAMERA,
            (("u8", Network.STATE_CAMERA_PICTURE), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)


if __name__ == "__main__":
    unittest.main()
