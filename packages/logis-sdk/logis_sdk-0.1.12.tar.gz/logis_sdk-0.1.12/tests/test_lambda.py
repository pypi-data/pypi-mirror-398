from logis.util.lambda_util import generate_all, invoke


def test_generator_result():

    def c():
        return None

    def a():
        yield 1
        yield 2
        yield 3
        return 4

    def b():
        yield from a()
        yield 5
        yield 6
        return 8

    result = generate_all(b())
    assert result.return_value == 8
    assert result.yield_values == [1, 2, 3, 5, 6]

    result = generate_all(a())
    assert result.return_value == 4
    assert result.yield_values == [1, 2, 3]

    result = invoke(c)
    assert result.return_value is None
    assert result.yield_values == []


def test_invoke():
    def a():
        return 1

    async def b():
        return 2

    result = invoke(a)
    assert result.return_value == 1
    assert result.yield_values == []

    result = invoke(b)
    assert result.return_value == 2
    assert result.yield_values == []
