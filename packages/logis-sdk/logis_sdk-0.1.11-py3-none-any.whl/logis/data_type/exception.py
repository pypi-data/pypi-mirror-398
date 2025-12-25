from typing import Any, Callable

ErrorHandler = Callable[[Exception], Any]


class MyBaseException(Exception):
    """
    基础异常类，所有自定义异常都应该继承自这个类
    """

    def __init__(self, *args, **attrs):
        super().__init__(*args)
        for k, v in attrs.items():
            hasattr(self, k) or setattr(self, k, v)


class UserFacingException(MyBaseException):
    """
    用户面向的异常类，用于在前端展示异常信息
    """

    def __init__(self, *args, **attrs):
        super().__init__(*args, **attrs)
