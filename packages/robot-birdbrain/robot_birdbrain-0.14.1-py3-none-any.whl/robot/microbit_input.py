# pylint: disable=unused-argument

from robot.constant import Constant
from robot.exception import Exception
from robot.request import Request


class MicrobitInput(Request):
    @classmethod
    def acceleration(cls, device, sensor="Accelerometer"):
        """Gives the acceleration of X,Y,Z in m/sec2."""

        return cls.xyz_response(device, sensor, "float")

    @classmethod
    def compass(cls, device, sensor='Compass'):
        """Returns values 0-359 indicating the orentation of the Earth's
        magnetic field."""

        sensor_options = {}
        sensor_options['min_response'] = Constant.DEFAULT_DEGREES_MIN_RESPONSE
        sensor_options['max_response'] = Constant.DEFAULT_DEGREES_MAX_RESPONSE

        compass_option = None if sensor == 'Compass' else 'static'

        return cls.sensor_response(device, sensor, compass_option, sensor_options)

    @classmethod
    def magnetometer(cls, device, sensor="Magnetometer"):
        """Return the values of X,Y,Z of a magnetommeter."""
        return cls.xyz_response(device, sensor, "int")

    @classmethod
    def button(cls, device, button):
        """Return the status of the button asked. Specify button 'A', 'B', or
        'Logo'. Logo available for V2 micro:bit only."""
        button = button.capitalize()

        if button not in Constant.VALID_BUTTONS:
            raise Exception("Invalid button: " + button)

        return cls.request_status(cls.response('hummingbird', 'in', 'button', button, device))

    @classmethod
    def sound(cls, device, port=None):
        """Return the current sound level as an integer between 1 and 100.
        Available for V2 micro:bit only."""

        response = cls.response('hummingbird', 'in', "V2sensor", "Sound", device)

        if response == 'micro:bit v2 required':
            return 0

        return int(response)

    @classmethod
    def temperature(cls, device):
        """Return the current temperature as an integer in degrees Celcius.
        Available for V2 micro:bit only."""

        response = cls.response('hummingbird', 'in', "V2sensor", "Temperature", device)

        if response == 'micro:bit v2 required':
            return 0

        return int(response)

    @classmethod
    def is_shaking(cls, device):
        """Return true if the device is shaking, false otherwise."""

        return cls.request_status(cls.response('hummingbird', 'in', 'orientation', 'Shake', device))

    @classmethod
    def orientation(cls, device):
        """Return the orentation of the Microbit. Results found in Constant.HUMMINGBIRD_ORIENTATION_RESULTS"""
        return cls.orientation_response(
            device,
            "orientation",
            Constant.HUMMINGBIRD_ORIENTATIONS,
            Constant.HUMMINGBIRD_ORIENTATION_RESULTS,
            Constant.HUMMINGBIRD_ORIENTATION_IN_BETWEEN,
        )
