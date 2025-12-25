"""Main MODI+ module."""

import time
import atexit

from importlib import import_module as im

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

from modi_plus.module.module import ModuleList
from modi_plus._exe_thread import ExeThread
from modi_plus.util.connection_util import get_platform, get_ble_task_path


class MODIPlus:
    network_uuids = {}

    def __call__(cls, *args, **kwargs):
        network_uuid = kwargs.get("network_uuid")
        connection_type = kwargs.get("connection_type")
        if connection_type != "ble":
            return super(MODIPlus, cls).__call__(*args, **kwargs)
        if not network_uuid:
            raise ValueError("Should input a valid network uuid!")
        if network_uuid not in cls.network_uuids:
            cls.network_uuids[network_uuid] = super(MODIPlus, cls).__call__(*args, **kwargs)
        return cls.network_uuids[network_uuid]

    def __init__(self, connection_type="serialport", verbose=False, port=None, network_uuid=""):
        self._modules = list()
        self._connection = self.__init_task(connection_type, verbose, port, network_uuid)
        self._exe_thread = ExeThread(self._modules, self._connection)

        print("Start initializing connected MODI+ modules")
        self._exe_thread.start()

        # check usb connected module
        init_time = time.time()
        while not self.__is_usb_connected():
            time.sleep(0.1)
            if time.time() - init_time > 3:
                print("MODI init timeout over. Check your module connection.")
                break

        print("MODI+ modules are initialized!")

        atexit.register(self.close)

    def __init_task(self, connection_type, verbose, port, network_uuid):
        if connection_type == "serialport":
            return im("modi_plus.task.serialport_task").SerialportTask(verbose, port)
        elif connection_type == "ble":
            if not network_uuid:
                raise ValueError("Network UUID not specified!")
            self.network_uuids[network_uuid] = self

            os = get_platform()
            if os == "chrome" or os == "linux":
                raise ValueError(f"{os} doen't supported for ble connection")

            return im(get_ble_task_path()).BleTask(verbose, network_uuid)
        else:
            raise ValueError(f"Invalid connection type: {connection_type}")

    def open(self):
        atexit.register(self.close)
        self._exe_thread = ExeThread(self._modules, self._connection)
        self._connection.open_connection()
        self._exe_thread.start()

    def close(self):
        atexit.unregister(self.close)
        print("Closing MODI+ connection...")
        self._exe_thread.close()
        self._connection.close_connection()

    def send(self, message):
        """Low level method to send json pkt directly to modules

        :param message: Json packet to send
        :return: None
        """
        self._connection.send_nowait(message)

    def recv(self):
        """Low level method to receive json pkt directly from modules

        :return: Json msg received
        :rtype: str if msg exists, else None
        """
        return self._connection.recv()

    def __get_module_by_id(self, module_id):
        for module in self._modules:
            if module.id == module_id:
                return module
        return None

    def __is_usb_connected(self):
        for module in self._modules:
            if module.is_usb_connected:
                return True
        return False

    def __get_connected_module_by_id(self, id):
        target = self.__get_module_by_id(id)
        if target is None:
            start_time = time.time()
            while time.time() - start_time < 3:
                target = self.__get_module_by_id(id)
                if target is not None:
                    return target
                time.sleep(0.1)
            raise Exception("Module with given id does not exits!")
        else:
            return target

    def network(self, id: int) -> Network:
        """Module Class of connected Network module.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "network":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not network!")
        return module

    def battery(self, id: int) -> Battery:
        """Module Class of connected Battery module.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "battery":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not battery!")
        return module

    def env(self, id: int) -> Env:
        """Module Class of connected Environment modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "env":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not env!")
        return module

    def imu(self, id: int) -> Imu:
        """Module Class of connected IMU modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "imu":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not imu!")
        return module

    def button(self, id: int) -> Button:
        """Module Class of connected Button modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "button":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not button!")
        return module

    def dial(self, id: int) -> Dial:
        """Module Class of connected Dial modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "dial":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not dial!")
        return module

    def joystick(self, id: int) -> Joystick:
        """Module Class of connected Joystick modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "joystick":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not joystick!")
        return module

    def tof(self, id: int) -> Tof:
        """Module Class of connected ToF modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "tof":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not tof!")
        return module

    def display(self, id: int) -> Display:
        """Module Class of connected Display modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "display":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not display!")
        return module

    def motor(self, id: int) -> Motor:
        """Module Class of connected Motor modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "motor":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not motor!")
        return module

    def led(self, id: int) -> Led:
        """Module Class of connected Led modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "led":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not led!")
        return module

    def speaker(self, id: int) -> Speaker:
        """Module Class of connected Speaker modules.
        """
        module = self.__get_connected_module_by_id(id)
        if module.module_type != "speaker":
            raise Exception(f"This module(0x{id:X}) is {module.module_type} not speaker!")
        return module

    @property
    def modules(self) -> ModuleList:
        """Module List of connected modules except network module.
        """
        return ModuleList(self._modules)

    @property
    def networks(self) -> ModuleList:
        """Module List of connected Network modules.
        """
        return ModuleList(self._modules, "network")

    @property
    def batterys(self) -> ModuleList:
        """Module List of connected Battery modules.
        """
        return ModuleList(self._modules, "battery")

    @property
    def envs(self) -> ModuleList:
        """Module List of connected Environment modules.
        """
        return ModuleList(self._modules, "env")

    @property
    def imus(self) -> ModuleList:
        """Module List of connected IMU modules.
        """
        return ModuleList(self._modules, "imu")

    @property
    def buttons(self) -> ModuleList:
        """Module List of connected Button modules.
        """
        return ModuleList(self._modules, "button")

    @property
    def dials(self) -> ModuleList:
        """Module List of connected Dial modules.
        """
        return ModuleList(self._modules, "dial")

    @property
    def joysticks(self) -> ModuleList:
        """Module List of connected Joystick modules.
        """
        return ModuleList(self._modules, "joystick")

    @property
    def tofs(self) -> ModuleList:
        """Module List of connected ToF modules.
        """
        return ModuleList(self._modules, "tof")

    @property
    def displays(self) -> ModuleList:
        """Module List of connected Display modules.
        """
        return ModuleList(self._modules, "display")

    @property
    def motors(self) -> ModuleList:
        """Module List of connected Motor modules.
        """
        return ModuleList(self._modules, "motor")

    @property
    def leds(self) -> ModuleList:
        """Module List of connected Led modules.
        """
        return ModuleList(self._modules, "led")

    @property
    def speakers(self) -> ModuleList:
        """Module List of connected Speaker modules.
        """
        return ModuleList(self._modules, "speaker")
