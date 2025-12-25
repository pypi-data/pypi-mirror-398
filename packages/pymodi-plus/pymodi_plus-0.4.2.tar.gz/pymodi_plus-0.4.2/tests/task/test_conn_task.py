import unittest
# from unittest import mock

from modi_plus.task.connection_task import ConnectionTask


class TestConnTask(unittest.TestCase):
    """Tests for 'ConnTask' class"""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.mock_kwargs = {"serialport_recv_q": None, "serialport_send_q": None}
        self.connection_task = ConnectionTask(**self.mock_kwargs)

    def tearDown(self):
        """Tear down test fixtures, if any."""
        del self.connection_task


if __name__ == "__main__":
    unittest.main()
