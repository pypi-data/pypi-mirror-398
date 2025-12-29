def obj_param(obj, defaults=None, **kwargs):
    """Special case of obj_params, which only contains one kwarg."""
    if len(kwargs) == 0:
        return defaults

    if len(kwargs) == 1:
        key, val = next(iter(kwargs.items()))
        if val is not None:
            return val
        elif hasattr(obj, key):
            return getattr(obj, key)
        else:
            return defaults


def obj_params_dict(obj, defaults=None, **kwargs) -> dict:
    if len(kwargs) == 0:
        return defaults

    if len(kwargs) == 1:
        key, val = next(iter(kwargs.items()))
        if val is not None:
            return {key: val}
        elif hasattr(obj, key):
            return {key: getattr(obj, key)}
        else:
            return {key: defaults}

    # len(kwargs) > 1
    res = {}
    if defaults is None:
        defaults_dict = {}
    elif isinstance(defaults, (list, tuple)):
        defaults_dict = dict(zip(kwargs.keys(), defaults))
    elif isinstance(defaults, dict):
        defaults_dict = defaults

    for key, val in kwargs.items():
        if val is not None:
            res[key] = val
        elif hasattr(obj, key):
            res[key] = getattr(obj, key)
        else:
            res[key] = defaults_dict.get(key, None)
    return res


def obj_params_list(obj, defaults=None, **kwargs) -> list:
    return list(obj_params_dict(obj, defaults, **kwargs).values())


def obj_params_tuple(obj, defaults=None, **kwargs) -> tuple:
    return tuple(obj_params_dict(obj, defaults, **kwargs).values())


def obj_params(obj, defaults=None, **kwargs):
    """
    Resolve param with priority:
    1. kwargs
    2. obj attr
    3. defaults

    Usage:
    - `obj_params(obj, defaults="", model="model_name")`
    - `obj_params(obj, defaults=("", False), model="model_name", stream=True)`
    - `obj_params(obj, defaults={"model": "", "stream": False}, model="model_name", stream=True)`

    Inputs:
        Not allowed keys of kwargs: `obj`, `defaults`

    Return:
        0 kwarg : return `defaults`
        1 kwarg : return value
        N kwargs: return tuple

    Number of returned params is same with kwargs.
    """
    if len(kwargs) == 0:
        return defaults
    elif len(kwargs) == 1:
        return obj_param(obj, defaults, **kwargs)
    else:
        res_dict = obj_params_dict(obj, defaults, **kwargs)
        return tuple(res_dict.values())
