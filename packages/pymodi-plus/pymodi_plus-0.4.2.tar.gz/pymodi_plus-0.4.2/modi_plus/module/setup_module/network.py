"""Network module."""

import time
import struct
from importlib import import_module as im

from modi_plus.util.connection_util import get_ble_task_path
from modi_plus.module.module import SetupModule


def check_connection(func):
    """Check connection decorator
    """
    def wrapper(*args, **kwargs):
        if isinstance(args[0]._connection, im(get_ble_task_path()).BleTask):
            raise ValueError(f"{func.__name__} doen't supported for ble connection")
        return func(*args, **kwargs)
    return wrapper


class Network(SetupModule):

    STATE_TRUE = 100
    STATE_FALSE = 0

    STATE_JOYSTICK_UP = 100
    STATE_JOYSTICK_DOWN = -100
    STATE_JOYSTICK_LEFT = -50
    STATE_JOYSTICK_RIGHT = 50
    STATE_JOYSTICK_UNPRESSED = 0

    STATE_TIMER_REACHED = 100
    STATE_TIMER_UNREACHED = 0

    STATE_IMU_FRONT = 100
    STATE_IMU_REAR = -100
    STATE_IMU_LEFT = -50
    STATE_IMU_RIGHT = 50
    STATE_IMU_ORIGIN = 0

    STATE_BUZZER_ON = 100
    STATE_BUZZER_OFF = 0

    STATE_CAMERA_PICTURE = 100

    PROPERTY_NETWORK_RECEIVE_DATA = 2
    PROPERTY_NETWORK_BUTTON = 3
    PROPERTY_NETWORK_SWITCH = 4
    PROPERTY_NETWORK_DIAL = 5
    PROPERTY_NETWORK_JOYSTICK = 6
    PROPERTY_NETWORK_SLIDER = 7
    PROPERTY_NETWORK_TIMER = 8
    PROPERTY_NETWORK_IMU = 9
    PROPERTY_NETWORK_IMU_DIRECTION = 0

    PROPERTY_NETWORK_SEND_DATA = 2
    PROPERTY_NETWORK_SEND_TEXT = 3
    PROPERTY_NETWORK_BUZZER = 4
    PROPERTY_NETWORK_CAMERA = 5

    PROPERTY_OFFSET_BUTTON_PRESSED = 0
    PROPERTY_OFFSET_BUTTON_CLICKED = 2
    PROPERTY_OFFSET_BUTTON_DOUBLE_CLICKED = 4

    PROPERTY_OFFSET_IMU_ROLL = 0
    PROPERTY_OFFSET_IMU_PITCH = 2
    PROPERTY_OFFSET_IMU_YAW = 4

    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self.__buzzer_flag = True
        self.__esp_version = None

    @property
    def esp_version(self):
        if self.__esp_version:
            return self.__esp_version
        self._conn.send('{"c":160,"s":25,"d":4095,"b":"AAAAAAAAAA==","l":8}')
        while not self.__esp_version:
            time.sleep(0.01)
        return self.__esp_version

    @esp_version.setter
    def esp_version(self, version):
        self.__esp_version = version

    @check_connection
    def received_data(self, index: int = 0) -> int:
        """Returns received data from MODI Play

        :param index: Data's index
        :type index: int
        :return: Received data
        :rtype: int
        """

        property_num = Network.PROPERTY_NETWORK_RECEIVE_DATA + 100 * index
        offset = 0

        raw = self._get_property(property_num)
        data = struct.unpack("i", raw[offset:offset + 4])[0]
        return data

    @check_connection
    def button_pressed(self, index: int = 0) -> bool:
        """Returns whether MODI Play button is pressed

        :param index: Button's index
        :type index: int
        :return: True is pressed
        :rtype: bool
        """

        property_num = Network.PROPERTY_NETWORK_BUTTON + 100 * index
        offset = Network.PROPERTY_OFFSET_BUTTON_PRESSED

        raw = self._get_property(property_num)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Network.STATE_TRUE

    @check_connection
    def button_clicked(self, index: int = 0) -> bool:
        """Returns whether MODI Play button is clicked

        :param index: Button's index
        :type index: int
        :return: True is clicked
        :rtype: bool
        """

        property_num = Network.PROPERTY_NETWORK_BUTTON + 100 * index
        offset = Network.PROPERTY_OFFSET_BUTTON_CLICKED

        raw = self._get_property(property_num)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Network.STATE_TRUE

    @check_connection
    def button_double_clicked(self, index: int = 0) -> bool:
        """Returns whether MODI Play button is double clicked

        :param index: Button's index
        :type index: int
        :return: True is double clicked
        :rtype: bool
        """

        property_num = Network.PROPERTY_NETWORK_BUTTON + 100 * index
        offset = Network.PROPERTY_OFFSET_BUTTON_DOUBLE_CLICKED

        raw = self._get_property(property_num)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Network.STATE_TRUE

    @check_connection
    def switch_toggled(self, index: int = 0) -> bool:
        """Returns whether MODI Play switch is toggled

        :param index: Switch's index
        :type index: int
        :return: `True` if toggled or `False`.
        :rtype: bool
        """

        property_num = Network.PROPERTY_NETWORK_SWITCH + 100 * index
        offset = 0

        raw = self._get_property(property_num)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Network.STATE_TRUE

    @check_connection
    def dial_turn(self, index: int = 0) -> int:
        """Returns the current degree of MODI Play dial

        :param index: Dial's index
        :type index: int
        :return: Current degree
        :rtype: int
        """

        property_num = Network.PROPERTY_NETWORK_DIAL + 100 * index
        offset = 0

        raw = self._get_property(property_num)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @check_connection
    def joystick_direction(self, index: int = 0) -> str:
        """Returns the direction of the MODI Play joystick

        :param index: Joystick's index
        :type index: int
        :return: 'up', 'down', 'left', 'right', 'unpressed'
        :rtype: str
        """

        property_num = Network.PROPERTY_NETWORK_JOYSTICK + 100 * index
        offset = 0

        raw = self._get_property(property_num)
        data = struct.unpack("h", raw[offset:offset + 2])[0]

        return {
            Network.STATE_JOYSTICK_UP: "up",
            Network.STATE_JOYSTICK_DOWN: "down",
            Network.STATE_JOYSTICK_LEFT: "left",
            Network.STATE_JOYSTICK_RIGHT: "right",
            Network.STATE_JOYSTICK_UNPRESSED: "unpressed"
        }.get(data)

    @check_connection
    def slider_position(self, index: int = 0) -> int:
        """Returns the current percentage of MODI Play slider

        :param index: Slider's index
        :type index: int
        :return: Current percentage
        :rtype: int
        """

        property_num = Network.PROPERTY_NETWORK_SLIDER + 100 * index
        offset = 0

        raw = self._get_property(property_num)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    @check_connection
    def time_up(self) -> bool:
        """Returns if the MODI Play timer ticks

        :return: True if timer is up
        :rtype: bool
        """

        property_num = Network.PROPERTY_NETWORK_TIMER
        offset = 0

        raw = self._get_property(property_num)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data == Network.STATE_TIMER_REACHED

    @property
    @check_connection
    def imu_roll(self) -> int:
        """Returns the roll angle of the MODI Play imu

        :return: Roll angle.
        :rtype: int
        """

        property_num = Network.PROPERTY_NETWORK_IMU
        offset = Network.PROPERTY_OFFSET_IMU_ROLL

        raw = self._get_property(property_num)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    @check_connection
    def imu_pitch(self) -> int:
        """Returns the pitch angle of the MODI Play imu

        :return: Pitch angle.
        :rtype: int
        """

        property_num = Network.PROPERTY_NETWORK_IMU
        offset = Network.PROPERTY_OFFSET_IMU_PITCH

        raw = self._get_property(property_num)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    @check_connection
    def imu_yaw(self) -> int:
        """Returns the yaw angle of the MODI Play imu

        :return: Yaw angle.
        :rtype: int
        """

        property_num = Network.PROPERTY_NETWORK_IMU
        offset = Network.PROPERTY_OFFSET_IMU_YAW

        raw = self._get_property(property_num)
        data = struct.unpack("h", raw[offset:offset + 2])[0]
        return data

    @property
    @check_connection
    def imu_direction(self) -> str:
        """Returns the direction of the MODI Play imu

        :return: 'front', 'rear', 'left', 'right', 'origin'
        :rtype: str
        """

        property_num = Network.PROPERTY_NETWORK_IMU_DIRECTION
        offset = 0

        raw = self._get_property(property_num)
        data = struct.unpack("h", raw[offset:offset + 2])[0]

        return {
            Network.STATE_IMU_FRONT: "front",
            Network.STATE_IMU_REAR: "rear",
            Network.STATE_IMU_LEFT: "left",
            Network.STATE_IMU_RIGHT: "right",
            Network.STATE_IMU_ORIGIN: "origin"
        }.get(data)

    @check_connection
    def send_data(self, index: int, data: int) -> None:
        """Send text to MODI Play

        :param index: Data's index
        :type index: int
        :param data: Data to send.
        :type data: int
        :return: None
        """

        property_num = Network.PROPERTY_NETWORK_SEND_DATA + 0x100 * index

        self._set_property(
            destination_id=self._id,
            property_num=property_num,
            property_values=(("s32", data),),
            force=True
        )

    @check_connection
    def send_text(self, text: str) -> None:
        """Send text to MODI Play

        :param text: Text to send.
        :type text: str
        :return: None
        """

        self._set_property(
            destination_id=self._id,
            property_num=Network.PROPERTY_NETWORK_SEND_TEXT,
            property_values=(("string", text),),
            force=True
        )

    @check_connection
    def buzzer_on(self) -> None:
        """Turns on MODI Play buzzer

        :return: None
        """

        if self.__buzzer_flag:
            self.buzzer_off()
            self.__buzzer_flag = False

        self._set_property(
            destination_id=self._id,
            property_num=Network.PROPERTY_NETWORK_BUZZER,
            property_values=(("u8", Network.STATE_BUZZER_ON),)
        )

    @check_connection
    def buzzer_off(self) -> None:
        """Turns off MODI Play buzzer

        :return: None
        """

        self._set_property(
            destination_id=self._id,
            property_num=Network.PROPERTY_NETWORK_BUZZER,
            property_values=(("u8", Network.STATE_BUZZER_OFF),)
        )
        self.__buzzer_flag = False

    @check_connection
    def take_picture(self) -> None:
        """Takes a picture on MODI Play

        :return: None
        """

        self._set_property(
            destination_id=self._id,
            property_num=Network.PROPERTY_NETWORK_CAMERA,
            property_values=(("u8", Network.STATE_CAMERA_PICTURE),)
        )
