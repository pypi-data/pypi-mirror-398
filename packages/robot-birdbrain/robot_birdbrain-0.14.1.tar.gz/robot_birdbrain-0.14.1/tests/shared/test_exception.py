from robot.exception import Exception
from robot.hummingbird import Hummingbird


def test_exception():
    exception = Exception("MESSAGE")

    assert str(exception) == "MESSAGE"


def test_exception_stop_all():
    hummingbird = Hummingbird('A')

    exception = Exception("STOP", hummingbird)

    assert str(exception) == "STOP"
