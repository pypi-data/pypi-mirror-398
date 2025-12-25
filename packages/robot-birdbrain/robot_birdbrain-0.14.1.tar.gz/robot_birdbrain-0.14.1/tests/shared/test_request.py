import pytest

from robot.constant import Constant
from robot.exception import Exception
from robot.request import Request


def test_request_uri():
    uri = Request.uri(["in", "1", "2", "3", "4", ["99", 99], "something"])

    assert uri == "http://127.0.0.1:30061/in/1/2/3/4/99/99/something"


def test_connected():
    assert Request.is_connected("A")


def test_not_connected():
    assert not Request.is_connected("C")


def test_not_connected_connected():
    assert not Request.is_not_connected("A")


def test_not_connected_not_connected():
    assert Request.is_not_connected("C")


def test_response_with_false_arg():
    assert not Request.response("1", "false", "2")


def test_response():
    assert Request.response("hummingbird", "in", "orientation", "Shake", "A")


def test_response_status():
    assert not Request.response_status("hummingbird", "in", "orientation", "Shake", "A")


def test_response_no_connection():
    with pytest.raises(Exception) as e:
        Request.response("hummingbird", "in", "orientation", "Shake", "C")

    assert e.value.message == "The device is not connected: C"


def test_request_status():
    assert Request.request_status("all stopped")
    assert Request.request_status(None) is None


def test_stop_all():
    response = Request.stop_all("A")

    assert response


def test_disconnect():
    with pytest.raises(Exception) as e:
        Request.stop_all("C")

    assert e.value.message == "The device is not connected: C"


def test_xyz_response_no_connection():
    with pytest.raises(Exception):
        Request.xyz_response("C", "Accelerometer")


def test_xyz_response():
    xyz = Request.xyz_response("A", "Accelerometer", "float")

    assert isinstance(xyz, list)
    assert len(xyz) == 3


def test_calculate_speed():
    assert Request.calculate_speed(0) == 255
    assert Request.calculate_speed(9) == 255
    assert Request.calculate_speed(100) == 146.0
    assert Request.calculate_speed(-100) == 74.0

    assert Request.calculate_speed("0") == 255
    assert Request.calculate_speed("9") == 255
    assert Request.calculate_speed("100") == 146.0
    assert Request.calculate_speed("-100") == 74.0


def test_calculate_left_or_right():
    assert Request.calculate_left_or_right('L') == 'Left'
    assert Request.calculate_left_or_right('R') == 'Right'
    assert Request.calculate_left_or_right('BAD') == 'None'


def test_validate_port():
    assert Request.validate_port(1, Constant.VALID_LED_PORTS)
    assert Request.validate_port(2, Constant.VALID_LED_PORTS)
    assert Request.validate_port(3, Constant.VALID_LED_PORTS)
    assert Request.validate_port("1", Constant.VALID_LED_PORTS)

    with pytest.raises(Exception):
        Request.validate_port(4, Constant.VALID_LED_PORTS)
    with pytest.raises(Exception):
        Request.validate_port(-1, Constant.VALID_LED_PORTS)
    with pytest.raises(Exception):
        Request.validate_port("4", Constant.VALID_LED_PORTS)

    assert Request.validate_port("all", None, True)


def test_debugging():
    Constant.BIRDBRAIN_TEST = True

    assert Request.response("hummingbird", "in", "orientation", "Shake", "A")
    assert Request.request_status("false") is False
    assert Request.request_status("not connected") is False
    assert Request.request_status("invalid orientation") is False
    assert Request.request_status("invalid port") is False
    assert Request.request_status("nonsense") is None


def test_sensor_response():
    assert Request.sensor_response(None, None, False) is False


def test_orientation_response(mocker):
    mocker.patch.object(Request, "response", return_value="false")

    assert Request.orientation_response(None, None, "unknown", [], "in between") == "in between"


def test_extracted_device():
    assert Request.extracted_device('hummingbird', 'in', 'orientation', 'Shake', 'A') == 'A'
    assert Request.extracted_device(['hummingbird', 'in', 'orientation', 'Shake', 'A']) == 'A'
    assert Request.extracted_device(('hummingbird', 'in', 'orientation', 'Shake', 'A')) == 'A'
    assert Request.extracted_device([('hummingbird', 'in', 'orientation', 'Shake', 'A')]) == 'A'
    assert Request.extracted_device((['hummingbird', 'in', 'orientation', 'Shake', 'A'])) == 'A'

    assert Request.extracted_device('hummingbird', 'out', 'symbol', 'C', 'true/false/true/false') == 'C'
    assert Request.extracted_device('hummingbird', 'out', 'symbol', 'C', 'false/true/false/true') == 'C'

    assert Request.extracted_device('hummingbird', 'out', 'move', 'B', 'Forward', 7, 5) == 'B'


def test_extracted_device_with_no_match():
    with pytest.raises(Exception) as e:
        Request.extracted_device((['hummingbird', 'in', 'BAD']))

    assert str(e.value) == "Unable to extract device name: ['hummingbird', 'in', 'BAD']"
