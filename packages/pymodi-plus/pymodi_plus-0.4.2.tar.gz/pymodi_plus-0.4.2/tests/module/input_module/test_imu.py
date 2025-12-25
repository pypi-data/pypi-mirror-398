import unittest

from modi_plus.module.input_module.imu import Imu
from modi_plus.util.message_util import parse_get_property_message
from modi_plus.util.unittest_util import MockConnection, MockImu


class TestImu(unittest.TestCase):
    """Tests for 'Imu' class."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.connection = MockConnection()
        mock_args = (-1, -1, self.connection)
        self.imu = MockImu(*mock_args)

    def tearDown(self):
        """Tear down test fixtures, if any."""

        del self.imu

    def test_get_angle_x(self):
        """Test get_angle_x method."""

        _ = self.imu.angle_x
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ANGLE_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_angle_y(self):
        """Test get_angle_y method."""

        _ = self.imu.angle_y
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ANGLE_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_angle_z(self):
        """Test get_angle_z method."""

        _ = self.imu.angle_z
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ANGLE_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_angular_vel_x(self):
        """Test get_angular_vel_x method."""

        _ = self.imu.angular_vel_x
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_GYRO_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_angular_vel_y(self):
        """Test get_angular_vel_y method."""

        _ = self.imu.angular_vel_y
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_GYRO_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_angular_vel_z(self):
        """Test get_angular_vel_z method."""

        _ = self.imu.angular_vel_z
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_GYRO_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_acceleration_x(self):
        """Test get_acceleration_x method."""

        _ = self.imu.acceleration_x
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ACC_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_acceleration_y(self):
        """Test get_acceleration_x method."""

        _ = self.imu.acceleration_y
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ACC_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_acceleration_z(self):
        """Test get_acceleration_z method."""

        _ = self.imu.acceleration_z
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ACC_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_vibration(self):
        """Test get_vibration method."""

        _ = self.imu.vibration
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_VIBRATION_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)

    def test_get_angle(self):
        """Test get_angle_z method."""

        _ = self.imu.angle
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ANGLE_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, (0.0, 0.0, 0.0))

    def test_get_angular_velocity(self):
        """Test get_angular_velocity method."""

        _ = self.imu.angular_velocity
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_GYRO_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, (0.0, 0.0, 0.0))

    def test_get_acceleration(self):
        """Test get_acceleration method."""

        _ = self.imu.acceleration
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Imu.PROPERTY_ACC_STATE, self.imu.prop_samp_freq)
        )
        self.assertEqual(_, (0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
