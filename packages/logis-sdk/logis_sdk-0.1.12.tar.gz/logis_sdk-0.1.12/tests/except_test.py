import pytest

from logis.data_type.exception import MyBaseException


def test_try_except():
    a = 0
    with pytest.raises(ZeroDivisionError):
        try:
            1 / 0
        finally:
            a = 1

    assert a == 1


def test_exception():
    e = Exception("test", "xxxx")

    assert e.args == ("test", "xxxx")

    assert str(e) == "('test', 'xxxx')"


def test_my_base_exception():
    e = MyBaseException("test", "xxxx", args=(1, 2, 3), v=1)

    assert e.v == 1
    assert e.args == ("test", "xxxx")

    assert str(e) == "('test', 'xxxx')"
