import pytest


def test_compare_counter_progress():
    from collections import Counter

    from logis.util.dict_util import compare_counter_progress

    progress = Counter(a=1, b=2, c=3)
    target = Counter(a=1, b=2, c=3, d=4)
    assert compare_counter_progress(progress, target) < 0
    progress["c"] = 100

    assert compare_counter_progress(progress, target) < 0

    progress["d"] = 100
    assert compare_counter_progress(progress, target) > 0
