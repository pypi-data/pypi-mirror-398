from time import sleep

import pytest

from robot.hummingbird import Hummingbird
from robot.hummingbird_output import HummingbirdOutput


def test_led():
    hummingbird = Hummingbird("A")

    HummingbirdOutput.led(hummingbird.device, 1, 50)
    sleep(0.15)

    HummingbirdOutput.led(hummingbird.device, 1, "0")

    with pytest.raises(Exception) as e:
        HummingbirdOutput.led(hummingbird.device, 5, 50)
    assert e.value.message == "Led port 5 out of range"


def test_tri_led():
    hummingbird = Hummingbird("A")

    HummingbirdOutput.tri_led(hummingbird.device, 1, 50, "50", 0)
    sleep(0.15)

    HummingbirdOutput.tri_led(hummingbird.device, 1, 0, 0, 0)

    with pytest.raises(Exception) as e:
        HummingbirdOutput.tri_led(hummingbird.device, 5, 50, "50", 0)
    assert e.value.message == "Tri_led port 5 out of range"


def test_position_servo():
    hummingbird = Hummingbird("A")

    HummingbirdOutput.position_servo(hummingbird.device, 1, 20)
    sleep(0.15)

    HummingbirdOutput.position_servo(hummingbird.device, 1, 160)
    sleep(0.15)


def test_rotation_servo():
    hummingbird = Hummingbird("A")

    HummingbirdOutput.rotation_servo(hummingbird.device, 2, 25)
    sleep(0.15)

    HummingbirdOutput.rotation_servo(hummingbird.device, "2", "-25")
    sleep(0.15)

    HummingbirdOutput.rotation_servo(hummingbird.device, 2, 0)
