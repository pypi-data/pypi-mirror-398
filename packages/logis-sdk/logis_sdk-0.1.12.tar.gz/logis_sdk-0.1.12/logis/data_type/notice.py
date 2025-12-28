from typing import Literal, Optional, Union

from pydantic import BaseModel


class Notification(BaseModel):
    title: Optional[str] = None
    duration: Union[float, int] = -1
    content: Optional[str] = None
    closable: bool = True
    type: Literal["info", "success", "warning", "error"] = "info"
