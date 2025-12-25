from time import sleep, time

from robot.constant import Constant
from robot.finch_input import FinchInput
from robot.request import Request
from robot.utility import Utility


class FinchOutput(Request):
    @classmethod
    def beak(cls, device, r_intensity, g_intensity, b_intensity):
        """Set beak to a valid intensity. Each intensity should be an integer from 0 to 100."""
        return cls.tri_led_response(device, 1, r_intensity, g_intensity, b_intensity)

    @classmethod
    def tail(cls, device, port, r_intensity, g_intensity, b_intensity):
        """Set tail to a valid intensity. Port can be specified as 1, 2, 3, 4, or all.
        Each intensity should be an integer from 0 to 100."""

        if not port == "all":
            cls.validate_port(port, Constant.VALID_TAIL_PORTS)

            port = int(port) + 1  # tail starts counting at 2

        return cls.tri_led_response(device, port, r_intensity, g_intensity, b_intensity)

    @classmethod
    def move(cls, device, direction, distance, speed, wait_to_finish_movement=True):
        """Move the Finch forward or backward for a given distance at a given speed.
        Direction should be specified as 'F' or 'B'."""
        calc_direction = None

        Request.validate(direction, Constant.VALID_MOVE_DIRECTION, "Bad Move Direction: " + str(direction))

        if direction == Constant.FORWARD:
            calc_direction = 'Forward'
        if direction == Constant.BACKWARD:
            calc_direction = 'Backward'

        calc_distance = Utility.bounds(distance, -10000, 10000)
        calc_speed = Utility.bounds(speed, 0, 100)

        return cls.__move_and_wait(
            device, wait_to_finish_movement, 'hummingbird', 'out', 'move', device, calc_direction, calc_distance, calc_speed
        )

    @classmethod
    def turn(cls, device, direction, angle, speed, wait_to_finish_movement=True):
        """Turn the Finch right or left to a given angle at a given speed.
        Direction should be specified as 'R' or 'L'."""
        calc_direction = Request.calculate_left_or_right(direction)
        calc_angle = Utility.bounds(angle, 0, 360)
        calc_speed = Utility.bounds(speed, 0, 100)

        Request.validate(direction, Constant.VALID_TURN_DIRECTION, "Bad Turn Direction: " + str(direction))

        return cls.__move_and_wait(
            device, wait_to_finish_movement, 'hummingbird', 'out', 'turn', device, calc_direction, calc_angle, calc_speed
        )

    @classmethod
    def wait(cls, device):
        timeout_time = time() + Constant.MOVE_TIMEOUT_SECONDS

        while (timeout_time > time()) and (FinchInput.is_moving(device)):
            sleep(Constant.MOVE_CHECK_MOVING_DELAY)

        return True

    @classmethod
    def motors(cls, device, left_speed, right_speed):
        """Set the speed of each motor individually. Speed should be in
        the range of -100 to 100."""

        left_speed = Utility.bounds(left_speed, -100, 100)
        right_speed = Utility.bounds(right_speed, -100, 100)

        return Request.response_status('hummingbird', 'out', 'wheels', device, left_speed, right_speed)

    @classmethod
    def stop(cls, device):
        """Stop the Finch motors."""

        return Request.response_status('hummingbird', 'out', 'stopFinch', device)

    @classmethod
    def reset_encoders(cls, device):
        """Reset both encoder values to 0."""

        response = Request.response_status('hummingbird', 'out', 'resetEncoders', device)

        sleep(Constant.RESET_ENCODERS_DELAY)  # finch needs a chance to actually reset

        return response

    @classmethod
    def __move_and_wait(cls, device, wait_to_finish_movement, *args):
        response = Request.response_status(*args)

        sleep(Constant.MOVE_START_WAIT_SECONDS)  # hack to give time to start before waiting

        if wait_to_finish_movement:
            cls.wait(device)

        return response
