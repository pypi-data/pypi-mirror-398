from logis.util import set_attr_if, set_attr_if_has
from logis.util.dict_util import remove_key_not_in
from logis.util.num_util import split_integer


def test_split_integer():
    assert list(split_integer(10, 3, order="asc", mode="limit_parts")) == [3, 3, 4]
    assert list(split_integer(10, 3, order="desc", mode="limit_parts")) == [4, 3, 3]

    assert list(split_integer(10, 3, order="desc", mode="limit_per_part")) == [
        3,
        3,
        3,
        1,
    ]
    assert list(split_integer(10, 3, order="asc", mode="limit_per_part")) == [
        1,
        3,
        3,
        3,
    ]


def test_remove_key_not_in():
    dc = dict(a=1, b=2, c=3, d=4)
    remove_key_not_in(dc, dict(d=5, e=6).keys())
    assert list(dc.keys()) == ["d"]


class Animal:
    def __init__(self):
        self.name = None
        self.age = None


def test_set_attr_if():

    a = Animal()
    set_attr_if_has(
        a,
        dict(name="dog", age=10, gender=1),
    )

    assert a.name == "dog"
    assert a.age == 10
    assert getattr(a, "gender", None) is None

    set_attr_if(a, dict(gender=1), lambda *args: True)

    assert hasattr(a, "gender") and getattr(a, "gender") == 1
