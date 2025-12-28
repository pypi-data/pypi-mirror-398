import logging
from typing import Any, Set, Type, Union

from pydantic import AliasChoices, AliasPath, BaseModel
from pydantic import Field as PydanticField
from sqlmodel import Field as SqlModelField


def collect_field_aliases(field: Union[PydanticField, SqlModelField]) -> Set[str]:
    """
    获取字段的别名。
    """

    def _try_collect(field: Any):
        x = getattr(field, "alias", None)
        y = getattr(field, "validation_alias", None)
        z = getattr(field, "serialization_alias", None)

        def _pick_alias(alias: Any):
            tmps = set()
            if isinstance(alias, str):
                tmps.add(alias)
            elif isinstance(alias, AliasChoices):
                for choice in alias.choices:
                    tmps.update(_pick_alias(choice))
            elif isinstance(alias, AliasPath):
                tmps.update(alias.convert_to_aliases())
            else:
                logging.warning(f"Unknown alias type: {type(alias)}")
            return tmps

        aliases = set()
        for tmp in filter(lambda x: x is not None, [x, y, z]):
            aliases |= _pick_alias(tmp)
        return aliases

    return set(_try_collect(field))


def rename_keys_by_field_name(m: Type[BaseModel], data: dict):
    """
    重命名数据字典的键，使它们与Pydantic模型的字段名称匹配。
    注意：
        1. 如果data中同时包含字段名和别名，字段名会被别名覆盖
        2. 如果有多个别名，以最后一个别名为准
    """
    for name, f in m.model_fields.items():
        aliases = collect_field_aliases(f)
        for alias in aliases:
            if alias in data:
                data[name] = data.pop(alias)
    return data


def model_validate(m: Type[BaseModel], data: dict):
    """
    sqlmodel的model_validate方法特性落后于pydantic，为了解决alias问题，产生了此方法
    """
    return m.model_validate(rename_keys_by_field_name(m, data))
