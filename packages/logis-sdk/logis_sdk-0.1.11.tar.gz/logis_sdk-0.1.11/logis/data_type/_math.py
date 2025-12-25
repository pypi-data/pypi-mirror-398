import math
from numbers import Number
from typing import Literal


def compute(
    operation: Literal["add", "subtract", "multiply", "divide"], *nums: Number
) -> Number:
    if not nums:
        raise ValueError("At least one number is required.")

    if len(nums) == 1:
        return nums[0]

    all_none = all(num is None for num in nums)
    if all_none:
        return None

    all_numbers = all(isinstance(num, Number) for num in nums)
    if not all_numbers:
        raise ValueError("All arguments must be numbers.")

    if operation == "add":
        return sum(nums)
    elif operation == "subtract":
        return nums[0] - sum(nums[1:])
    elif operation == "multiply":
        return math.prod(nums)
    elif operation == "divide":
        return nums[0] / math.prod(nums[1:])
    else:
        raise ValueError(f"Unknown operation: {operation}")
