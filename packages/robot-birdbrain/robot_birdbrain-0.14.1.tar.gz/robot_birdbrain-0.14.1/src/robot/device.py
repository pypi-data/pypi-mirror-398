from time import sleep

from robot.constant import Constant
from robot.exception import Exception
from robot.request import Request
from robot.state import State


class Device:
    def __init__(self, device="A"):
        self.state = State()
        self.device = self.remap_device(device)
        self.connected = False

        if device is None:
            raise Exception("Missing device name")
        if device not in Constant.VALID_DEVICES:
            raise Exception("Invalid device name: " + device)

    def connect(self, raise_exception_if_no_connection=True):
        self.connect_device()

        if raise_exception_if_no_connection and not self.connected:
            raise Exception("No connection: " + self.device)

        return self

    def is_connected(self):
        """Determine if the device is connected"""

        return self.connected

    def __is_device(self, operator):
        response = Request.response("hummingbird", "in", operator, "static", self.device)

        return response == 'true'

    def is_microbit(self):
        """Determine if the device is a Microbit"""

        # allow hummingbird/finch to be seen as microbit
        # return self.__is_device("isMicrobit")
        return True

    def is_hummingbird(self):
        """Determine if the device is a hummingbird."""
        return self.__is_device("isHummingbird")

    def is_finch(self):
        """Determine if the device is a Finch"""

        return self.__is_device("isFinch")

    def remap_device(self, device):
        return device

    def connect_device(self):
        self.connected = Request.is_connected(self.device)

        return self.connected

    def stop_all(self):
        Request.stop_all(self.device)

    def set_cache(self, name, value):
        return self.state.set(name, value)

    def get_cache(self, name):
        return self.state.get(name)

    def sleep(self, seconds):
        sleep(seconds)

    isConnectionValid = is_connected
    isFinch = is_finch
    isHummingbird = is_hummingbird
    isMicrobit = is_microbit
