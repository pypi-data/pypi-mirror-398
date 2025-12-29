"""Format utils"""

from copy import deepcopy
from typing import Union, Literal

from .colors import colored, decolored
from .maths import max_key_len
from .strings import chars_slice, chars_len


class DictListAligner:
    def __init__(self):
        self.list_item_types = {}

    def get_item_type(self, v: list) -> Union[str, bool, Union[int, float]]:
        if not v:
            return None
        if isinstance(v[0], bool):
            return "bool"
        elif isinstance(v[0], (int, float)):
            return "num"
        elif isinstance(v[0], str):
            return "str"
        else:
            return str(type(v[0]))

    def is_all_items_types_valid(self, lst: list) -> bool:
        for v in lst:
            if not isinstance(v, (bool, int, float, str)):
                return False
        return True

    def extract_same_len_lists(self, d: dict) -> dict[int, dict]:
        dict_lists_by_len: dict[int, dict] = {}
        for k, v in d.items():
            if isinstance(v, list):
                if not self.is_all_items_types_valid(v):
                    continue
                v_len = len(v)
                item_type = self.get_item_type(v)
                ak = (v_len, item_type)
                self.list_item_types[k] = item_type
                if ak not in dict_lists_by_len:
                    dict_lists_by_len[ak] = {}
                dict_lists_by_len[ak][k] = v
        return dict_lists_by_len

    def calc_aligned_widths(
        self, d: dict
    ) -> dict[tuple[int, Union[str, bool, Union[int, float]]], list]:
        aligned_widths_by_len: dict[tuple, list] = {}
        for k, v in d.items():
            if isinstance(v, list):
                if not self.is_all_items_types_valid(v):
                    continue
                list_len = len(v)
                item_type = self.get_item_type(v)
                ak = (list_len, item_type)
                if ak not in aligned_widths_by_len:
                    aligned_widths_by_len[ak] = [0] * list_len
                for i, vv in enumerate(v):
                    if isinstance(vv, str):
                        vv_width = chars_len(decolored(vv))
                    else:
                        vv_width = chars_len(str(vv))
                    aligned_widths_by_len[ak][i] = max(
                        aligned_widths_by_len[ak][i], vv_width
                    )
        return aligned_widths_by_len

    def align_lists_in_dict(self, d: dict, align: Literal["l", "r"] = None) -> None:
        dict_lists_by_len = self.extract_same_len_lists(d)
        aligned_widths_by_len = self.calc_aligned_widths(d)
        for ak, dd in dict_lists_by_len.items():
            list_len, item_type = ak
            aligned_widths = aligned_widths_by_len[ak]
            for k, v in dd.items():
                for i, vv in enumerate(v):
                    v[i] = chars_slice(vv, end=aligned_widths[i], align=align)
                d[k] = v


class DictStringifier:
    def __init__(
        self,
        indent: int = 2,
        max_depth: int = None,
        depth_offset: int = 1,
        align_colon: bool = True,
        align_list: bool = True,
        align_list_side: Literal["l", "r"] = None,
        add_quotes: bool = True,
        is_colored: bool = True,
        use_braces: bool = True,
        key_prefix: str = "",
        brace_colors: list[str] = ["light_blue", "light_cyan", "light_magenta"],
        key_colors: list[str] = ["light_blue", "light_cyan", "light_magenta"],
        value_colors: list[str] = ["white"],
    ):
        self.indent = indent
        self.max_depth = max_depth
        self.depth_offset = depth_offset
        self.align_colon = align_colon
        self.align_list = align_list
        self.align_list_side = align_list_side
        self.add_quotes = add_quotes
        self.is_colored = is_colored
        self.use_braces = use_braces
        self.key_prefix = key_prefix
        self.depth_configs = {}
        self.brace_colors = brace_colors
        self.key_colors = key_colors
        self.value_colors = value_colors

    def get_depth_config(self, depth: int):
        if depth in self.depth_configs:
            return self.depth_configs[depth]

        if isinstance(self.key_colors, str):
            key_color = self.key_colors
        else:
            key_color = self.key_colors[depth % len(self.key_colors)]
        if isinstance(self.value_colors, str):
            value_color = self.value_colors
        else:
            value_color = self.value_colors[depth % len(self.value_colors)]
        if isinstance(self.brace_colors, str):
            brace_color = self.brace_colors
        else:
            brace_color = self.brace_colors[depth % len(self.brace_colors)]

        indent_str = " " * self.indent * (depth + self.depth_offset)
        brace_indent_str = " " * self.indent * depth
        if self.is_colored:
            lb = colored("{", brace_color)
            rb = colored("}", brace_color)
            lk = colored("[", brace_color)
            rk = colored("]", brace_color)
            colon = colored(":", brace_color)
            comma = colored(",", brace_color)
            ellipsis = colored("...", value_color)
        else:
            lb, rb = "{", "}"
            lk, rk = "[", "]"
            colon = ":"
            comma = ","
            ellipsis = "..."

        self.depth_configs[depth] = {
            "key_color": key_color,
            "value_color": value_color,
            "brace_color": brace_color,
            "indent_str": indent_str,
            "brace_indent_str": brace_indent_str,
            "lb": lb,
            "rb": rb,
            "lk": lk,
            "rk": rk,
            "colon": colon,
            "comma": comma,
            "ellipsis": ellipsis,
        }

        return self.depth_configs[depth]

    def dict_to_str(
        self,
        d: Union[dict, list],
        depth: int = 0,
    ) -> tuple[str, str]:
        configs = self.get_depth_config(depth)
        key_color = configs["key_color"]
        value_color = configs["value_color"]
        indent_str = configs["indent_str"]
        brace_indent_str = configs["brace_indent_str"]
        lb, rb = configs["lb"], configs["rb"]
        lk, rk = configs["lk"], configs["rk"]
        colon = configs["colon"]
        comma = configs["comma"]
        ellipsis = configs["ellipsis"]

        if self.max_depth is not None and depth > self.max_depth:
            return f"{lb}{ellipsis}{rb}", "dict"

        lines = []
        if isinstance(d, dict):
            if self.align_list:
                aligner = DictListAligner()
                aligner.align_lists_in_dict(d, align=self.align_list_side)
            if self.add_quotes:
                key_len = max_key_len(d, 2)
            else:
                key_len = max_key_len(d)
            for idx, (key, value) in enumerate(d.items()):
                key_str = f"{key}"
                if self.add_quotes:
                    key_str = f'"{key_str}"'
                if self.align_colon:
                    key_str = chars_slice(key_str, end=key_len)
                if self.key_prefix:
                    key_str = f"{self.key_prefix}{key_str}"
                value_str, value_str_type = self.dict_to_str(
                    value, depth=depth + 1 if isinstance(value, (dict, list)) else depth
                )
                if self.add_quotes:
                    if isinstance(value_str, str) and value_str_type == "str":
                        value_str = f'"{value_str}"'
                if self.is_colored:
                    colored_key_str = colored(key_str, key_color)
                    colored_value_str = colored(value_str, value_color)
                    line = f"{indent_str}{colored_key_str} {colon} {colored_value_str}"
                else:
                    line = f"{indent_str}{key_str} {colon} {value_str}"
                if self.align_list:
                    if key in aligner.list_item_types:
                        if aligner.list_item_types[key] != "str":
                            line = line.replace("'", "")
                if self.use_braces and idx < len(d) - 1:
                    line += comma
                lines.append(line)
            if lines:
                lines_str = "\n".join(lines)
                if self.use_braces:
                    dict_str = f"{lb}\n{lines_str}\n{brace_indent_str}{rb}"
                else:
                    if depth == 0:
                        dict_str = f"{lines_str}"
                    else:
                        dict_str = f"\n{lines_str}"
            else:
                dict_str = f"{lb}{rb}"
            str_type = "dict"
        elif isinstance(d, list):
            is_list_contain_dict = any(isinstance(v, dict) for v in d)
            if is_list_contain_dict:
                list_strs = []
                for v in d:
                    v_str = self.dict_to_str(v, depth=depth)[0]
                    list_strs.append(v_str)
                dict_str = f"{lk}{', '.join(list_strs)}{rk}"
            else:
                dict_str = [self.dict_to_str(v, depth=depth)[0] for v in d]
            str_type = "list"
        else:
            dict_str = d
            str_type = "str"

        return dict_str, str_type


def dict_to_str(
    d: dict,
    indent: int = 2,
    max_depth: int = None,
    align_colon: bool = True,
    align_list: bool = True,
    align_list_side: Literal["l", "r"] = None,
    add_quotes: bool = False,
    is_colored: bool = True,
    brace_colors: list[str] = ["light_blue", "light_cyan", "light_magenta"],
    key_colors: list[str] = ["light_blue", "light_cyan", "light_magenta"],
    value_colors: list[str] = ["white"],
) -> str:
    ds = DictStringifier(
        indent=indent,
        max_depth=max_depth,
        align_colon=align_colon,
        align_list=align_list,
        align_list_side=align_list_side,
        add_quotes=add_quotes,
        is_colored=is_colored,
        brace_colors=brace_colors,
        key_colors=key_colors,
        value_colors=value_colors,
    )
    return ds.dict_to_str(deepcopy(d))[0]


def dict_to_lines(
    d: dict,
    indent: int = 2,
    max_depth: int = None,
    depth_offset: int = 0,
    align_colon: bool = True,
    align_list: bool = True,
    align_list_side: Literal["l", "r"] = None,
    add_quotes: bool = False,
    is_colored: bool = True,
    key_prefix: str = "",
    key_colors: list[str] = ["light_magenta"],
    value_colors: list[str] = ["light_cyan"],
) -> str:
    ds = DictStringifier(
        indent=indent,
        max_depth=max_depth,
        depth_offset=depth_offset,
        align_colon=align_colon,
        align_list=align_list,
        align_list_side=align_list_side,
        add_quotes=add_quotes,
        is_colored=is_colored,
        use_braces=False,
        key_prefix=key_prefix,
        key_colors=key_colors,
        value_colors=value_colors,
    )
    return ds.dict_to_str(deepcopy(d))[0]
