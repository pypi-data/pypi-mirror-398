import pytest

from logis.iface import Storable


class MyBox(Storable):

    def store(self, item, **config):
        print(item, config)
        return True


class MyBox2:
    def store(self, item, a=2, **config):
        print(item, config)
        return True

    def retrieve(self, item, **config):
        print(item, config)
        return True

    def pre_store(self, item, **config):

        print(item, config)
        return True

    def pre_retrieve(self, item, **config):
        print(item, config)
        return True


class MyBox3:
    def store(self, *args, **config):
        print(args, config)
        return True

    def retrieve(self, *args, **config):
        print(args, config)
        return True

    def pre_store(self, **config):
        pass

    def pre_retrieve(self, **config):
        pass


def test_issubclass():
    assert issubclass(MyBox, Storable)
    x = MyBox()
    assert x.store("hello", xxx=1)

    assert issubclass(MyBox2, Storable)

    assert isinstance(MyBox2(), Storable)
    assert isinstance(MyBox3(), Storable)
