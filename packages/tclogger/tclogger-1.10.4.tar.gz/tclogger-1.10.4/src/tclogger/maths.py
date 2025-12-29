"""Math utils"""

import math
from typing import Union, Literal


def int_bits(num, base: int = 10):
    """Calc bits of integer with base X"""
    return math.ceil(math.log(num + 1, base))


def chars_len(chars: Union[str, int]) -> int:
    """Calc length of chars"""
    chars = str(chars)
    res = 0
    if isinstance(chars, int):
        chars = str(chars)
    for ch in chars:
        if ord(ch) > 255:
            res += 2
        else:
            res += 1
    return res


def max_key_len(d: dict, offset: int = 0, use_chars_len: bool = True) -> int:
    """Get max string length of dict keys"""
    if not d:
        return 0
    len_func = chars_len if use_chars_len else len
    return max([len_func(str(k)) + offset for k in d.keys()])


def is_str_float(s: str) -> bool:
    return s.replace(".", "", 1).isdigit() and s.count(".") < 2


def to_digits(s: Union[str, int, float], precision: int = None) -> float:
    if isinstance(s, (int, float)):
        return s
    else:  # str
        try:
            return int(s)
        except:
            if precision is None:
                return float(s)
            else:
                return round(float(s), precision)


def get_by_threshold(
    d: Union[dict, list],
    threshold: Union[int, float],
    direction: Literal["upper_bound", "lower_bound"] = "lower_bound",
    target: Literal["key", "value"] = "key",
    is_to_digits: bool = True,
    digits_precision: int = None,
    is_sort: bool = True,
) -> tuple:
    """Get item from dict, which compares on target (key/value) against threshold with direction:
        - threshold as `upper_bound`: get maximum item that is lower than threshold
        - threshold as `lower_bound`: get minimum item that is higher than threshold

    params:
        - d (dict): keys should be int, float, or string (need to convert to float)
        - threshold: numeric threshold to compare against.
        - direction: "upper_bound" or "lower_bound"
        - target: "key" or "value", which to sort and compare against the threshold.

    return:
        - tuple (key, value); if no such entry exists, return (None, None)
    """
    # unify to list of tuples
    if isinstance(d, dict):
        items = list(d.items())
    else:
        items = d
    # unify to number (int/float)
    if is_to_digits:
        if target == "value":
            items = [(k, to_digits(v, digits_precision)) for k, v in items]
        else:
            items = [(to_digits(k, digits_precision), v) for k, v in items]
    # sort, asc, from low to high
    if is_sort:
        if target == "key":
            sorted_items = sorted(items, key=lambda item: item[0])
        else:  # target == "value"
            sorted_items = sorted(items, key=lambda item: item[1])
    # Based on direction, filter the sorted items.
    last_item = (None, None)
    if direction == "upper_bound":
        for item in sorted_items:
            if target == "key":
                if item[0] <= threshold:
                    last_item = item
                else:
                    break
            else:  # target == "value"
                if item[1] <= threshold:
                    last_item = item
                else:
                    break
    else:  # direction == "lower_bound"
        for item in reversed(sorted_items):
            if target == "key":
                if item[0] >= threshold:
                    last_item = item
                else:
                    break
            else:  # target == "value"
                if item[1] >= threshold:
                    last_item = item
                else:
                    break
    return last_item
