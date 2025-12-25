from modi_plus.module.setup_module.network import Network
from modi_plus.module.setup_module.battery import Battery
from modi_plus.module.input_module.env import Env
from modi_plus.module.input_module.imu import Imu
from modi_plus.module.input_module.button import Button
from modi_plus.module.input_module.dial import Dial
from modi_plus.module.input_module.joystick import Joystick
from modi_plus.module.input_module.tof import Tof
from modi_plus.module.output_module.display import Display
from modi_plus.module.output_module.motor import Motor
from modi_plus.module.output_module.led import Led
from modi_plus.module.output_module.speaker import Speaker


class MockConnection:
    def __init__(self):
        self.send_list = []

    def send(self, pkt):
        self.send_list.append(pkt)

    def send_nowait(self, pkt):
        self.send_list.append(pkt)

    def recv(self):
        return "Test"


class MockNetwork(Network):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockBattery(Battery):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockEnv(Env):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockImu(Imu):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockButton(Button):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockDial(Dial):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockJoystick(Joystick):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockTof(Tof):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockDisplay(Display):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockMotor(Motor):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockLed(Led):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False


class MockSpeaker(Speaker):
    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._enable_get_property_timeout = False
