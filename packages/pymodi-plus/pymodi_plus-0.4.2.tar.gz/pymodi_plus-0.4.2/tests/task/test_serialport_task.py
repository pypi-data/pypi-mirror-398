import unittest

from unittest import mock

from modi_plus.task.serialport_task import SerialportTask


class TestSerialportTask(unittest.TestCase):
    """Tests for 'SerialportTask' class"""
    class MockSerial:
        def __init__(self):
            self.in_waiting = 1
            self.write = mock.Mock()
            self.close = mock.Mock()

        def read_mock(self):
            self.in_waiting = 0
            return "complete"

    def setUp(self):
        """Set up test fixtures, if any."""
        self.serialport_task = SerialportTask()

    def tearDown(self):
        """Tear down test fixtures, if any."""
        del self.serialport_task

    def test_close_conn(self):
        """Test close_conn method"""
        self.serialport_task._bus = self.MockSerial()
        self.serialport_task.close_connection()
        self.serialport_task.bus.close.assert_called_once_with()

    def test_recv_data(self):
        """Test _read_data method"""
        self.serialport_task._bus = self.MockSerial()
        self.serialport_task._recv_queue.put("complete")
        self.assertEqual(self.serialport_task.recv(), "complete")

    def test_send_data(self):
        """Test _write_data method"""
        self.serialport_task._bus = self.MockSerial()
        self.serialport_task.send("foo")
        self.serialport_task._bus.write.assert_called_once_with("foo".encode())


if __name__ == "__main__":
    unittest.main()
