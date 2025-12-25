from typing import Optional

from pydantic import AliasChoices, ConfigDict
from sqlmodel import Field, SQLModel

from logis.util.pydantic_util import collect_field_aliases


class TestTableModel(SQLModel, table=False):
    model_config = ConfigDict(strict=False, coerce_numbers_to_str=True)
    name: str = Field(
        "",
        alias="名字",
        schema_extra=dict(
            validation_alias=AliasChoices("userName", "name"), strict=False
        ),
    )

    age: Optional[int] = Field(default=None)


def test_collect_alias():
    name_field = TestTableModel.model_fields["name"]
    aliases = collect_field_aliases(name_field)

    assert not aliases.difference(["名字", "userName", "name"])


def test_implict_type_cast():
    m = TestTableModel.model_validate(dict(age="10", name=100))
    assert m.age == 10
    assert m.name == "100"
