from robot.device import Device
from robot.microbit_input import MicrobitInput
from robot.microbit_output import MicrobitOutput
from robot.request import Request


class Microbit(Device):
    def __init__(self, device='A', raise_exception_if_no_connection=True):
        super().__init__(device)

        self.connected = self.connect(raise_exception_if_no_connection)

    def display(self, device_list):
        return MicrobitOutput.display(self.state, self.device, device_list)

    def clear_display(self):
        return MicrobitOutput.clear_display(self.state, self.device)

    def point(self, x, y, value):
        return MicrobitOutput.point(self.state, self.device, x, y, value)

    def print(self, message):
        return MicrobitOutput.print(self.state, self.device, message)

    def play_note(self, note, beats):
        return MicrobitOutput.play_note(self.device, note, beats)

    def beep(self):
        return MicrobitOutput.play_note(self.device, 80, 0.333)

    def acceleration(self):
        return MicrobitInput.acceleration(self.device)

    def compass(self):
        return MicrobitInput.compass(self.device)

    def magnetometer(self):
        return MicrobitInput.magnetometer(self.device)

    def button(self, button):
        return MicrobitInput.button(self.device, button)

    def sound(self, port=None):
        return MicrobitInput.sound(self.device, port)

    def temperature(self):
        return MicrobitInput.temperature(self.device)

    def is_shaking(self):
        return MicrobitInput.is_shaking(self.device)

    def orientation(self):
        return MicrobitInput.orientation(self.device)

    def stop_all(self):
        Request.stop_all(self.device)

    getAcceleration = acceleration
    getButton = button
    getCompass = compass
    setDisplay = display
    isShaking = is_shaking
    getMagnetometer = magnetometer
    getOrientation = orientation
    playNote = play_note
    setPoint = point
    getSound = sound
    stopAll = stop_all
    getTemperature = temperature
