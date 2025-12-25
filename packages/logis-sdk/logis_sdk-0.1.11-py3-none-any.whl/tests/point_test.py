from decimal import Decimal

import pytest

from logis.data_type import GenericPoint, Point


def test_point():
    p1 = Point(1, 2, 0)
    p2 = Point(1, 2, 3)
    p3 = Point.from_tuple([1, 2, 3])
    p4 = Point.from_tuple([10, 1, 0])
    for p in [p1, p2, p3, p4]:
        print(p)

    assert p1 - p2 == Point(0, 0, -3)
    assert p3 - p4 == Point(-9, 1, 3)
    assert Point() - Point() == Point()


def test_generic_point():
    p = GenericPoint[float](1.23456, 2.34567, 3.45678, precision=4)
    assert p.x == 1.2346
    assert p.y == 2.3457
    assert p.z == 3.4568

    p = GenericPoint[Decimal](
        Decimal("1.23456"), Decimal("2.34567"), Decimal("3.45678"), precision=4
    )

    assert p.x == Decimal("1.2346")
    assert p.y == Decimal("2.3457")
    assert p.z == Decimal("3.4568")


def test_compute():
    p1 = GenericPoint[int].from_tuple((1, 2, 3), precision=1)
    p2 = GenericPoint[float](1, 3, 4, precision=1)
    a = p1 + p2
    assert a.x == 2
    assert a.y == 5
    assert a.z == 7

    p3 = GenericPoint[Decimal](
        Decimal("1.14"), Decimal("2.16"), Decimal("3.55"), precision=1
    )
    b = p1 + p3
    assert b.x == Decimal("2.1")
    assert b.y == Decimal("4.2")
    assert b.z == Decimal("6.6")

    c = p2 * 5
    assert c.x == Decimal("5.0")
    assert c.y == Decimal("15.0")
    assert c.z == Decimal("20.0")

    p4 = GenericPoint[int](5, 10)
    d = p4 / 5
    assert d.x == 1
    assert d.y == 2
    assert d.z is None

    p5 = GenericPoint[int](10, 20, 1)
    p6 = GenericPoint[int](10, 10, None)

    with pytest.raises(ValueError):
        p5 / p6
