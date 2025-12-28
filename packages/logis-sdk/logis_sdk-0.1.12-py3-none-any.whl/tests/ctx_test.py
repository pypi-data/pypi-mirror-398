from logis.ctx import Context


def test_counter():
    assert next(Context.counter()) == 0
    assert next(Context.counter()) == 1
    assert next(Context.counter(id="1")) == 0
    assert next(Context.counter(id="1")) == 1
    assert next(Context.counter(id="2", start=1)) == 1
    assert next(Context.counter(id="3", start=1, step=2)) == 1
    assert next(Context.counter(id="3")) == 3
