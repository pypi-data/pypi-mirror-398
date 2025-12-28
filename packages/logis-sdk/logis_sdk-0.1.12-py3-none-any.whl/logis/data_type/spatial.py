from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator

from logis.data_type.base import DEFAULT_PYDANTIC_MODEL_CONFIG
from logis.data_type.point import Point
from logis.data_type.unitable import Length, QuantifiedValue


class SpatialProps(BaseModel):
    """
    空间属性
    """

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG

    width: Optional[Length] = Field(
        default=None,
        validation_alias=AliasChoices("单元格宽度", "width"),
    )
    height: Optional[Length] = Field(
        default=None, validation_alias=AliasChoices("层高", "height")
    )
    depth: Optional[Length] = Field(
        validation_alias=AliasChoices("货架深度", "托盘货架深度"), default=None
    )
    rotation: Optional[QuantifiedValue] = Field(
        validation_alias=AliasChoices("旋转", "rotate"), default=None
    )
    center_point: Optional[Point] = None

    @field_validator("center_point", mode="before")
    def center_point_validator_before(cls, v: Optional[Point]):
        if v is None:
            return None
        if isinstance(v, Point):
            return v
        if isinstance(v, dict):
            return Point.model_validate(v)
        elif isinstance(v, (tuple, list)):
            return Point.from_tuple(v)
        raise ValueError("only dict, tuple, list type is supported")
