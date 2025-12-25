# pylint: disable=redefined-builtin

from time import sleep

import pytest

from robot.constant import Constant
from robot.exception import Exception
from robot.finch import Finch
from robot.hummingbird import Hummingbird
from robot.request import Request


def test_is():
    finch = Finch("B")

    assert finch.is_connected()
    assert finch.is_microbit()
    assert not finch.is_hummingbird()
    assert finch.is_finch()

    assert finch.isConnectionValid()
    assert finch.isMicrobit()
    assert not finch.isHummingbird()
    assert finch.isFinch()

    with pytest.raises(Exception) as e:
        Hummingbird('B')
    assert e.value.message == "Error: Device B is not a Hummingbird"


def test_beak_with_alias():
    finch = Finch('B')

    finch.beak(100, 50, 50)
    sleep(0.15)
    finch.setBeak(0, 0, 0)


def test_tail_with_alias():
    finch = Finch("B")

    assert finch.tail(1, 10, 0, 50)
    sleep(0.1)
    assert finch.tail(1, "50", 0, "0")
    sleep(0.1)
    assert finch.tail("2", "50", 0, "0")
    sleep(0.1)
    assert finch.tail(3, "50", 0, "0")
    sleep(0.1)
    assert finch.tail(4, "50", 0, "0")
    sleep(0.1)
    assert finch.tail("all", 100, 0, 100)
    sleep(0.1)
    assert finch.setTail("all", 0, 0, 0)


def test_move_with_alias():
    finch = Finch("B")

    assert finch.move(Constant.FORWARD, 4, 20)
    assert finch.move(Constant.FORWARD, "4", "20")
    assert finch.move(Constant.BACKWARD, 4, 20)
    assert finch.setMove(Constant.BACKWARD, "4", "20")

    with pytest.raises(Exception) as e:
        finch = Finch("B")

        assert finch.move(None, 4, 20)

    assert e.value.message == "Bad Move Direction: None"

    with pytest.raises(Exception) as e:
        finch = Finch("B")

        assert finch.move("BAD", 4, 20)

    assert e.value.message == "Bad Move Direction: BAD"


def test_is_moving():
    finch = Finch("B")

    assert finch.move(Constant.FORWARD, 7, 5, False)
    assert finch.is_moving()

    assert finch.wait()

    assert finch.move(Constant.BACKWARD, 7, 5, True)

    finch.stop_all()

    sleep(1)

    assert not finch.is_moving()


def test_turn_with_alias():
    finch = Finch("B")

    finch.turn("L", 45, 50)
    finch.turn("R", 45, 50)
    finch.turn("L", "45", 50)
    finch.setTurn("R", 45, "50")


def test_motors_with_alias():
    finch = Finch("B")

    assert finch.motors(25, 0)
    sleep(0.2)
    assert finch.motors(-25, 0)
    sleep(0.2)

    assert finch.motors(0, -25)
    sleep(0.2)
    assert finch.motors("0", "25")
    sleep(0.2)

    Request.stop_all("B")

    Request.stop_all("B")


def test_stop():
    finch = Finch("B")

    assert finch.move(Constant.FORWARD, 99999, 5, False)
    sleep(0.2)
    assert finch.stop()

    assert finch.move(Constant.BACKWARD, 99999, 5, False)
    sleep(0.2)
    assert finch.stop()


def test_reset_encoders():
    finch = Finch("B")

    assert finch.reset_encoders()
    assert finch.resetEncoders()


def test_light_with_alias():
    finch = Finch("B")

    assert 0 <= finch.light("L") <= 100
    assert isinstance(finch.getLight("L"), int)

    assert 0 <= finch.light("R") <= 100
    assert isinstance(finch.getLight("R"), int)

    with pytest.raises(Exception) as e:
        finch.light("BAD")
    assert e.value.message == "Error: Request to device failed"


def test_distance_with_alias():
    finch = Finch("B")

    response = finch.distance()
    response = finch.getDistance()

    assert 0 <= response <= 298
    assert isinstance(response, int)


def test_line_with_alias():
    finch = Finch("B")

    assert 0 <= finch.line("L") <= 100
    assert isinstance(finch.getLine("L"), int)

    assert 0 <= finch.line("R") <= 100
    assert isinstance(finch.getLine("R"), int)

    with pytest.raises(Exception) as e:
        finch.line("BAD")
    assert e.value.message == "Error: Request to device failed"


def test_encoder_with_alias():
    finch = Finch("B")

    assert -100.0 <= finch.encoder("L") <= 100.0
    assert isinstance(finch.getEncoder("L"), float)

    assert -100.0 <= finch.encoder("R") <= 100.0
    assert isinstance(finch.getEncoder("R"), float)

    with pytest.raises(Exception) as e:
        finch.encoder("BAD")
    assert e.value.message == "Bad Encoder Side: BAD"


def test_orientation_with_alias():
    finch = Finch("B")

    response = finch.orientation()
    response = finch.getOrientation()

    some_position = False
    for orientation in Constant.FINCH_ORIENTATION_RESULTS:
        some_position = some_position or (orientation == response)

    assert some_position


def test_stop_all():
    finch = Finch("B")

    finch.stop_all()
    finch.stopAll()
