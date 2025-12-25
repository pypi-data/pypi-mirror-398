import pytest

from robot.exception import Exception
from robot.finch import Finch
from robot.hummingbird import Hummingbird


def helper_test_acceleration(device):
    response = device.acceleration()
    response = device.getAcceleration()

    assert -100.0 <= response[0] <= 100.0
    assert -100.0 <= response[1] <= 100.0
    assert -100.0 <= response[2] <= 100.0

    assert isinstance(response[0], float)
    assert isinstance(response[1], float)
    assert isinstance(response[2], float)


def helper_test_compass(device):
    response = device.compass()
    response = device.getCompass()

    assert 0 <= response <= 359
    assert isinstance(response, int)


def helper_test_magnetometer(device):
    response = device.magnetometer()
    response = device.getMagnetometer()

    assert -100 <= response[0] <= 100
    assert -100 <= response[1] <= 100
    assert -100 <= response[2] <= 100

    assert isinstance(response[0], int)
    assert isinstance(response[1], int)
    assert isinstance(response[2], int)


def helper_test_button(device):
    assert not device.button("A")
    assert not device.button("B")
    assert not device.button("LOGO")
    assert not device.button("Logo")
    assert not device.getButton("logo")

    with pytest.raises(Exception) as e:
        device.button("BAD")
    assert e.value.message == "Invalid button: Bad"


def helper_test_sound(device):
    response = device.sound(3)
    response = device.getSound(3)

    assert 0 <= response <= 100


def helper_test_temperature(device):
    response = device.temperature()
    response = device.getTemperature()

    assert 0 <= response <= 50


def helper_test_is_shaking(device):
    response = device.is_shaking()
    response = device.isShaking()

    assert not response


def helper_test_shared(device):
    helper_test_acceleration(device)
    helper_test_compass(device)
    helper_test_magnetometer(device)
    helper_test_button(device)
    helper_test_sound(device)
    helper_test_temperature(device)
    helper_test_is_shaking(device)


def test_shared():
    helper_test_shared(Hummingbird("A"))
    helper_test_shared(Finch("B"))
