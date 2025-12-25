from typing import Optional

from modi_plus.task.connection_task import ConnectionTask


class BleTask(ConnectionTask):
    CHAR_UUID = "00008421-0000-1000-8000-00805f9b34fb"

    def __init__(self, verbose=False, uuid=None):
        super().__init__(verbose=verbose)

    def open_connection(self):
        pass

    def close_connection(self):
        pass

    def handle_disconnected(self, _):
        print("Device is being properly disconnected...")

    def recv(self) -> Optional[str]:
        return ""

    @ConnectionTask.wait
    def send(self, pkt: str) -> None:
        pass

    def send_nowait(self, pkt: str) -> None:
        pass
