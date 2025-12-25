__doc__ = """
字典工具类
"""

from typing import Any, Callable, Dict, Iterable, Tuple, Union

cn_en_dict = dict(
    半径="radius",
)


def unify_key_name(input: dict, mappings: dict = cn_en_dict) -> dict:
    """
    将字典的键名按照字典中的映射规则进行统一转换
    Args:
        input (dict): 输入的字典，键名可能是中文或其他形式。
        mappings (dict): 键名映射规则，键为原始键名，值为目标键名。
    """
    output = dict()
    for k, v in input.items():
        new_key = mappings.get(k, k)
        if new_key in output:
            raise ValueError(f"Duplicate key found: {new_key} in input dictionary.")
        output[new_key] = v
    return output


def remove_key_not_in(dc: dict, keys: Iterable[Any], delete_value: bool = False):
    """
    移除不在指定范围内的key

    Args:
        delete_value: 是否同时del value
    """
    for key in list(dc.keys()):
        if key not in keys:
            v = dc.pop(key, None)
            if delete_value and v is not None:
                del v


def get_the_first_existent_key(obj: dict, *keys, default=None) -> Tuple[Any, Any]:
    """
    获取第一个存在的key的值

    Args:
        obj (dict): 输入的字典，键名可能是中文或其他形式。
        keys (Iterable[Any]): 要查找的键名列表。
        default (Any, optional): 如果没有找到任何键，返回的默认值。默认值为None。

    Returns:
        (Tuple[Any, Any]): 第一个存在的键值对，键为存在的键名，值为对应的值。如果没有找到任何键，返回(None, default)。
    """
    for key in keys:
        if key in obj:
            return key, obj[key]
    return None, default


from collections import Counter


def compare_counter_progress(progress: Counter, target: Counter) -> int:
    """
    比较计数器的进度
    主要是兼容低版本，高版本的Counter可以直接比较
    """
    p_keys = set(progress.keys())
    t_keys = set(target.keys())
    assert p_keys.issubset(t_keys), "progress must be a subset of target"
    dk = len(p_keys) - len(target.keys())
    if dk != 0:
        return dk
    dvs = []
    for k in p_keys:
        v1 = progress.get(k)
        v2 = target.get(k)
        dv = v1 - v2 if v1 != v2 else 0
        if dv > 0:
            dv = 1
        elif dv < 0:
            dv = -1
        if dv != 0:
            dvs.append(dv)

    if len(dvs) == 0:
        return 0

    dv_sum = sum(dvs)

    # 全部相等
    if dv_sum == 0:
        return 0
    # 全部大
    elif dv_sum == len(dvs):
        return 1
    # 全部小
    elif dv_sum == -len(dvs):
        return -1
    # 有的大有的小就是小
    return -1
