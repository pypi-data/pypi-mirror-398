import threading as th

from modi_plus.task.exe_task import ExeTask


class ExeThread(th.Thread):
    """
    :param dict() modules: dict() of module instance
    """

    def __init__(self, modules, connection_task):
        super().__init__(daemon=True)
        connection_task.open_connection()
        self.__exe_task = ExeTask(modules, connection_task)
        self.__kill_sig = False

    def close(self):
        self.__kill_sig = True

    def run(self) -> None:
        """ Run executor task

        :return: None
        """
        while True:
            self.__exe_task.run(delay=0.001)
            if self.__kill_sig:
                break
