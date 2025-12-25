from robot.exception import Exception
from robot.finch_input import FinchInput
from robot.finch_output import FinchOutput
from robot.microbit import Microbit


class Finch(Microbit):
    """The Finch class includes the control of the outputs and inputs present
    in the Finch robot. When creating an instance, specify which robot by the
    device letter used in the BlueBirdConnector device list (A, B, or C)."""

    def __init__(self, device='A', raise_exception_if_no_connection=True):
        super().__init__(device)

        self.connected = self.connect(raise_exception_if_no_connection)

        if not self.is_finch():
            raise Exception("Error: Device " + device + " is not a Finch")

    def is_moving(self):
        return FinchInput.is_moving(self.device)

    def beak(self, r_intensity, g_intensity, b_intensity):
        return FinchOutput.beak(self.device, r_intensity, g_intensity, b_intensity)

    def tail(self, port, r_intensity, g_intensity, b_intensity):
        return FinchOutput.tail(self.device, port, r_intensity, g_intensity, b_intensity)

    def move(self, direction, distance, speed, wait_to_finish_movement=True):
        return FinchOutput.move(self.device, direction, distance, speed, wait_to_finish_movement)

    def turn(self, direction, angle, speed, wait_to_finish_movement=True):
        return FinchOutput.turn(self.device, direction, angle, speed, wait_to_finish_movement)

    def motors(self, left_speed, right_speed):
        return FinchOutput.motors(self.device, left_speed, right_speed)

    def wait(self):
        return FinchOutput.wait(self.device)

    def stop(self):
        return FinchOutput.stop(self.device)

    def reset_encoders(self):
        return FinchOutput.reset_encoders(self.device)

    def light(self, side):
        return FinchInput.light(self.device, side)

    def distance(self):
        return FinchInput.distance(self.device)

    def line(self, side):
        return FinchInput.line(self.device, side)

    def encoder(self, side):
        return FinchInput.encoder(self.device, side)

    def orientation(self):
        return FinchInput.orientation(self.device)

    def acceleration(self):
        return FinchInput.acceleration(self.device)

    def compass(self):
        return FinchInput.compass(self.device)

    def magnetometer(self):
        return FinchInput.magnetometer(self.device)

    getAcceleration = acceleration
    setBeak = beak
    getCompass = compass
    getDistance = distance
    getEncoder = encoder
    getLight = light
    getLine = line
    getMagnetometer = magnetometer
    setMotors = motors
    setMove = move
    getOrientation = orientation
    resetEncoders = reset_encoders
    setTail = tail
    setTurn = turn
