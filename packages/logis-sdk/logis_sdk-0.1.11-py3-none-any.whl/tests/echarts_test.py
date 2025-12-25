import json

from pyecharts.charts import Bar


def test_bar():
    bar = Bar()
    bar.add_xaxis(["A", "B", "C", "D", "E"])
    bar.add_yaxis("Series 1", [1, 2, 3, 4, 5])

    x = bar.dump_options()
    y = json.loads(x)

    x = bar.dump_options_with_quotes()
    y = json.loads(x)
