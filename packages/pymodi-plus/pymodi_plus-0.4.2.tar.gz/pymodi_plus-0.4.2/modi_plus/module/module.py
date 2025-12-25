"""Module module."""

import time
import json
from os import path
from typing import Tuple, Union
from importlib.util import find_spec

from modi_plus.util.message_util import parse_get_property_message, parse_set_property_message

BROADCAST_ID = 0xFFF


def get_module_type_from_uuid(uuid):
    module_type_num = uuid >> 32
    module_type = {
        # Setup modules
        0: "network",
        0x10: "battery",

        # Input modules
        0x2000: "env",
        0x2010: "imu",
        0x2030: "button",
        0x2040: "dial",
        0x2070: "joystick",
        0x2080: "tof",

        # Output modules
        0x4000: "display",
        0x4010: "motor",
        0x4011: "motor",
        0x4020: "led",
        0x4030: "speaker",
    }.get(module_type_num)
    return "network" if module_type is None else module_type


def get_module_from_name(module_type: str):
    """ Find module type for module initialize

    :param module_type: Type of the module in string
    :type module_type: str
    :return: Module corresponding to the type
    :rtype: Module
    """

    module_type = module_type[0].lower() + module_type[1:]
    module_name = module_type[0].upper() + module_type[1:]
    module_module = find_spec(f"modi_plus.module.input_module.{module_type}")
    if not module_module:
        module_module = find_spec(f"modi_plus.module.output_module.{module_type}")
    if not module_module:
        module_module = find_spec(f"modi_plus.module.setup_module.{module_type}")
    module_module = module_module.loader.load_module(module_module.name)
    return getattr(module_module, module_name)


def ask_modi_plus_device(devices):
    if not devices:
        raise ValueError(
            "No MODI+ network module(s) available!\n"
            "The network module that you\"re trying to connect, may in use."
        )
    for idx, dev in enumerate(devices):
        print(f"<{idx}>: {dev}")
    i = input("Choose your device index (ex: 0) : ")
    return devices[int(i)].lstrip("MODI+_")


class Module:
    """
    :param int id_: The id of the module.
    :param int uuid: The uuid of the module.
    """

    class Property:
        def __init__(self):
            self.value = None
            self.last_update_time = time.time()

    class GetValueInitTimeout(Exception):
        def __init__(self):
            super().__init__("property initialization failed\nplease check the module connection")

    RUN = 0
    WARNING = 1
    FORCED_PAUSE = 2
    ERROR_STOP = 3
    UPDATE_FIRMWARE = 4
    UPDATE_FIRMWARE_READY = 5
    REBOOT = 6
    PNP_ON = 1
    PNP_OFF = 2

    def __init__(self, id_, uuid, connection_task):
        self._id = id_
        self._uuid = uuid
        self._connection = connection_task
        self.module_type = str()

        # property
        self.prop_samp_freq = 91        # sampling_rate[ms] = (100 - property_sampling_frequency) * 11
        self.prop_request_period = 2    # [s]
        self.__get_properties = dict()
        self.__set_properties = dict()
        self.__last_set_property_num = None

        self.is_connected = True
        self.is_usb_connected = False
        self.has_printed = False
        self.last_updated_time = time.time()
        self.first_connected_time = None
        self.__app_version = None
        self.__os_version = None
        self._enable_get_property_timeout = True

    def __gt__(self, other):
        if self.first_connected_time is not None:
            if other.first_connected_time is not None:
                return self.first_connected_time > other.first_connected_time
            else:
                return False
        else:
            if other.first_connected_time is not None:
                return True
            else:
                return False

    def __lt__(self, other):
        if self.first_connected_time is not None:
            if other.first_connected_time is not None:
                return self.first_connected_time < other.first_connected_time
            else:
                return True
        else:
            if other.first_connected_time is not None:
                return False
            else:
                return True

    def __str__(self):
        return f"{self.__class__.__name__}(0x{self._id:X})"

    @property
    def app_version(self):
        version_string = ""
        version_string += str(self.__app_version >> 13) + "."
        version_string += str(self.__app_version % (2 ** 13) >> 8) + "."
        version_string += str(self.__app_version % (2 ** 8))
        return version_string

    @app_version.setter
    def app_version(self, version_info):
        self.__app_version = version_info

    @property
    def os_version(self):
        version_string = ""
        version_string += str(self.__os_version >> 13) + "."
        version_string += str(self.__os_version % (2 ** 13) >> 8) + "."
        version_string += str(self.__os_version % (2 ** 8))
        return version_string

    @os_version.setter
    def os_version(self, version_info):
        self.__os_version = version_info

    @property
    def id(self) -> int:
        return self._id

    @property
    def uuid(self) -> int:
        return self._uuid

    @property
    def is_up_to_date(self):
        root_path = path.join(path.dirname(__file__), "..", "assets")
        version_path = path.join(root_path, "version.txt")

        with open(version_path, "r") as version_file:
            try:
                version_info = json.loads(version_file.read())
            except Exception:
                pass

        app_version_info = version_info[self.module_type].lstrip("v").rstrip("\n")
        if self.module_type in ["env", "display", "speaker"]:
            os_version_info = version_info["os_e103"].lstrip("v").rstrip("\n")
        else:
            os_version_info = version_info["os_e230"].lstrip("v").rstrip("\n")

        app_version_digits = [int(digit) for digit in app_version_info.split(".")]
        os_version_digits = [int(digit) for digit in os_version_info.split(".")]

        latest_app_version = (
            app_version_digits[0] << 13
            | app_version_digits[1] << 8
            | app_version_digits[2]
        )
        latest_os_version = (
            os_version_digits[0] << 13
            | os_version_digits[1] << 8
            | os_version_digits[2]
        )

        return latest_app_version <= self.__app_version or latest_os_version <= self.__os_version

    def _get_property(self, property_type: int) -> bytearray:
        """ Get module property value and request

        :param property_type: Type of the requested property
        :type property_type: int
        """

        # Register property if not exists
        if property_type not in self.__get_properties:
            self.__get_properties[property_type] = self.Property()
            self.__request_property(self._id, property_type)

        # Request property value if not updated for 2 sec
        last_update = self.__get_properties[property_type].last_update_time
        if time.time() - last_update > self.prop_request_period:
            self.__request_property(self._id, property_type)

        if self.__get_properties[property_type].value is None:
            if self._enable_get_property_timeout:
                first_request_time = time.time()

                # 3s timeout
                while self.__get_properties[property_type].value is None:
                    if time.time() - first_request_time > 3:
                        raise Module.GetValueInitTimeout
                    time.sleep(0.1)
            else:
                return bytearray(14)  # Increased from 12 to 14 to support RGB properties (offset 12 + 2 bytes)

        return self.__get_properties[property_type].value

    def _set_property(self, destination_id: int,
                      property_num: int,
                      property_values: Union[Tuple, str],
                      force: bool = False) -> None:
        """Send the message of set_property command to the module

        :param destination_id: Id of the destination module
        :type destination_id: int
        :param property_num: Property Type
        :type property_num: int
        :param property_values: Property Values
        :type property_values: Tuple
        :param force: Force data to be sent
        :type force: bool
        :return: None
        """

        do_send = False
        now_time = time.time()

        if not self.__check_last_set_property(property_num):
            force = True

        if property_num in self.__set_properties:
            if property_values == self.__set_properties[property_num].value:
                duration = now_time - self.__set_properties[property_num].last_update_time
                if force or duration > self.prop_request_period:
                    # 마지막으로 보낸 데이터와 같은 경우, 2초마다 전송 or force가 true인 경우
                    self.__set_properties[property_num].value = property_values
                    self.__set_properties[property_num].last_update_time = now_time
                    do_send = True
            else:
                # 마지막으로 보낸 데이터와 다른 경우, 바로 전송
                self.__set_properties[property_num].value = property_values
                self.__set_properties[property_num].last_update_time = now_time
                do_send = True
        else:
            # 데이터를 한번도 안 보낸 경우, 바로 전송
            self.__set_properties[property_num] = self.Property()
            self.__set_properties[property_num].value = property_values
            self.__set_properties[property_num].last_update_time = now_time
            do_send = True

        if do_send:
            message = parse_set_property_message(
                destination_id,
                property_num,
                property_values,
            )
            self._connection.send_nowait(message)

        self.__last_set_property_num = property_num

    def update_property(self, property_type: int, property_value: bytearray) -> None:
        """ Update property value and time

        :param property_type: Type of the updated property
        :type property_type: int
        :param property_value: Value to update the property
        :type property_value: bytearray
        """

        if property_type not in self.__get_properties:
            self.__get_properties[property_type] = self.Property()
        self.__get_properties[property_type].value = property_value
        self.__get_properties[property_type].last_update_time = time.time()

    def __request_property(self, destination_id: int, property_type: int) -> None:
        """ Generate message for request property

        :param destination_id: Id of the destination module
        :type destination_id: int
        :param property_type: Type of the requested property
        :type property_type: int
        :return: None
        """

        self.__get_properties[property_type].last_update_time = time.time()
        req_prop_msg = parse_get_property_message(destination_id, property_type, self.prop_samp_freq)
        self._connection.send(req_prop_msg)

    def __check_last_set_property(self, property_num: int) -> bool:
        if self.__last_set_property_num is None:
            return False
        else:
            return self.__last_set_property_num == property_num


class SetupModule(Module):
    pass


class InputModule(Module):
    pass


class OutputModule(Module):
    pass


class ModuleList(list):

    def __init__(self, src, module_type=None):
        self.__src = src
        self.__module_type = module_type
        super().__init__(self.sublist())

    def __len__(self):
        return len(self.sublist())

    def __eq__(self, other):
        return super().__eq__(other)

    def __getitem__(self, key):
        if int(key) >= len(self):
            start_time = time.time()
            # 3s timeout
            while ((time.time() - start_time) < 3) and (int(key) >= len(self)):
                time.sleep(0.1)
            if int(key) >= len(self):
                raise Exception("Not enough modules exits!!")
        return self.sublist()[key]

    def get(self, module_id):
        for module in self.sublist():
            if module.id == module_id:
                return module
        raise Exception("Module with given id does not exits!!")

    def sublist(self):
        """ When accessing the module, the modules are sorted in an ascending order of
        1. the connected time from network module

        :return: Module
        """

        if self.__module_type:
            modules = list(filter(lambda module: module.module_type == self.__module_type, self.__src))
        else:
            modules = self.__src
        modules.sort()
        return modules

    def find(self, module_id):
        for idx, module in enumerate(self.sublist()):
            if module_id == module.id:
                return idx
        return -1
