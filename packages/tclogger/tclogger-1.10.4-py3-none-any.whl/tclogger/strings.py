from typing import Literal
from .maths import chars_len


def chars_slice(
    text: str,
    beg: int = None,
    end: int = None,
    use_chars_len: bool = True,
    fill_char: str = " ",
    align: Literal["l", "r"] = None,
) -> str:
    """Slice string with beg and end, considering chars length."""
    if beg is None:
        beg = 0
    if end is None:
        end = len(text)

    if not use_chars_len:
        return text[beg:end]

    if beg < 0:
        beg = len(text) + beg
    if end < 0:
        end = len(text) + end + 1

    res_beg_idx = None
    res_end_idx = None
    fill_left = ""
    fill_right = ""
    res = ""
    beg_idx = 0
    end_idx = 0
    if not isinstance(text, str):
        if isinstance(text, (int, float)):
            align = "r"
        text = str(text)
    for ch in text:
        end_idx = beg_idx + chars_len(ch)
        if beg_idx >= beg and end_idx <= end:
            res += ch
            if res_beg_idx is None:
                res_beg_idx = beg_idx
                fill_left = fill_char * (beg_idx - beg)
        if end_idx >= end:
            if res_end_idx is None:
                res_end_idx = end_idx
                fill_right = fill_char * (end_idx - end)
            break
        beg_idx = end_idx
    if res_end_idx is None:
        res_end_idx = end_idx
        fill_right = fill_char * (end - end_idx)
    if not align:
        res = fill_left + res + fill_right
    elif align == "l":
        res = res + fill_left + fill_right
    else:
        res = fill_left + fill_right + res
    return res
