from collections.abc import Callable

"""It is ok to use lambdas to shorten codes of calls,
but readability and extensibility are more important here.
"""

# helper functions


def type_str(attr) -> str:
    attr_type = type(attr)
    type_module = attr_type.__module__
    type_name = attr_type.__name__
    if type_module == "builtins":
        return type_name
    else:
        return f"{type_module}.{type_name}"


def dict_type_str(obj: dict) -> str:
    dict_keys = str(list(obj.keys()))
    dict_keys_str = f"{{{dict_keys[1:-1]}}}"
    return f"dict{dict_keys_str}[{len(obj)}]"


# default is_include in attrs_to_dict


def is_attr_included(name: str, attr) -> bool:
    """Only include attrs that are: non-internal, non-callable, and non-staticmethod"""
    return (
        not name.startswith("__")
        and not callable(attr)
        and type(attr) is not staticmethod
    )


# default callables in attrs_to_dict


def none_call() -> tuple[Callable, Callable]:
    def key_call(name, attr) -> bool:
        return attr is None

    def val_call(name, attr):
        return "None"

    return key_call, val_call


def constant_call() -> tuple[Callable, Callable]:
    def key_call(name, attr) -> bool:
        return isinstance(attr, (int, float, str, bool, type(None)))

    def val_call(name, attr):
        if isinstance(attr, str):
            return f"'{attr}'"
        if isinstance(attr, (int, float, bool)):
            return attr
        return f"({type_str(attr)}) {attr}"

    return key_call, val_call


def list_call() -> tuple[Callable, Callable]:
    def key_call(name, attr) -> bool:
        return isinstance(attr, list)

    def val_call(name, attr):
        if len(attr) > 0:
            list_type = type(attr[0]).__name__
            list_size = len(attr)
            if list_type == "dict":
                return dict_type_str(attr[0])
            else:
                return f"list({list_type})[{list_size}]"
        else:
            return f"[]"

    return key_call, val_call


def tuple_call() -> tuple[Callable, Callable]:
    def key_call(name, attr) -> bool:
        return isinstance(attr, tuple)

    def val_call(name, attr):
        if len(attr) > 0:
            tuple_types = str(list(map(lambda x: type(x).__name__, attr)))
            tuple_size = len(attr)
            tuple_types_str = f"({tuple_types[1:-1]})"
            return f"tuple{tuple_types_str}[{tuple_size}]"
        else:
            return f"(,)"

    return key_call, val_call


def dict_call() -> tuple[Callable, Callable]:
    def key_call(name, attr) -> bool:
        return isinstance(attr, dict)

    def val_call(name, attr):
        return dict_type_str(attr)

    return key_call, val_call


def iter_call() -> tuple[Callable, Callable]:
    def key_call(name, attr) -> bool:
        return hasattr(attr, "__iter__")

    def val_call(name, attr):
        if hasattr(attr, "__len__"):
            return f"iter[{len(attr)}]"
        else:
            return f"iter"

    return key_call, val_call


def type_call() -> tuple[Callable, Callable]:
    def key_call(name, attr) -> bool:
        return True

    def val_call(name, attr):
        return f"<{type_str(attr)}>"

    return key_call, val_call


MID_CALLS = [
    *[none_call(), constant_call()],
    *[list_call(), tuple_call(), dict_call(), iter_call()],
]
LAST_CALLS = [type_call()]


# main function
def attrs_to_dict(
    obj,
    is_include: Callable = is_attr_included,
    pre_calls: list[tuple[Callable, Callable]] = None,
    post_calls: list[tuple[Callable, Callable]] = None,
) -> dict:
    """The is_include, and each callable in pre_calls and post_calls should take two arguments:
    - name: str, the name of the attribute
    - attr, the attribute itself
    The pre_calls are called before mid_calls, and the post_calls are called after mid_calls.

    For is_include:
    - if True, the attr would be included in the result
    - if False, the attribute would be ignored

    For each callable in pre_calls and post_calls:
    - the 1st callable (key_call) is to determine whether the 2nd callable (val_call) should be called
    - if key_call returns True, val_call would be called, and the result would be the value of the attr
    - if all key_call return False, the last_call would be called to set the default value of the attr
    """
    res = {}
    pre_calls = pre_calls or []
    post_calls = post_calls or []
    calls = [*pre_calls, *MID_CALLS, *post_calls, *LAST_CALLS]
    for name, attr in obj.__dict__.items():
        if is_include(name, attr):
            for key_call, val_call in calls:
                if key_call(name, attr):
                    res[name] = val_call(name, attr)
                    break

    return res
