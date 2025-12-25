from robot.utility import Utility


def test_is_none_or_empty():
    assert Utility.is_none_or_empty(None)
    assert Utility.is_none_or_empty('')
    assert not Utility.is_none_or_empty('something')


def test_bounds():
    assert Utility.bounds(10, 0, 100) == 10
    assert Utility.bounds(10, -100, 100) == 10
    assert Utility.bounds(-10, -100, 100) == -10
    assert Utility.bounds(-100, -100, 100) == -100
    assert Utility.bounds(100, -100, 100) == 100

    assert Utility.bounds(101, -100, 100) == 100
    assert Utility.bounds(-101, -100, 100) == -100
    assert Utility.bounds(999999, -100, 100) == 100
    assert Utility.bounds(-999999, -100, 100) == -100

    assert Utility.bounds(10.0, 0.0, 100.0) == 10.0
    assert Utility.bounds(10.0, -100.0, 100.0) == 10.0
    assert Utility.bounds(-10.0, -100.0, 100.0) == -10.0
    assert Utility.bounds(-100.0, -100.0, 100.0) == -100.0
    assert Utility.bounds(100.0, -100.0, 100.0) == 100.0

    assert Utility.bounds(101.0, -100.0, 100.0) == 100.0
    assert Utility.bounds(-101.0, -100.0, 100.0) == -100.0
    assert Utility.bounds(999999.0, -100.0, 100.0) == 100.0
    assert Utility.bounds(-999999.0, -100.0, 100.0) == -100.0

    assert Utility.bounds(str(10), str(0), str(100)) == 10
    assert Utility.bounds(str(10), str(-100), str(100)) == 10
    assert Utility.bounds(str(-10), str(-100), str(100)) == -10
    assert Utility.bounds(str(-100), str(-100), str(100)) == -100
    assert Utility.bounds(str(100), str(-100), str(100)) == 100

    assert Utility.bounds(str(101), str(-100), str(100)) == 100
    assert Utility.bounds(str(-101), str(-100), str(100)) == -100
    assert Utility.bounds(str(999999), str(-100), str(100)) == 100
    assert Utility.bounds(str(-999999), str(-100), str(100)) == -100


def test_decimal_bounds():
    assert Utility.decimal_bounds(10, 0, 100) == 10
    assert Utility.decimal_bounds(10, -100, 100) == 10
    assert Utility.decimal_bounds(-10, -100, 100) == -10
    assert Utility.decimal_bounds(-100, -100, 100) == -100
    assert Utility.decimal_bounds(100, -100, 100) == 100

    assert Utility.decimal_bounds(101, -100, 100) == 100
    assert Utility.decimal_bounds(-101, -100, 100) == -100
    assert Utility.decimal_bounds(999999, -100, 100) == 100
    assert Utility.decimal_bounds(-999999, -100, 100) == -100

    assert Utility.decimal_bounds(10.0, 0.0, 100.0) == 10.0
    assert Utility.decimal_bounds(10.0, -100.0, 100.0) == 10.0
    assert Utility.decimal_bounds(-10.0, -100.0, 100.0) == -10.0
    assert Utility.decimal_bounds(-100.0, -100.0, 100.0) == -100.0
    assert Utility.decimal_bounds(100.0, -100.0, 100.0) == 100.0

    assert Utility.decimal_bounds(101.0, -100.0, 100.0) == 100.0
    assert Utility.decimal_bounds(-101.0, -100.0, 100.0) == -100.0
    assert Utility.decimal_bounds(999999.0, -100.0, 100.0) == 100.0
    assert Utility.decimal_bounds(-999999.0, -100.0, 100.0) == -100.0

    assert Utility.decimal_bounds(str(10), str(0), str(100)) == 10
    assert Utility.decimal_bounds(str(10), str(-100), str(100)) == 10
    assert Utility.decimal_bounds(str(-10), str(-100), str(100)) == -10
    assert Utility.decimal_bounds(str(-100), str(-100), str(100)) == -100
    assert Utility.decimal_bounds(str(100), str(-100), str(100)) == 100

    assert Utility.decimal_bounds(str(101), str(-100), str(100)) == 100
    assert Utility.decimal_bounds(str(-101), str(-100), str(100)) == -100
    assert Utility.decimal_bounds(str(999999), str(-100), str(100)) == 100
    assert Utility.decimal_bounds(str(-999999), str(-100), str(100)) == -100


def test_flatten():
    flattened = Utility.flatten_string(["something", "1", ["A", "B"], "2", "else", 99, [99]])

    assert flattened == "something/1/A/B/2/else/99/99"


def test_flatten_tuple():
    flattened = Utility.flatten_string(("something", "1", ["A", "B"], "2", "else", 99, [99]))

    assert flattened == "something/1/A/B/2/else/99/99"
