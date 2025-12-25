import pytest

from logis.util.lambda_util import invoke


class A:
    @property
    def id(self) -> int:
        pass


class B(A):
    def __init__(self):
        self.id = 10


def test_id():
    with pytest.raises(AttributeError):
        b = B()
        assert b.id == 10


def test_mro():
    class A:
        def __init__(self, **kwargs):
            print("->A")
            super().__init__(**kwargs)
            print("->A end")

        def method(self):
            return "A"

    class B(A):
        def __init__(self, **kwargs):
            print("->B")
            super().__init__(**kwargs)
            print("->B end")

    class C(A):
        def __init__(self, **kwargs):
            print("->C")
            super().__init__(**kwargs)
            print("->C end")

        def method(self):
            return "C"

    class D(B, C):
        def __init__(self, **kwargs):
            print("->D")
            super().__init__(**kwargs)
            print("->D end")

    assert D().method() == "C"
    assert D.mro() == [D, B, C, A, object]


def test_atexit():
    from atexit import register

    async def hello(name: str):
        return print("hello " + name)

    def handler():
        print("atexit111")

    register(handler)

    class MyClass:
        def __init__(self):
            register(lambda: invoke(hello, "andy"))

    MyClass()
