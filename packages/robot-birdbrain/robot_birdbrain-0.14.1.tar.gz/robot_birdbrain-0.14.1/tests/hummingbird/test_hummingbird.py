from time import sleep

import pytest

from robot.constant import Constant
from robot.exception import Exception
from robot.finch import Finch
from robot.hummingbird import Hummingbird
from robot.request import Request


def test_connect_device_name_as_none():
    with pytest.raises(Exception) as e:
        Hummingbird(None)
    assert e.value.message == "Missing device name"


def test_connect_bad_device_name():
    with pytest.raises(Exception) as e:
        Hummingbird('D')
    assert e.value.message == "Invalid device name: D"


def test_connect_valid_device_name():
    hummingbird = Hummingbird("A")

    assert hummingbird.device == "A"


def test_is():
    hummingbird = Hummingbird("A")

    assert hummingbird.is_connected()
    assert hummingbird.is_microbit()
    assert hummingbird.is_hummingbird()
    assert not hummingbird.is_finch()

    assert hummingbird.isConnectionValid()
    assert hummingbird.isMicrobit()
    assert hummingbird.isHummingbird()
    assert not hummingbird.isFinch()

    with pytest.raises(Exception) as e:
        Finch('A')
    assert e.value.message == "Error: Device A is not a Finch"


def test_led_with_alias():
    hummingbird = Hummingbird("A")

    assert hummingbird.led(1, 100)
    sleep(0.15)

    assert hummingbird.led(1, 0)
    sleep(0.15)

    assert hummingbird.led(1, 50)
    sleep(0.15)

    hummingbird.setLED(1, 0)


def test_led_no_connection():
    with pytest.raises(Exception) as e:
        Hummingbird('C')
    assert e.value.message == "No connection: C"


def test_tri_led_with_alias():
    hummingbird = Hummingbird("A")

    assert hummingbird.tri_led(1, 50, "50", 0)
    sleep(0.15)

    assert hummingbird.setTriLED(1, 100, "0", "0")
    sleep(0.15)

    assert hummingbird.tri_led(1, 0, "0", "0")
    sleep(0.15)


def test_position_servo_with_alias():
    hummingbird = Hummingbird("A")

    assert hummingbird.position_servo(1, 50)
    sleep(0.15)

    assert hummingbird.setPositionServo(1, "130")


def test_rotation_servo_with_alias():
    hummingbird = Hummingbird("A")

    assert hummingbird.rotation_servo(2, 50)
    sleep(0.15)

    assert hummingbird.setRotationServo(2, "-50")
    sleep(0.15)

    assert hummingbird.rotation_servo(2, 100)
    sleep(0.15)

    assert hummingbird.setRotationServo(2, -100)
    sleep(0.15)

    assert hummingbird.setRotationServo(2, 0)


def test_orientation_with_alias():
    hummingbird = Hummingbird("A")

    response = hummingbird.orientation()
    response = hummingbird.getOrientation()

    some_position = False
    for orientation in Constant.HUMMINGBIRD_ORIENTATION_RESULTS:
        some_position = some_position or (orientation == response)

    assert some_position


def test_sensor():
    hummingbird = Hummingbird("A")

    response = hummingbird.sensor(1)
    response = hummingbird.getSensor(1)

    assert isinstance(response, float)


def test_light_with_alias():
    hummingbird = Hummingbird("A")

    response = hummingbird.light(3)
    response = hummingbird.getLight(3)
    response = hummingbird.light("3")

    assert 0 <= response <= 100
    assert isinstance(response, int)

    with pytest.raises(Exception) as e:
        response = hummingbird.light(4)
    assert e.value.message == "Light port 4 out of range"


def test_sound_with_alias():
    hummingbird = Hummingbird("A")

    response = hummingbird.sound(3)
    response = hummingbird.getSound(3)
    response = hummingbird.sound("3")

    assert 0 <= response <= 100
    assert isinstance(response, int)

    with pytest.raises(Exception) as e:
        response = hummingbird.sound(4)
    assert e.value.message == "Sound port 4 out of range"


def test_sound_microbit():
    hummingbird = Hummingbird("A")

    response = hummingbird.sound("micro:bit")

    assert 0 <= response <= 100
    assert isinstance(response, int)


def test_distance_with_alias():
    hummingbird = Hummingbird("A")

    response = hummingbird.distance(2)
    response = hummingbird.getDistance(2)
    response = hummingbird.distance("2")

    assert 0 <= response <= 298
    assert isinstance(response, int)


def test_dial_with_alias():
    hummingbird = Hummingbird("A")

    response = hummingbird.dial(1)
    response = hummingbird.getDial(1)
    response = hummingbird.dial("1")

    assert 0 <= response <= 100
    assert isinstance(response, int)


def test_voltage_with_alias():
    hummingbird = Hummingbird("A")

    response = hummingbird.voltage(1)
    response = hummingbird.getVoltage(1)

    assert isinstance(response, float)


def test_stop_all():
    hummingbird = Hummingbird("A")

    hummingbird.stop_all()
    hummingbird.stopAll()


def test_lost_connected(mocker):
    hummingbird = Hummingbird("A")

    mocker.patch.object(Request, "is_not_connected_response", return_value=True)
    mocker.patch.object(Request, "is_connected", return_value=False)

    with pytest.raises(Exception) as e:
        hummingbird.led(1, 50)
    assert str(e.value) == 'The device is not connected: A'
