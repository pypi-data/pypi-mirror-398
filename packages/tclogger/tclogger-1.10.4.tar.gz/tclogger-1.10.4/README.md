# tclogger
Python terminal colored logger

![](https://img.shields.io/pypi/v/tclogger?label=tclogger&color=blue&cacheSeconds=60)

## Install

By default, this package has no third-party dependencies, so you can feel free to install it with:

```sh
pip install tclogger --upgrade
```

Also, you could install with all optional dependencies for some advanced features:

- `tzdata`: timezone features
- `rapidfuzz`: fuzzy matching

```sh
pip install tclogger[all] --upgrade
```

## Usage

Run example:

```sh
python example.py
```

See: [example.py](https://github.com/Hansimov/tclogger/blob/main/example.py)

```python
import tclogger
import time

from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from tclogger import TCLogger, logger, TCLogstr, logstr, colored, decolored, add_fills
from tclogger import Runtimer, OSEnver, shell_cmd
from tclogger import get_now_ts, get_now_str, get_now_ts_str
from tclogger import TIMEZONE, set_timezone, tcdatetime
from tclogger import ts_to_str, str_to_ts, dt_to_str, unify_ts_and_str
from tclogger import CaseInsensitiveDict, dict_to_str, dict_to_lines
from tclogger import dict_to_table_str
from tclogger import dict_get, dict_set, dict_get_all, dict_set_all
from tclogger import dict_flatten
from tclogger import FileLogger
from tclogger import TCLogbar, TCLogbarGroup
from tclogger import brk, brc, brp
from tclogger import int_bits, max_key_len, chars_len
from tclogger import to_digits, get_by_threshold
from tclogger import chars_slice
from tclogger import attrs_to_dict
from tclogger import obj_param, obj_params
from tclogger import obj_params_dict, obj_params_list, obj_params_tuple
from tclogger import match_val, match_key, iterate_folder, match_paths
from tclogger import copy_file, copy_file_relative, copy_folder
from tclogger import tree_folder
from tclogger import raise_breakpoint


def test_logger_verbose():
    logger.note("Hello ", end="")
    logger.warn("You should not see this message", verbose=False)
    logger.mesg("World")
    logger.verbose = False
    logger.warn("You should not see later messages")
    logger.verbose = True
    logger.set_indent(2)
    logger.success("You should see this message, with indent")


def test_logger_level():
    logger.note("This is a note message")
    logger.warn("This is a warning message")
    logger.enter_quiet(True)
    logger.warn("You should not see this warning message")
    print("You should see an error message below:")
    logger.err("You should see this error message")
    logger.set_level("warning")
    print("Now the level is set to warning:")
    logger.note("You should not see this note message")
    logger.warn("You should see this warning message")
    logger.exit_quiet(True)


def test_fillers():
    fill_str = add_fills()
    logger.note(fill_str)
    fill_str = add_fills(text="hello", filler="= ")
    logger.okay(fill_str)
    fill_str = add_fills(filler="- = ")
    logger.mesg(fill_str)


def test_run_timer_and_logger():
    with Runtimer():
        logger.note(tclogger.__file__)
        logger.mesg(get_now_ts())
        logger.success(get_now_str())
        logger.note(f"Now: {logstr.mesg(get_now_str())}, ({logstr.file(get_now_ts())})")


def test_logger_prefix():
    # Test without prefix (default)
    logger.note("> Default: no prefix, no ms, no color")
    logger.mesg("This is a message without prefix")

    # Test with prefix (no ms, no color)
    prefix_logger = TCLogger(name="MyApp", use_prefix=True)
    logger.note("> With prefix (no ms, no color):")
    prefix_logger.note("This is a note message, no prefix color")
    prefix_logger.mesg("This is a mesg message, no prefix color")
    prefix_logger.warn("This is a warn message, no prefix color")
    prefix_logger.erro("This is a erro message, no prefix color", indent=2)

    # Test with prefix and ms
    ms_logger = TCLogger(name="MSApp", use_prefix=True, use_prefix_ms=True)
    logger.note("> With prefix and ms:")
    ms_logger.note("Note with ms")
    ms_logger.mesg("Mesg with ms")
    ms_logger.warn("Warn with ms")
    ms_logger.okay("Okay with ms (no prefix)", use_prefix=False)

    # Test with prefix, ms and color
    prefix_logger = TCLogger(
        name="MyApp", use_prefix=True, use_prefix_ms=True, use_prefix_color=True
    )
    prefix_logger.set_level("debug")
    logger.note("> With prefix, ms and color:")
    prefix_logger.okay("This is a okay message")
    prefix_logger.erro("This is a erro message")
    prefix_logger.hint("This is a hint message")
    prefix_logger.glow("This is a glow message")
    prefix_logger.file("This is a file message")
    prefix_logger.dbug("This is a dbug message")

    # Test with level warning
    logger.note("> set_level: warning")
    prefix_logger.set_level("warning")
    prefix_logger.okay("This is a okay message")
    prefix_logger.erro("This is a erro message")
    prefix_logger.hint("This is a hint message")


def test_now_and_timezone():
    # Asia/Shanghai
    logger.success(TIMEZONE)
    logger.success(get_now_str())
    dt = tcdatetime.fromisoformat("2024-10-31")
    logger.success(dt)
    # Europe/London
    set_timezone("Europe/London")
    logger.note(get_now_str())
    dt = tcdatetime(year=2024, month=10, day=31)
    logger.note(dt)
    logger.note(tcdatetime.strptime("2024-10-31", "%Y-%m-%d"))
    logger.note(tcdatetime.now())
    dt = tcdatetime.fromisoformat("2024-10-31")
    logger.note(dt)
    logger.note(dt.strftime("%Y-%m-%d %H:%M:%S"))
    # America/New_York
    set_timezone("America/New_York")
    logger.warn(get_now_str())
    dt = tcdatetime.fromisoformat("2024-10-31")
    logger.warn(dt)
    logger.warn(dt.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"))
    # Asia/Shanghai
    set_timezone("Asia/Shanghai")
    logger.success(get_now_str())
    # Compare
    dt1 = tcdatetime.fromisoformat("2024-12-03 12:00:00")
    dt2 = tcdatetime(year=2024, month=12, day=4)
    dt3 = tcdatetime.max()
    logger.note(f"dt1: {dt1}, dt2: {dt2}, dt3: {dt3}")
    cp12 = "<" if dt1 < dt2 else ">"
    cp23 = "<" if dt2 < dt3 else ">"
    cp13 = "<" if dt1 < dt3 else ">"
    logger.success(f"dt1 {cp12} dt2; dt2 {cp23} dt3; dt1 {cp13} dt3")


def test_dt_to_str():
    dt1 = timedelta(seconds=12)
    logger.note(f"dt1: {logstr.success(dt_to_str(dt1))}")
    dt2 = timedelta(seconds=60 * 24 + 12)
    logger.note(f"dt2: {logstr.success(dt_to_str(dt2))}")
    dt3 = timedelta(seconds=3600 * 8 + 60 * 24 + 12)
    logger.note(f"dt3: {logstr.success(dt_to_str(dt3))}")
    dt4 = timedelta(seconds=3600 * 24 * 1 + 3600 * 8 + 60 * 24 + 12)
    logger.note(f"dt4: {logstr.success(dt_to_str(dt4, precision=3))}")
    dt5 = 360100.123
    logger.note(f"dt5: {logstr.success(dt_to_str(dt5, precision=3))}")

    t_ts = 1700000000
    t_ts, t_str = unify_ts_and_str(t_ts)
    logger.mesg(f"t_ts: {logstr.success(t_ts)}, t_str: {logstr.success(t_str)}")
    t_str = "2021-08-31 08:53:20"
    t_ts, t_str = unify_ts_and_str(t_str)
    logger.mesg(f"t_ts: {logstr.success(t_ts)}, t_str: {logstr.success(t_str)}")


def test_color():
    s1 = colored("hello", color="green", bg_color="bg_red", fonts=["bold", "blink"])
    s2 = colored("world", color="red", bg_color="bg_blue", fonts=["bold", "underline"])
    s3 = colored(f"BEG {s1} __ {s2} END")
    logger.note(s3)
    logger.okay(s3)
    s4 = decolored(logstr.okay(s3))
    logger.glow("Glowing text")
    print(s4)


def test_case_insensitive_dict():
    d = CaseInsensitiveDict()
    d["Hello"] = "old world"
    print(d["hello"])
    print(d)
    d["hELLo"] = "New WORLD"
    print(d["HEllO"])
    print(d)


def test_dict_get_and_set():
    d = {
        "owner": {"name": "Alice", "mid": 12345},
        "tags": ["tag1", "tag2", "tag3"],
        "children": [
            {
                "owner": {"name": "Bob", "mid": 54321},
                "tags": ["tag4", "tag5", "tag6"],
            }
        ],
    }
    print(dict_get(d, "owner.name"))
    print(dict_get(d, ["children", 0, "owner", "mid"]))
    dict_set(d, "owner.name", "Alice2")
    print(d)
    dict_set(d, ["owner", "mid"], 56789)
    print(d)
    print(dict_get(d, "owner.none", default="NotExist"))
    dict_set(d, "owner.new", "NewValue")
    print(d)
    dict_set(d, ["children", 1, "owner", "name"], "Bob2")
    print(d)
    dict_set(d, ["tags", 3], "tagsX")
    print(d)


def test_dict_to_str():
    d = {
        "hello": "world",
        "now": get_now_str(),
        "list": [1, 2, 3, [4, 5], "6"],
        "nested": {"key1": "value1", "key2": "value2", "key_3": {"subkey": "subvalue"}},
        "中文Key": "中文Value",
    }
    s = dict_to_str(d, add_quotes=True, max_depth=1)
    logger.success(s)

    print()
    s = dict_to_str(d, add_quotes=False, is_colored=False, max_depth=0)
    print(s)

    print()
    l = dict_to_lines(d)
    print(l)

    print()
    l = dict_to_lines(d, key_prefix="* ")
    print(l)


def test_dict_to_table_str():
    d = {
        ("alice", "smith"): [25, "enginner", "180.2"],
        ("bob", "johnson"): [30, "manager", "175.5"],
        ("charlie", "brown"): [22, "intern", "168.9"],
    }

    key_headers = ["first Name", "last Name"]
    val_headers = ["Age", "Position", "Height"]

    table_str = dict_to_table_str(
        d,
        key_headers=key_headers,
        val_headers=val_headers,
        aligns=["l", "l", "r", "l"],
        default_align="right",
        sum_at_tail=True,
        is_colored=True,
    )
    print(table_str)


def test_log_file():
    logger = TCLogger(
        use_prefix=True,
        use_prefix_color=True,
        use_prefix_ms=True,
        use_file=True,
        # file_path=Path(__file__).parent / "logger.log",
        file_mode="w",
    )
    logger.erro("This is an erro message")
    logger.line("This is a  line message")
    logger.okay("This is an okay message")


def test_file_logger():
    file_logger = FileLogger(Path(__file__).parent / "test.log")
    file_logger.log("This is an error message", "error")
    file_logger.log("This is a default message")
    file_logger.log("This is a prefixed message", prefix="+")
    file_logger.log("This is a success message", msg_type="success")


def test_align_dict_list():
    data = {
        "_id": None,
        "view_avg": 15175,
        "view_maxn": [94092954, 86624275, 68368263, 57713196, 53493614],
        "view_percentile": [39, 152, 254, 539, 3032, 13602, 51956, 282149, 94092954],
        "coin_avg": 57,
        "coin_maxn": [3093375, 2021980, 1420923, 1354206, 1312931],
        "coin_percentile": [0, 0, 0, 1, 6, 24, 76, 682, 3093375],
        "danmaku_avg": 26,
        "danmaku_maxn": [762005, 365521, 349354, 335414, 334935],
        "danmaku_percentile": [0, 0, 0, 0, 2, 12, 57, 353, 762005],
        "percentiles": [0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 0.99, 1.0],
        "sub_lists": {
            "sub1": [1, 2, 4, 5, 6],
            "sub2": [21, 2, 35, 43, 89],
            "sub3": ["a", "abc", "gh", "jkl", "qerq"],
            "sub4": ["x", "ef", "i", "mkns", "adfa"],
        },
        "bools1": [True, False, True, False, True],
        "bools2": [False, True, False, True, True],
    }
    print(dict_to_str(data, align_list=True))


def test_list_of_dicts():
    dict_data = {
        "list_of_lists": [[1, 2, 3], ["a", "b", "c"]],
        "list_of_dicts": [{"key1": "dict1"}, {"key2": "dict2", "key3": "dict3"}],
        "empty_list": [],
        "empty_dict": {},
    }
    print(dict_to_str(dict_data, align_list=True))
    print()
    list_data = [{"key1": "val1"}, {"key2": "val2"}, {"key10": "val10"}]
    print(dict_to_str(list_data, align_list=True))


def test_logbar():
    epochs = 3
    total = 1000000
    logbar = TCLogbar(
        total=total, show_datetime=False, flush_interval=0.1, grid_mode="symbol"
    )
    for epoch in range(epochs):
        for i in range(total):
            logbar.update(increment=1)
            logbar.set_head(f"[{epoch+1}/{epochs}]")
        logbar.grid_mode = "shade"
        logbar.set_desc("THIS IS A SO LONG DESC WHICH IS USED TO TEST LINE UP")
        logbar.reset(linebreak=True)


def test_logbar_group():
    epochs = 3
    total = 100
    sub_total = 1000
    epoch_bar = TCLogbar(total=epochs)
    epoch_bar.set_desc(f"[0/{epochs}]")
    progress_bar = TCLogbar(total=total)
    sub_progress_bar = TCLogbar(total=sub_total)
    TCLogbarGroup([epoch_bar, progress_bar, sub_progress_bar], show_at_init=True)
    # TCLogbarGroup([epoch_bar, progress_bar, sub_progress_bar], show_at_init=False)
    # print("This is a noise line to test lazy blank prints of logbar group.")
    # epoch_bar.update(0)
    for epoch in range(epochs):
        for i in range(total):
            for j in range(sub_total):
                sub_progress_bar.update(1, desc=f"[{j+1}/{sub_total}]")
                time.sleep(0.01)
            sub_progress_bar.reset()
            progress_bar.update(1, desc=f"[{i+1}/{total}]")
        progress_bar.reset()
        epoch_bar.set_desc()
        epoch_bar.update(1, desc=f"[{epoch+1}/{epochs}]", flush=True)


def test_logbar_total():
    total = 500

    logbar = TCLogbar()
    for i in range(total):
        logbar.update(1)
        time.sleep(0.001)
    logbar.flush()
    print()

    logbar = TCLogbar(total=total)
    for i in range(total + 250):
        logbar.update(1)
        time.sleep(0.01)


def test_logbar_verbose():
    total = 1000
    logbar1 = TCLogbar(total=total, show_datetime=False, head="bar1", verbose=False)
    logger.note("> Here should NOT show bar1")
    for i in range(total):
        logbar1.update(1)
    print()

    logbar2 = TCLogbar(total=total, show_datetime=False, head="bar2", verbose=True)
    logger.note("> Here should show bar2")
    for i in range(total):
        logbar2.update(1)
    print()

    logger.note("> Here should NOT show bar1 and bar2")
    TCLogbarGroup([logbar1, logbar2], verbose=False)
    print()

    logger.note("> Here should show bar1 and bar2")
    TCLogbarGroup([logbar1, logbar2], verbose=True)
    print()


def test_decorations():
    text = "Hello World"
    logger.note(f"Brackets: {logstr.mesg(brk(text))}")
    logger.note(f"Braces  : {logstr.mesg(brc(text))}")
    logger.note(f"Parens  : {logstr.mesg(brp(text))}")


def test_math():
    texts = ["你好", "Hello", 12345, "你好，世界！", "Hello, World!", None, 0, ""]
    res = {}
    for text in texts:
        text_len = chars_len(text)
        res[text] = text_len
    key_max_len = max_key_len(res)
    for text, text_len in res.items():
        text_str = str(text) + " " * (key_max_len - chars_len(str(text)))
        text_len_str = logstr.mesg(brk(text_len))
        logger.note(f"{text_str} : {text_len_str}")


def test_get_by_threshold():
    d = {4: 40, "3.2": 30, 1: 10, 2: 20}
    sorted_items = sorted(d.items(), key=lambda item: to_digits(item[0]))
    logger.mesg(dict_to_str(sorted_items))

    logger.note(f"key, 3.5, upper_bound")
    result = get_by_threshold(d, threshold=3.5, direction="upper_bound", target="key")
    print(result)  # (3.2, 30)

    logger.note(f"value, 25, upper_bound")
    result = get_by_threshold(
        sorted_items, threshold=25, direction="upper_bound", target="value"
    )
    print(result)  # (2, 20)

    logger.note("key, 3.5, lower_bound")
    result = get_by_threshold(
        sorted_items, threshold=3.5, direction="lower_bound", target="key"
    )
    print(result)  # (4, 40)

    logger.note("value, 10, upper_bound")
    result = get_by_threshold(
        sorted_items, threshold=10, direction="upper_bound", target="value"
    )
    print(result)  # (1, 10)


def test_str_slice():
    texts = ["你好我是小明", "Hello", 12345789, "你好，世界！", "Hello, World!", "XX"]
    beg, end = 1, 8
    logger.file("pad None")
    for text in texts:
        sliced_str = chars_slice(str(text), beg=beg, end=end)
        logger.note(f"{sliced_str}: {logstr.mesg(text)}")
    logger.file("pad left")
    for text in texts:
        sliced_str = chars_slice(str(text), beg=beg, end=end, align="l")
        logger.note(f"{sliced_str}: {logstr.mesg(text)}")
    logger.file("pad right")
    for text in texts:
        sliced_str = chars_slice(str(text), beg=beg, end=end, align="r")
        logger.note(f"{sliced_str}: {logstr.mesg(text)}")


def test_temp_indent():
    logger.note("no indent")
    with logger.temp_indent(2):
        logger.warn("* indent 2")
        with logger.temp_indent(2):
            logger.err("* indent 4")
        logger.hint("* indent 2")
    logger.mesg("no indent")


def test_attrs_to_dict():
    logger.note("> Logging attrs of logger:")
    attrs_dict = attrs_to_dict(logger)
    logger.mesg(dict_to_str(attrs_dict), indent=2)

    logger.note("> Logging attrs of example:")
    # a obj which allows to add attributes
    obj = type("AnyObject", (), {})()
    obj.dict_val = {
        "hello": "world",
        "now": get_now_str(),
        "list": [1, 2, 3, [4, 5], "6"],
        "nested": {"key1": "value1", "key2": "value2", "key_3": {"subkey": "subvalue"}},
        "中文Key": "中文Value",
    }
    obj.int_val = 12345
    obj.float_val = 3.0
    obj.bool_val = True
    obj.str_val = "Hello World"
    obj.none_val = None
    obj.list_val = [1, 2, 3, 4, 5]
    obj.list_dict_val = [{"k1": "v11", "k2": "v2"}, {"k1": "v21"}, {"k2": "v22"}]
    obj.tuple_val = (1, 2, 3, "4", {"5": 6})
    obj_attrs_dict = attrs_to_dict(obj)
    logger.mesg(dict_to_str(obj_attrs_dict), indent=2)


def test_obj_param():
    class Example:
        def __init__(self):
            self.name = "init_name"
            self.value = 42

    example = Example()
    defaults = ("default_name", 0)

    # no kwargs
    result = obj_param(example, defaults)
    logger.note(f"no kwargs:")
    logger.mesg(result)

    # 1 kwarg
    result = obj_param(example, defaults, name="name_1_kwarg")
    logger.note(f"1 kwarg:")
    logger.mesg(result)

    # 1 kwarg with None
    result = obj_params(example, defaults, name=None)
    logger.note(f"1 kwarg with None:")
    logger.mesg(result)

    # 2 kwargs contain None
    result = obj_params(example, defaults, name=None, value=100)
    logger.note(f"2 kwargs contain None:")
    logger.mesg(result)

    # 2 kwargs
    result = obj_params(example, defaults, name="name_2_kwargs", value=100)
    logger.note(f"2 kwargs:")
    logger.mesg(result)

    # partial kwargs
    result = obj_params_dict(example, defaults, name="name_partial_kwargs")
    logger.note(f"partial kwargs with dict:")
    logger.mesg(result)


def test_match_val():
    val = "hello"
    vals = ["hallo", "Hello", "hello"]
    closest_val, closest_idx, max_score = match_val(val, vals)
    logger.note(f"  * {closest_val} (index: {closest_idx}, score: {max_score})")

    val2 = "new york"
    vals2 = ["new yor", "newyork", "new yorx", "new  yorkz"]
    closest_val, closest_idx, max_score = match_val(
        val2, vals2, spaces_to="merge", use_fuzz=True
    )
    logger.note(f"  * {closest_val} (index: {closest_idx}, score: {max_score})")


def test_match_key():
    def log_key_pattern(key, pattern, is_matched: bool):
        msg = f"{brk(key)} - {pattern}"
        if is_matched:
            mark = "✓ "
            logger.okay(mark + msg)
        else:
            mark = "× "
            logger.warn(mark + msg)

    k11 = "hello.world"
    k12 = "Hello.World"
    k13 = ["hello", "world"]

    p11 = "hello.world"
    p12 = ["hello", "world"]

    for k in [k11, k12, k13]:
        for p in [p11, p12]:
            log_key_pattern(k, p, match_key(k, p, ignore_case=True))

    k21 = "my.stared.works"
    p21 = ["my", "stared.works"]
    p22 = ["my", "Stared", "works"]  # False
    for k in [k21]:
        for p in [p21, p22]:
            log_key_pattern(k, p, match_key(k, p, ignore_case=False))


def test_dict_set_all():
    d = {
        "Hello": {"World": 1},
        "names": [
            {"first": "Alice", "last": "Smith"},
            {"first": "Bob", "last": "Johnson"},
        ],
    }

    logger.note(dict_to_str(d))

    logger.note("> Set 'Hello.World' to 2")
    dict_set_all(d, "Hello.World", 2)
    logger.mesg(dict_to_str(d))

    logger.note("> Set 'names.first' to 'Charlie'")
    dict_set_all(d, "names.first", "Charlie")
    logger.mesg(dict_to_str(d))

    logger.note("> Set 'names.0.last' to 'Xiaoming'")
    dict_set_all(d, "names.0.last", "Xiaoming", index_list=True)
    logger.mesg(dict_to_str(d))


def test_dict_flatten():
    d1 = {
        "owner": {"name": "影视飓风", "face": "https://face.url"},
        "stat": {"view": 6999431, "share": 200},
        "stat.favorite": 100,
        "title": "黑神话悟空：取经路上的山水风光",
        "pages": [
            {
                "cid": 1428998731,
                "dimension": {"x": 100, "y": 200},
                "matrix": [{"mx": 10, "my": 20}, {"mx": 30, "my": 40}],
            },
            {
                "cid": 1428998737,
                "dimension": {"x": 50, "y": 150},
                "matrix": [{"mx": 5, "my": 15}, {"mx": 25, "my": 35}],
            },
        ],
    }

    keys = "owner.name"
    logger.note(f"> Flatten: {keys}")
    dict_flatten(d1, keys=keys)
    logger.mesg(dict_to_str(d1))

    keys = ["pages", "cid"]
    logger.note(f"> Flatten: {keys}")
    dict_flatten(d1, keys=keys)
    logger.mesg(dict_to_str(d1))

    keys = "pages.dimension"
    logger.note(f"> Flatten: {keys}, in_replace=False")
    d2 = dict_flatten(d1, keys=keys, in_replace=False)
    logger.mesg(dict_to_str(d2))
    logger.mesg(f"Is d2 == d1: {d2 == d1}")  # should be False

    keys = "owner"
    logger.note(f"> Flatten: {keys}")
    dict_flatten(d1, keys=keys, expand_sub=True)
    logger.mesg(dict_to_str(d1))

    keys = "stat"
    logger.note(f"> Flatten: {keys}")
    dict_flatten(d1, keys=keys, expand_sub=True)
    logger.mesg(dict_to_str(d1))


def test_match_paths():
    root = Path(__file__).parent
    includes = ["*.py", "*.md"]
    excludes = ["__init__.py", "example.py"]

    logger.note(f"> Matching paths:")
    matched_paths = match_paths(
        root,
        includes=includes,
        excludes=excludes,
        unmatch_bool=True,
        to_str=True,
        verbose=True,
        indent=2,
    )
    logger.note(f"> Matched paths:")
    logger.mesg(dict_to_str(matched_paths), indent=2)


class RaiseBreakpointClass:
    def run(self):
        raise_breakpoint(head_n=2, tail_n=2)


def test_raise_breakpoint():
    obj = RaiseBreakpointClass()
    obj.run()


def test_copy_folder():
    copy_folder(
        src_root=Path(__file__).parent,
        dst_root=Path(__file__).parents[1] / "copy_test",
        includes=["*.py", "*.md"],
        excludes=["__init__.py", "example.py"],
        use_gitignore=True,
        confirm_before_copy=True,
        confirm_before_remove=False,
    )


def test_tree_folder():
    tree_folder(
        root=Path(__file__).parent,
        excludes=["__init__.py"],
        use_gitignore=True,
        show_color=True,
    )


if __name__ == "__main__":
    test_logger_verbose()
    test_logger_level()
    test_fillers()
    test_run_timer_and_logger()
    test_logger_prefix()
    test_now_and_timezone()
    test_dt_to_str()
    test_color()
    test_case_insensitive_dict()
    test_dict_get_and_set()
    test_dict_to_str()
    test_dict_to_table_str()
    test_align_dict_list()
    test_list_of_dicts()
    test_log_file()
    test_file_logger()
    test_logbar()
    test_logbar_group()
    test_logbar_total()
    test_logbar_verbose()
    test_decorations()
    test_math()
    test_get_by_threshold()
    test_str_slice()
    test_temp_indent()
    test_attrs_to_dict()
    test_obj_param()
    test_match_val()
    test_match_key()
    test_dict_set_all()
    test_dict_flatten()
    test_match_paths()
    test_copy_folder()
    test_tree_folder()
    test_raise_breakpoint()

    # python example.py

```