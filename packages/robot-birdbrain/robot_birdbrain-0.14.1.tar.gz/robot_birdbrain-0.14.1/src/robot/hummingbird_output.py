from robot.constant import Constant
from robot.request import Request
from robot.utility import Utility


class HummingbirdOutput(Request):
    @classmethod
    def led(cls, device, port, intensity):
        """Set led  of a certain port requested to a valid intensity."""
        cls.validate_port(port, Constant.VALID_LED_PORTS)

        calculated_intensity = Utility.bounds(Request.calculate_intensity(intensity), 0, 255)

        return Request.response_status('hummingbird', 'out', 'led', port, calculated_intensity, device)

    @classmethod
    def tri_led(cls, device, port, r_intensity, g_intensity, b_intensity):
        """Set TriLED  of a certain port requested to a valid intensity."""
        cls.validate_port(port, Constant.VALID_TRI_LED_PORTS)

        return cls.tri_led_response(device, port, r_intensity, g_intensity, b_intensity)

    @classmethod
    def position_servo(cls, device, port, angle):
        """Set Position servo of a certain port requested to a valid angle."""
        Request.validate_port(port, Constant.VALID_SERVO_PORTS)

        calculated_angle = Utility.bounds(Request.calculate_angle(angle), 0, 254)

        return Request.response_status('hummingbird', 'out', 'servo', port, calculated_angle, device)

    @classmethod
    def rotation_servo(cls, device, port, speed):
        """Set Rotation servo of a certain port requested to a valid speed."""
        Request.validate_port(port, Constant.VALID_SERVO_PORTS)

        calculated_speed = Request.calculate_speed(Utility.bounds(int(speed), -100, 100))

        return Request.response_status('hummingbird', 'out', 'rotation', port, calculated_speed, device)
