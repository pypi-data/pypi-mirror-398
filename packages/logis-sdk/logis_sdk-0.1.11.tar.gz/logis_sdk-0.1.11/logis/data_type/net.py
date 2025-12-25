import logging
from typing import Generic, Literal, Optional, Union

import requests
from pydantic import BaseModel

from .base import DEFAULT_PYDANTIC_MODEL_CONFIG, T


class ApiError(BaseModel):
    code: int = -1
    message: str = "错误"


class ApiResponse(BaseModel, Generic[T]):

    success: bool
    data: Optional[T] = None
    error: Union[ApiError, Optional[str]] = None
    message: Optional[str] = None
    extra: Optional[dict] = None

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG

    @staticmethod
    def positive(data: T, **kwargs):
        return ApiResponse[T](success=True, data=data, **kwargs)

    @staticmethod
    def negative(error: Union[ApiError, str], **kwargs):
        return ApiResponse[None](success=False, error=error, **kwargs)

    @staticmethod
    def from_http_response(
        r: requests.Response, content_type: Optional[Literal["json", "text"]] = None
    ):
        ct = content_type or r.headers.get("content-type") or ""
        try:
            data = r.json() if "json" in ct else r.text
        except Exception as e:
            logging.warning("解析响应体失败: %s", e)
            data = r.text
        return (
            ApiResponse.positive(data)
            if r.status_code == 200
            else ApiResponse.negative(
                ApiError(code=r.status_code, message=str(r.status_code))
            )
        )
