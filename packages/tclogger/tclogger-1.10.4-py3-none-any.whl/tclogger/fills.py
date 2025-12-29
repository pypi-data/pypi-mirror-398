import shutil

from typing import Union, Literal

from .maths import chars_len
from .colors import colored, decolored, COLOR_TYPE


def fill_to_len(filler: str, length: int) -> str:
    filler_len = chars_len(filler)
    complete_fill_count = length // filler_len
    remaining_fill_len = length % filler_len
    filled_str = filler * complete_fill_count + filler[:remaining_fill_len]
    return filled_str


def add_fills(
    text: str = "",
    filler: str = "=",
    fill_side: Literal["left", "right", "both"] = "both",
    is_text_colored: bool = False,
    fill_color: COLOR_TYPE = None,
    total_width: int = None,
):
    if not total_width:
        total_width = shutil.get_terminal_size().columns
    if not text:
        filled_str = colored(fill_to_len(filler, total_width), color=fill_color)
        return filled_str

    text = text.strip()
    if is_text_colored:
        text_width = chars_len(decolored(text))
    else:
        text_width = chars_len(text)
    if text_width >= total_width:
        return text

    if fill_side[0].lower() == "b":
        leading_fill_str = (
            fill_to_len(filler, (total_width - text_width) // 2 - 1) + " "
        )
        trailing_fill_str = " " + fill_to_len(
            filler, total_width - text_width - chars_len(leading_fill_str) - 1
        )
    elif fill_side[0].lower() == "l":
        leading_fill_str = fill_to_len(filler, total_width - text_width - 1) + " "
        trailing_fill_str = ""
    elif fill_side[0].lower() == "r":
        leading_fill_str = ""
        trailing_fill_str = " " + fill_to_len(filler, total_width - text_width - 1)
    else:
        raise ValueError("Invalid fill_side")

    if fill_color:
        leading_fill_str = colored(leading_fill_str, color=fill_color)
        trailing_fill_str = colored(trailing_fill_str, color=fill_color)

    filled_str = f"{leading_fill_str}{text}{trailing_fill_str}"
    return filled_str
