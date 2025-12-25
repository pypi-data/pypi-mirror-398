# pylint: disable=redefined-builtin, duplicate-code

import pytest

from robot.constant import Constant
from robot.exception import Exception
from robot.finch_input import FinchInput
from robot.finch_output import FinchOutput
from robot.request import Request


def test_is_moving():
    assert FinchOutput.move("B", Constant.FORWARD, 7, 5, False)
    assert FinchInput.is_moving("B")

    FinchOutput.wait("B")

    assert FinchOutput.move("B", Constant.BACKWARD, 7, 5, True)

    assert Request.stop_all("B")

    assert not FinchInput.is_moving("B")


def test_light():
    response = FinchInput.light("B", "L")

    assert 0 <= response <= 100
    assert isinstance(response, int)

    response = FinchInput.light("B", "R")

    assert 0 <= response <= 100
    assert isinstance(response, int)

    with pytest.raises(Exception) as e:
        FinchInput.light("B", "BAD")
    assert e.value.message == "Error: Request to device failed"

    with pytest.raises(Exception) as e:
        FinchInput.light("B", None)
    assert e.value.message == "Error: Request to device failed"


def test_distance():
    response = FinchInput.distance("B")

    assert 0 <= response <= 298
    assert isinstance(response, int)


def test_line():
    response = FinchInput.line("B", "L")

    assert 0 <= response <= 100
    assert isinstance(response, int)

    response = FinchInput.line("B", "R")

    assert 0 <= response <= 100
    assert isinstance(response, int)

    with pytest.raises(Exception) as e:
        FinchInput.line("B", "BAD")
    assert e.value.message == "Error: Request to device failed"

    with pytest.raises(Exception) as e:
        FinchInput.line("B", None)
    assert e.value.message == "Error: Request to device failed"


def test_encoder():
    response = FinchInput.encoder("B", "L")

    assert -100.0 <= response <= 100.0
    assert isinstance(response, float)

    response = FinchInput.encoder("B", "R")

    assert -100.0 <= response <= 100.0
    assert isinstance(response, float)

    with pytest.raises(Exception) as e:
        FinchInput.encoder("B", "BAD")
    assert e.value.message == "Bad Encoder Side: BAD"

    with pytest.raises(Exception) as e:
        FinchInput.encoder("B", None)
    assert e.value.message == "Bad Encoder Side: None"


def test_acceleration():
    response = FinchInput.acceleration("B")

    assert -100.0 <= response[0] <= 100.0
    assert -100.0 <= response[1] <= 100.0
    assert -100.0 <= response[2] <= 100.0

    assert isinstance(response[0], float)
    assert isinstance(response[1], float)
    assert isinstance(response[2], float)


def test_compass():
    response = FinchInput.compass("B")

    assert 0 <= response <= 359
    assert isinstance(response, int)


def test_magnetometer():
    response = FinchInput.magnetometer("B")

    assert -180.0 <= response[0] <= 180.0
    assert -180.0 <= response[1] <= 180.0
    assert -180.0 <= response[2] <= 180.0

    assert isinstance(response[0], int)
    assert isinstance(response[1], int)
    assert isinstance(response[2], int)


def test_orientation():
    response = FinchInput.orientation("B")

    some_position = False
    for orientation in Constant.FINCH_ORIENTATION_RESULTS:
        some_position = some_position or (orientation == response)

    assert some_position
