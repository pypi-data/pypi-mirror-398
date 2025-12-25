import pandas as pd


def test_cascade():
    # 外层数据
    outer_df = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})

    # 内层数据（通过 id 与外层关联）
    inner_df = pd.DataFrame(
        {
            "id": [1, 1, 2, 2],  # 关联键
            "param": ["x", "y", "x", "y"],
            "value": [10, 20, 30, 40],
        }
    )

    # 通过 merge 关联内外层数据
    a = pd.merge(outer_df, inner_df, on="id")
    print(a)

    b = pd.json_normalize(
        data={
            "id": [1, 2],
            "name": ["A", "B"],
            "params": [
                {"key": "x", "value": 10},
                {"key": "y", "value": 20},
            ],
            "metadata": {
                "created_at": "2023-01-01",
                "updated_at": "2023-01-02",
            },
        }
    )
    print(b)
