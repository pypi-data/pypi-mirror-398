from itertools import count
from numbers import Number
from typing import Dict, Generic, Optional, Tuple, TypeVar

from logis.data_type import Number, TuplePoint

from ._math import compute

T = TypeVar("T", bound=Number)


class GenericPoint(Generic[T]):

    @classmethod
    def model_validate(cls, v: Dict[str, T]):
        if v is None:
            return None
        if isinstance(v, dict):
            return cls(**v)
        raise ValueError("only dict type is supported")

    def __init__(
        self,
        x: Optional[T] = None,
        y: Optional[T] = None,
        z: Optional[T] = None,
        *args,
        precision: Optional[int] = None,
        **kwargs,
    ):
        """
        Args:
            x (T | None, optional): X coordinate. Defaults to None.
            y (T | None, optional): Y coordinate. Defaults to None.
            z (T | None, optional): Z coordinate. Defaults to None.
            precision (int | None, optional): Precision. Defaults to None.
        """
        self.precision = precision
        if precision is not None:
            x = round(x, precision) if x is not None else x
            y = round(y, precision) if y is not None else y
            z = round(z, precision) if z is not None else z
        self.x, self.y, self.z = x, y, z

    @classmethod
    def from_tuple(
        cls, tp: Tuple[T], precision: Optional[int] = None, **kwargs
    ) -> "GenericPoint[T]":
        return cls(*tp, precision=precision, **kwargs)

    def __add__(self, other: "GenericPoint[T]") -> "GenericPoint[T]":
        assert self.precision == other.precision, "Precision must be the same."
        x = compute("add", self.x, other.x)
        y = compute("add", self.y, other.y)
        z = compute("add", self.z, other.z)
        return self.__class__(x, y, z, precision=self.precision)

    def __sub__(self, other: "GenericPoint[T]") -> "GenericPoint[T]":
        assert self.precision == other.precision, "Precision must be the same."
        x = compute("subtract", self.x, other.x)
        y = compute("subtract", self.y, other.y)
        z = compute("subtract", self.z, other.z)
        return self.__class__(x, y, z, precision=self.precision)

    def __mul__(self, other: Number) -> "GenericPoint[T]":
        assert other is not None, "Multiplier must not be None."
        x = compute("multiply", self.x, other) if self.x is not None else None
        y = compute("multiply", self.y, other) if self.y is not None else None
        z = compute("multiply", self.z, other) if self.z is not None else None
        return self.__class__(x, y, z, precision=self.precision)

    def __truediv__(self, other: Number) -> "GenericPoint[T]":
        assert other is not None, "Divisor must not be None."
        x = compute("divide", self.x, other) if self.x is not None else None
        y = compute("divide", self.y, other) if self.y is not None else None
        z = compute("divide", self.z, other) if self.z is not None else None
        return self.__class__(x, y, z, precision=self.precision)

    def __eq__(self, value):
        if not isinstance(value, self.__class__):
            return False
        return (
            self.x == value.x
            and self.y == value.y
            and self.z == value.z
            and self.precision == value.precision
        )


class Point(GenericPoint[float]):
    """
    此类不通用，历史遗留，不建议使用，如有需要建议使用GenericPoint
    支持x,y,z三维坐标点，也可当作二维坐标使用
    TODO: 处理单位
    """

    __counter = count(0, step=1)

    @classmethod
    def try_parse(cls, dc: dict, precision: int = 3, **kwargs) -> "Point":
        """
        尝试读取X、Y、Z坐标，返回一个Point对象
        """
        if not isinstance(dc, dict):
            raise ValueError("Expected a dictionary for Point parsing.")
        xyz = [dc.get(k, None) for k in ("X", "Y", "Z")]
        return Point(xyz, precision=precision, **kwargs)

    @classmethod
    def from_tuple(cls, args: Tuple[Number], precision: int = 3, **kwargs):
        """
        从元组创建点
        """
        return cls(args, precision=precision, **kwargs)

    @classmethod
    def of(
        cls,
        x: Optional[Number] = None,
        y: Optional[Number] = None,
        z: Optional[Number] = None,
        precision: int = 3,
        **kwargs,
    ) -> "Point":
        p = Point(x, y, z, precision=precision, **kwargs)
        return p

    def __init__(self, *args, precision=3, **kwargs):
        """
        支持[x,y]、x,y、[x,y,z]、x,y,z传参赋值
        默认x=y=z=0

        TODO: 不应该自动转float、不应该自动保留两位小数
        """
        self._id = next(self.__counter)
        self.unit: Optional[str] = kwargs.get("unit", None)
        x: Optional[Number] = kwargs.get("x", None)
        y: Optional[Number] = kwargs.get("y", None)
        z: Optional[Number] = kwargs.get("z", None)
        if len(args) == 1:
            x = round(float(args[0][0]), precision) if args[0][0] is not None else None
            y = round(float(args[0][1]), precision) if args[0][1] is not None else None
            if len(args[0]) > 2 and (z := args[0][2]) is not None:
                z = round(float(z), precision)

        elif len(args) >= 2:
            x = round(float(args[0]), precision) if args[0] is not None else None
            y = round(float(args[1]), precision) if args[1] is not None else None
            if len(args) > 2 and (z := args[2]) is not None:
                z = round(float(z), precision)

        # 调试过程中发现z有时候是None有时候是0，因此这里统一给了默认值
        # 实际上应该外层规范
        x = x if x is not None else 0
        y = y if y is not None else 0
        z = z if z is not None else 0

        kwargs.update(x=x, y=y, z=z, precision=precision)

        super().__init__(**kwargs)

    def __repr__(self):
        return f"Point({self.x}, {self.y}, {self.z})"

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __lt__(self, other):
        """
        FIXME: 考虑z
        """
        if isinstance(other, Point):
            # TODO: 只要任何一个大于就行？
            return (self.x, self.y) < (other.x, other.y)
        return NotImplemented

    def __sub__(self, other: "Point"):
        def sub(a: Number, b: Number):
            if a is None and b is None:
                return None
            a = a or 0
            b = b or 0
            return a - b

        assert self.unit == other.unit, "unit must be same"
        return Point.of(
            x=sub(self.x, other.x),
            y=sub(self.y, other.y),
            z=sub(self.z, other.z),
            unit=self.unit,
        )

    def to_tuple(self) -> TuplePoint:
        return (
            self.x,
            self.y,
            self.z,
        )

    def __str__(self):
        return f"Point(id={self._id},x={self.x},y={self.y},z={self.z})"


if __name__ == "__main__":
    pass
