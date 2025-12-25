import unittest

from modi_plus.module.setup_module.battery import Battery
from modi_plus.util.message_util import parse_get_property_message
from modi_plus.util.unittest_util import MockConnection, MockBattery


class TestBattery(unittest.TestCase):
    """Tests for 'Battery' class."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.connection = MockConnection()
        self.mock_kwargs = [-1, -1, self.connection]
        self.battery = MockBattery(*self.mock_kwargs)

    def tearDown(self):
        """Tear down test fixtures, if any."""

        del self.battery

    def test_get_level(self):
        """Test get_level method."""

        _ = self.battery.level
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Battery.PROPERTY_BATTERY_STATE, self.battery.prop_samp_freq)
        )
        self.assertEqual(_, 0.0)


if __name__ == "__main__":
    unittest.main()
