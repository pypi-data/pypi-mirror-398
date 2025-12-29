""" Inspired by termcolor: https://github.com/termcolor/termcolor """

import re

from typing import Literal, Iterable, Union

FONT_TYPE = Literal[
    "bold",
    "dark",
    "underline",
    "blink",
    "reverse",
    "concealed",
]

BG_COLOR_TYPE = Literal[
    "bg_black",
    "bg_grey",
    "bg_red",
    "bg_green",
    "bg_yellow",
    "bg_blue",
    "bg_magenta",
    "bg_cyan",
    "bg_light_grey",
    "bg_dark_grey",
    "bg_light_red",
    "bg_light_green",
    "bg_light_yellow",
    "bg_light_blue",
    "bg_light_magenta",
    "bg_light_cyan",
    "bg_white",
]

COLOR_TYPE = Literal[
    "black",
    "grey",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "light_grey",
    "dark_grey",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "white",
]

FONTS: dict[FONT_TYPE, int] = {
    "bold": 1,
    "dark": 2,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "concealed": 8,
}

BG_COLORS: dict[BG_COLOR_TYPE, int] = {
    "bg_black": 40,
    "bg_grey": 40,
    "bg_red": 41,
    "bg_green": 42,
    "bg_yellow": 43,
    "bg_blue": 44,
    "bg_magenta": 45,
    "bg_cyan": 46,
    "bg_light_grey": 47,
    "bg_dark_grey": 100,
    "bg_light_red": 101,
    "bg_light_green": 102,
    "bg_light_yellow": 103,
    "bg_light_blue": 104,
    "bg_light_magenta": 105,
    "bg_light_cyan": 106,
    "bg_white": 107,
}

COLORS: dict[COLOR_TYPE, int] = {
    "black": 30,
    "grey": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "light_grey": 37,
    "dark_grey": 90,
    "light_red": 91,
    "light_green": 92,
    "light_yellow": 93,
    "light_blue": 94,
    "light_magenta": 95,
    "light_cyan": 96,
    "white": 97,
}


COLOR_SET = "\033[%sm%s"
COLOR_RESET = "\033[0m"
RE_COLORED = (
    r"(?P<colored_text>\033\[(?P<color_ints>\d+(\;\d+)*)m(?P<text>[^\033]*)\033\[0m)"
)


def color_text_with_ints(text: str, color_ints: list[int]) -> str:
    if color_ints:
        color_ints_str = ";".join(map(str, color_ints))
        res = f"\033[{color_ints_str}m{text}\033[0m"
    else:
        res = text
    return res


def colored(
    text: str,
    color: COLOR_TYPE = None,
    bg_color: BG_COLOR_TYPE = None,
    fonts: Union[FONT_TYPE, Iterable[FONT_TYPE]] = None,
) -> str:
    text = str(text)

    color_ints = []
    if color:
        color_ints.append(COLORS[color])
    if bg_color:
        color_ints.append(BG_COLORS[bg_color])
    if fonts:
        if isinstance(fonts, str):
            color_ints.append(FONTS[fonts])
        else:
            color_ints.extend([FONTS[font] for font in fonts])

    # handle nested colored text
    matches = re.finditer(RE_COLORED, text)
    if matches:
        res = ""
        prev_end = 0
        for match in matches:
            start = match.start()
            end = match.end()
            if start > prev_end:
                res += color_text_with_ints(text[prev_end:start], color_ints)
            res += match.group("colored_text")
            prev_end = end
        if prev_end < len(text):
            res += color_text_with_ints(text[prev_end:], color_ints)
    else:
        res = color_text_with_ints(text, color_ints)

    return res


def decolored(text: str) -> str:
    if not isinstance(text, str):
        return text
    matches = re.finditer(RE_COLORED, text)
    if matches:
        res = ""
        prev_end = 0
        for match in matches:
            start = match.start()
            end = match.end()
            if start > prev_end:
                res += text[prev_end:start]
            res += match.group("text")
            prev_end = end
        if prev_end < len(text):
            res += text[prev_end:]
    else:
        res = text

    return res
