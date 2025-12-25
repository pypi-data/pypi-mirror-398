from typing import Any, Tuple

from pydantic import BaseModel, Field

from .base import DEFAULT_PYDANTIC_MODEL_CONFIG


class EchartsConfig(BaseModel):
    option: dict = Field(default_factory=dict)
    attrs: dict = Field(default_factory=dict)

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG

    def add_class(self, *class_list: str):
        self.attrs.setdefault("class", []).extend(class_list)
        return self

    def add_css_style(self, *pairs: Tuple[str, Any]):
        self.attrs.setdefault("style", {}).update({k: v for k, v in pairs})
        return self
