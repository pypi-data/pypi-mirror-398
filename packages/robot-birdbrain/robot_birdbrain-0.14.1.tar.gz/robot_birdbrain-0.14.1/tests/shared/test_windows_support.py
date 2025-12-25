import pytest

from robot.constant import Constant
from robot.finch import Finch
from robot.finch_input import FinchInput
from robot.finch_output import FinchOutput
from robot.hummingbird import Hummingbird
from robot.hummingbird_input import HummingbirdInput
from robot.microbit_output import MicrobitOutput
from robot.request import Request
from robot.state import State


def test_windows_support(mocker):
    mocker.patch.object(Request, "response_from_uri", return_value="200")
    mocker.patch.object(FinchOutput, "wait", return_value=True)

    Request.is_connected('A')

    state = State()

    assert MicrobitOutput.point(state, "A", 3, 3, True)

    hummingbird = Hummingbird('A')

    with pytest.raises(Exception) as e:
        hummingbird.light(4)
    assert e.value.message == "Light port 4 out of range"

    with pytest.raises(Exception) as e:
        hummingbird.sound(4)
    assert e.value.message == "Sound port 4 out of range"

    with pytest.raises(Exception) as e:
        HummingbirdInput.sound("A", 4)
    assert e.value.message == "Sound port 4 out of range"

    assert FinchOutput.move("B", Constant.FORWARD, 7, 5, False)

    with pytest.raises(Exception) as e:
        assert FinchOutput.move("B", "BAD", 4, 5)
    assert e.value.message == "Bad Move Direction: BAD"

    with pytest.raises(Exception) as e:
        assert FinchOutput.turn("B", "BAD", 90, 50)
    assert e.value.message == "Bad Turn Direction: BAD"

    with pytest.raises(Exception) as e:
        FinchInput.encoder("B", "BAD")
    assert e.value.message == "Bad Encoder Side: BAD"


def test_windows_support_finch():
    finch = Finch('B')

    with pytest.raises(Exception) as e:
        finch.encoder("BAD")
    assert e.value.message == "Bad Encoder Side: BAD"


def test_windows_support_lost_connected(mocker):
    hummingbird = Hummingbird("A")

    mocker.patch.object(Request, "response_from_uri", return_value="200")
    mocker.patch.object(Request, "is_not_connected_response", return_value=False)
    mocker.patch.object(Request, "is_connected", return_value=False)

    with pytest.raises(Exception) as e:
        hummingbird.led(1, 50)
    assert str(e.value) == 'The device is not connected: A'
