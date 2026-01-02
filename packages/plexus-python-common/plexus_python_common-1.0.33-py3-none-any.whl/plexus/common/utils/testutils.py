import uuid as py_uuid

import textcase
from iker.common.utils.jsonutils import JsonType
from iker.common.utils.jsonutils import json_difference, json_reformat

from plexus.common.utils.datautils import compute_vin_code_check_digit

__all__ = [
    "generate_dummy_uuid_str",
    "generate_dummy_uuid",
    "generate_dummy_vin_code",
    "case_insensitive_json_compare",
]


def generate_dummy_uuid_str(*nums: int) -> str:
    if len(nums) > 8:
        raise ValueError("a maximum of 8 integers can be provided")
    if not all(0 <= num <= 0xFFFF for num in nums):
        raise ValueError("all integers must be in the range 0 to 65535 (0xFFFF)")
    i0, i1, i2, i3, i4, i5, i6, i7 = list(nums) + [0] * (8 - len(nums))
    return f"{i0:04x}{i1:04x}-{i2:04x}-{i3:04x}-{i4:04x}-{i5:04x}{i6:04x}{i7:04x}"


def generate_dummy_uuid(*nums: int) -> py_uuid.UUID:
    return py_uuid.UUID(generate_dummy_uuid_str(*nums))


def generate_dummy_vin_code(*nums: int) -> str:
    if len(nums) > 4:
        raise ValueError("a maximum of 4 integers can be provided")
    if not all(0 <= num <= 9999 for num in nums):
        raise ValueError("all integers must be in the range 0 to 9999")
    i0, i1, i2, i3 = list(nums) + [0] * (4 - len(nums))
    unchecked_vin_code = f"{i0:04d}{i1:04d}0{i2:04d}{i3:04d}"
    check_digit = compute_vin_code_check_digit(unchecked_vin_code)
    return unchecked_vin_code[:8] + check_digit + unchecked_vin_code[-8:]


def case_insensitive_json_compare(a: JsonType, b: JsonType, *, print_diff_messages: bool = True) -> bool:
    identical = True
    for node_path, diff_message in json_difference(json_reformat(a, key_formatter=textcase.camel),
                                                   json_reformat(b, key_formatter=textcase.camel),
                                                   []):
        if print_diff_messages:
            print(node_path, diff_message)
        identical = False
    return identical
