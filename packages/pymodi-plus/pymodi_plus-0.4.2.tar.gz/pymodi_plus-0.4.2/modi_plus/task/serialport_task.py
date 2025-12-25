from typing import Optional
from queue import Queue
import threading as th

from serial.serialutil import SerialException

from modi_plus.task.connection_task import ConnectionTask
from modi_plus.util.connection_util import list_modi_ports
from modi_plus.util.modi_serialport import ModiSerialPort


class SerialportTask(ConnectionTask):

    def __init__(self, verbose=False, port=None):
        print("Initiating serial connection...")
        super().__init__(verbose)
        self.__port = port
        self.__json_buffer = b""
        self._recv_queue = Queue()
        self.__recv_thread = None
        self.__stop_signal = False

    #
    # Inherited Methods
    #
    def open_connection(self) -> None:
        """ Open serial port

        :return: None
        """

        modi_ports = list_modi_ports()
        if not modi_ports:
            raise SerialException("No MODI+ network module is available")

        if self.__port:
            if self.__port not in map(lambda info: info, modi_ports):
                raise SerialException(f"{self.__port} is not connected to a MODI+ network module.")
            else:
                try:
                    self._bus = self.__init_serial(self.__port)
                    self._bus.open()
                    self.__open_recv_thread()
                    return
                except SerialException:
                    raise SerialException(f"{self.__port} is not available.")

        for modi_port in modi_ports:
            self._bus = self.__init_serial(modi_port)
            try:
                self._bus.open(modi_port)
                self.__open_recv_thread()
                print(f'Serial is open at "{modi_port}"')
                return
            except SerialException:
                continue
        raise SerialException("No MODI+ port is available now")

    @staticmethod
    def __init_serial(port):
        ser = ModiSerialPort(timeout=0.01)
        return ser

    def __open_recv_thread(self):
        self.__json_buffer = b""
        self._recv_queue = Queue()
        self.__stop_signal = False
        self.__recv_thread = th.Thread(target=self.__recv_handler, daemon=True)
        self.__recv_thread.start()

    def __close_recv_thread(self):
        self.__stop_signal = True
        if self.__recv_thread:
            self.__recv_thread.join()

    def __recv_handler(self):
        while not self.__stop_signal:
            recv = self._bus.read()
            if recv:
                self.__json_buffer += recv

            header_index = self.__json_buffer.find(b"{")
            if header_index < 0:
                self.__json_buffer = b""
                continue
            self.__json_buffer = self.__json_buffer[header_index:]

            tail_index = self.__json_buffer.find(b"}")
            if tail_index < 0:
                continue

            json_pkt = self.__json_buffer[:tail_index + 1].decode("utf8")
            self.__json_buffer = self.__json_buffer[tail_index + 1:]
            self._recv_queue.put(json_pkt)

    def close_connection(self) -> None:
        """ Close serial port

        :return: None
        """

        self.__close_recv_thread()
        self._bus.close()

    def recv(self) -> Optional[str]:
        """ Read serial message and put message to serial read queue

        :return: str
        """

        if self._recv_queue.empty():
            return None

        json_pkt = self._recv_queue.get()
        if json_pkt is None:
            return None

        if self.verbose:
            print(f"recv: {json_pkt}")

        return json_pkt

    @ConnectionTask.wait
    def send(self, pkt: str, verbose=False) -> None:
        """ Send json pkt

        :param pkt: Json pkt to send
        :type pkt: str
        :param verbose: Verbosity parameter
        :type verbose: bool
        :return: None
        """

        self._bus.write(pkt.encode("utf8"))
        if self.verbose or verbose:
            print(f"send: {pkt}")

    def send_nowait(self, pkt: str, verbose=False) -> None:
        """ Send json pkt

        :param pkt: Json pkt to send
        :type pkt: str
        :param verbose: Verbosity parameter
        :type verbose: bool
        :return: None
        """

        self._bus.write(pkt.encode("utf8"))
        if self.verbose or verbose:
            print(f"send: {pkt}")
