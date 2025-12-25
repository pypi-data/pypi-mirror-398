import os
import sys
import platform
from typing import List

import serial.tools.list_ports as stl


def list_modi_ports() -> List[str]:
    """Returns a list of connected MODI ports

    :return: List[ListPortInfo]
    """
    info_list = []

    def __is_modi_port(port):
        return (port.vid == 0x2FDE and port.pid == 0x0003) or port.description == "MODI+ Network Module"
    modi_ports = [port for port in stl.comports() if __is_modi_port(port)]
    for modi_port in modi_ports:
        info_list.append(modi_port.device)

    if sys.platform.startswith("win"):
        from modi_plus.util.winusb import list_modi_winusb_paths
        path_list = list_modi_winusb_paths()
        for index, value in enumerate(path_list):
            info_list.append(value)

    return info_list


def is_on_pi() -> bool:
    """Returns whether connected to pi

    :return: true if connected to pi
    :rtype: bool
    """
    return os.name != "nt" and os.uname()[4][:3] == "arm"


def is_network_module_connected() -> bool:
    """Returns whether network module is connected

    :return: true if connected
    :rtype: bool
    """
    return bool(list_modi_ports())


def ask_modi_device(devices):
    if not devices:
        raise ValueError(
            "No MODI network module(s) available!\n"
            "The network module that you're trying to connect, may in use."
        )
    for idx, dev in enumerate(devices):
        print(f"<{idx}>: {dev}")
    i = input("Choose your device index (ex: 0) : ")
    return devices[int(i)].lstrip("MODI+_")


def get_platform():
    if platform.uname().node == "raspberrypi":
        return "rpi"
    elif platform.uname().node == "penguin":
        return "chrome"
    return sys.platform


def get_ble_task_path():
    mod_path = {
        "win32": "modi_plus.task.ble_task.ble_task_win",
        "darwin": "modi_plus.task.ble_task.ble_task_mac",
        "linux": "modi_plus.task.ble_task.ble_task_linux",
        "rpi": "modi_plus.task.ble_task.ble_task_rpi",
    }.get(get_platform())
    return mod_path


class MODIConnectionError(Exception):
    pass
