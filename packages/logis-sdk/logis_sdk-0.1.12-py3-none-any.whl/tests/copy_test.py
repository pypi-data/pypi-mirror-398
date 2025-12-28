from copy import copy, deepcopy


class MyInnerClass:
    def __init__(self):
        self.inner_name = "who"


class MyClass:

    def __init__(self):
        self.name: str = None
        self.age = 10
        self.inner = MyInnerClass()

    def yield_method(self):
        yield 1


def test_copy():
    obj = MyClass()
    obj1 = copy(obj)
    obj.name = 11
    assert obj1.name != obj.name
    assert obj1.inner is obj.inner


def test_deepcopy():
    obj = MyClass()
    obj2 = deepcopy(obj)
    obj.age = 1000
    assert obj.name == obj2.name
    assert obj.age != obj2.age
    assert obj.inner is not obj2.inner
