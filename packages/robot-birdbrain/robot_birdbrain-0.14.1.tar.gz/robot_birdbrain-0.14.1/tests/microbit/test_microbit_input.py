# pylint: disable=duplicate-code

import pytest

from robot.constant import Constant
from robot.exception import Exception
from robot.microbit_input import MicrobitInput
from robot.request import Request


def test_acceleration():
    response = MicrobitInput.acceleration("A", "Accelerometer")
    response = MicrobitInput.acceleration("A")

    assert -100.0 <= response[0] <= 100.0
    assert -100.0 <= response[1] <= 100.0
    assert -100.0 <= response[2] <= 100.0

    assert isinstance(response[0], float)
    assert isinstance(response[1], float)
    assert isinstance(response[2], float)


def test_compass():
    response = MicrobitInput.compass("A", "Compass")
    response = MicrobitInput.compass("A")

    assert 0 <= response <= 359
    assert isinstance(response, int)


def test_magnetometer():
    response = MicrobitInput.magnetometer("A")

    assert -180.0 <= response[0] <= 180.0
    assert -180.0 <= response[1] <= 180.0
    assert -180.0 <= response[2] <= 180.0

    assert isinstance(response[0], int)
    assert isinstance(response[1], int)
    assert isinstance(response[2], int)


def test_button():
    assert not MicrobitInput.button("A", "A")
    assert not MicrobitInput.button("A", "B")
    assert not MicrobitInput.button("A", "LOGO")
    assert not MicrobitInput.button("A", "Logo")
    assert not MicrobitInput.button("A", "logo")

    with pytest.raises(Exception) as e:
        MicrobitInput.button("A", "BAD")
    assert e.value.message == "Invalid button: Bad"


def test_sound():
    response = MicrobitInput.sound("A")

    assert 0 <= response <= 100
    assert isinstance(response, int)


def test_temperature():
    response = MicrobitInput.temperature("A")

    assert 0 <= response <= 50
    assert isinstance(response, int)


def test_is_shaking():
    response = MicrobitInput.is_shaking("A")

    assert not response


def test_orientation():
    response = MicrobitInput.orientation("A")

    some_position = False
    for orientation in Constant.HUMMINGBIRD_ORIENTATION_RESULTS:
        some_position = some_position or (orientation == response)

    assert some_position


def test_v2_required_temperature(mocker):
    mocker.patch.object(Request, "response", return_value="micro:bit v2 required")

    response = MicrobitInput.temperature("A")

    assert response == 0


def test_v2_required_sound(mocker):
    mocker.patch.object(Request, "response", return_value="micro:bit v2 required")

    response = MicrobitInput.sound("A")

    assert response == 0
