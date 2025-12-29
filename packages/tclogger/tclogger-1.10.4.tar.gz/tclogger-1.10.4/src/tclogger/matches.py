import os
import re

from copy import deepcopy
from functools import partial
from pathlib import Path
from rapidfuzz import fuzz
from typing import Literal, Union, Protocol, Iterator

from .logs import TCLogger
from .types import KeysType, StrsType, PathType, PathsType
from .paths import norm_path

logger = TCLogger(__name__)


def match_val(
    val: str,
    vals: list[str],
    ignore_case: bool = True,
    spaces_to: Literal["keep", "ignore" "merge"] = "merge",
    use_fuzz: bool = False,
) -> tuple[str, int, float]:
    """
    Return:
        - closest val
        - index of the closest val in the list
        - similarity score (0-1)

    score = (1 – d/L)
    * d: distance by insert(1)/delete(1)/replace(2)
    * L: length sum of both strings
    """
    if not vals:
        return None, None, 0

    xval = deepcopy(val)
    xvals = deepcopy(vals)

    if spaces_to == "ignore":
        xval = re.sub(r"\s+", "", val.strip())
        xvals = [re.sub(r"\s+", "", v.strip()) for v in vals]
    elif spaces_to == "merge":
        xval = re.sub(r"\s+", " ", val.strip())
        xvals = [re.sub(r"\s+", " ", v.strip()) for v in vals]
    else:
        pass

    if ignore_case:
        xval = xval.lower()
        xvals = [v.lower() for v in xvals]

    if use_fuzz:
        scores = [fuzz.ratio(xval, v) / 100.0 for v in xvals]
    else:
        scores = [1 if xval == v else 0 for v in xvals]

    midx, max_score = None, 0.0
    for i, s in enumerate(scores):
        if s > max_score:
            midx = i
            max_score = s
    if midx is None:
        mval = None
    else:
        mval = vals[midx]
    return mval, midx, max_score


class MatchKeyFuncType(Protocol):
    """Match key with pattern.

    Example functions::
    - `match_key`: match key with pattern
    """

    def __call__(self, key: KeysType, pattern: KeysType, **kwargs) -> bool: ...


def unify_key_to_list(
    key: KeysType, ignore_case: bool = False, sep: str = "."
) -> list[Union[str, int]]:
    xkey = deepcopy(key)
    if isinstance(xkey, str):
        # split "a.b.c" to ["a", "b", "c"]
        xkey = xkey.split(sep)
    elif isinstance(xkey, (list, tuple)):
        # split case like ["a.b", "c"]
        xkey = [k.split(sep) if isinstance(k, str) else k for k in xkey]
        xkey = [item for sublist in xkey for item in sublist]
    if ignore_case:
        xkey = [k.lower() if isinstance(k, str) else k for k in xkey]
    return xkey


def unify_key_to_str(key: KeysType, ignore_case: bool = False, sep: str = ".") -> str:
    """Compared to `unitfy_key_to_list()`, this would enable match_key to accept str-format list idx in as key part.
    This means that "a.0.x" is same to ["a", 0, "x"] and ["a", "0", "x"].
    """
    xkey = deepcopy(key)
    if isinstance(xkey, (list, tuple)):
        xkey = sep.join(str(k) for k in xkey)
    if ignore_case:
        xkey = xkey.lower()
    return xkey


def match_key(
    key: KeysType,
    pattern: KeysType,
    ignore_case: bool = False,
    use_regex: bool = False,
    sep: str = ".",
) -> bool:
    unify_params = {"ignore_case": ignore_case, "sep": sep}
    xkey = unify_key_to_str(key, **unify_params)
    xpattern = unify_key_to_str(pattern, **unify_params)
    if use_regex:
        xpattern = rf"{xpattern}$"
        return re.search(xpattern, xkey) is not None
    else:
        return xkey == xpattern


def unify_paths(paths: PathsType) -> list[PathType]:
    """Unify paths to a list of Path objects."""
    if not paths:
        return []
    if isinstance(paths, (str, Path)):
        paths = [paths]
    return paths


def patternize_path(path: str) -> str:
    path = path.strip()
    # ignore comment lines
    if path.startswith("#"):
        return ""
    if path:
        # replace * to .*, and . (not ends with *) to \.
        path = re.sub(r"\*", ".*", path.strip())
        path = re.sub(r"\.(?!\*)", r"\.", path)
        # if not starts with /, prepend .*/
        if not path.startswith("/"):
            path = f".*/{path}"
        # remove trailing slashes
        path = path.rstrip("/")
    return path


def get_gitignore_patterns(root: PathType) -> list[str]:
    """Load .gitignore patterns.
    NOTE: Currently only covers .gitignore **under root**,
    and would support sub-directories in the future.
    """
    res = [".git"]
    path = Path(root) / ".gitignore"
    if path.exists():
        with path.open() as f:
            lines = f.read().splitlines()
        lines = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
        res.extend(lines)
    return res


def unify_includes_excludes(
    root: PathType = ".",
    includes: StrsType = None,
    excludes: StrsType = None,
    use_gitignore: bool = True,
) -> tuple[list[str], list[str]]:
    """Unify includes and excludes to list of strs."""
    includes = unify_paths(includes)
    excludes = unify_paths(excludes)
    if use_gitignore:
        gitignore_patterns = get_gitignore_patterns(root)
        excludes.extend(gitignore_patterns)
    includes = [patternize_path(p) for p in includes]
    excludes = [patternize_path(p) for p in excludes]
    includes = [p for p in includes if p]
    excludes = [p for p in excludes if p]
    return includes, excludes


class InExCludeMatchFuncType(Protocol):
    """Match path with include or exclude pattern.

    Example functions::
    - `re_search`: match path with re.search
    """

    def __call__(self, path: PathType, pattern: str, **kwargs) -> bool: ...


def re_search(
    path: PathType,
    pattern: str,
    ignore_case: bool = True,
    suffix_match: bool = True,
) -> bool:
    """NOTE: Compared to `re.search(<pattern>, <string>, flags)`,
    the order of params `path` and `pattern` in `re_search` is swapped.
    The intension is to be consistent with `match_path()` and `match_key()`.
    """
    if ignore_case:
        flags = re.IGNORECASE
    else:
        flags = 0
    if suffix_match:
        pattern = rf"{pattern}$"
    return re.search(pattern, str(path), flags=flags) is not None


def inexclude_path_match(
    path: PathType,
    includes: StrsType = None,
    excludes: StrsType = None,
    include_match_func: InExCludeMatchFuncType = None,
    exclude_match_func: InExCludeMatchFuncType = None,
    unmatch_bool: bool = True,
) -> bool:
    if not includes and not excludes:
        return False

    if excludes:
        for exclude_pattern in excludes:
            if exclude_match_func(path, exclude_pattern):
                return False

    if includes:
        for include_pattern in includes:
            if include_match_func(path, include_pattern):
                return True

    # When program reaches here,
    # it means both includes and excludes are not matched

    # if includes is provided while excludes not, then unmatch means False
    if includes and not excludes:
        return False
    # if excludes is provided while includes not, then unmatch means True
    if excludes and not includes:
        return True
    # if both are provided, return unmatch_bool
    return unmatch_bool


class MatchPathFuncType(Protocol):
    """Match path with includes and excludes.

    Required params:
    - `path`: path to match
    - `includes`: list of include patterns
    - `excludes`: list of exclude patterns

    Example functions:
    - `match_path`: match path with includes and excludes
    """

    def __call__(
        self, path: PathType, includes: StrsType, excludes: StrsType, **kwargs
    ) -> bool: ...


def match_path(
    path: PathType,
    includes: StrsType = None,
    excludes: StrsType = None,
    unmatch_bool: bool = True,
    ignore_case: bool = True,
) -> bool:
    partial_params = {
        "ignore_case": ignore_case,
        "suffix_match": True,
    }
    include_match_func: InExCludeMatchFuncType = partial(re_search, **partial_params)
    exclude_match_func: InExCludeMatchFuncType = partial(re_search, **partial_params)
    return inexclude_path_match(
        path,
        includes=includes,
        excludes=excludes,
        include_match_func=include_match_func,
        exclude_match_func=exclude_match_func,
        unmatch_bool=unmatch_bool,
    )


def inner_iterate_folder(
    root: PathType = ".",
    match_func: MatchPathFuncType = match_path,
    verbose: bool = True,
    indent: int = 2,
    level: int = 0,
) -> Iterator[tuple[Path, bool, int]]:
    root = norm_path(root)
    if level == 0:
        logger.note(f"> {root}", verbose=verbose, indent=indent)
        temp_indent = indent + 2
    else:
        temp_indent = 2
    with logger.temp_indent(temp_indent):
        if root.is_file():
            yield root, match_func(root), level
        else:
            level = level + 1
            for p in os.listdir(root):
                p = Path(root) / p
                match_bool = match_func(p)
                if p.is_file():
                    yield p, match_bool, level
                elif p.is_dir():
                    if match_bool:
                        logger.note(f"> {p}", verbose=verbose)
                        yield p, match_bool, level
                        yield from inner_iterate_folder(
                            p,
                            match_func=match_func,
                            verbose=verbose,
                            level=level,
                        )
                    else:
                        yield p, match_bool, level
                else:
                    logger.warn(f"* skip: {p}", verbose=verbose)
                    pass


def iterate_folder(
    root: PathType = ".",
    includes: StrsType = None,
    excludes: StrsType = None,
    yield_folder: bool = False,
    unmatch_bool: bool = True,
    ignore_case: bool = True,
    use_gitignore: bool = True,
    verbose: bool = True,
    indent: int = 2,
) -> Iterator[tuple[Path, bool, int]]:
    """Iterate paths with includes and excludes.

    Args:
        - root: root path to traverse
        - includes: list of patterns to include
        - excludes: list of patterns to exclude
        - unmatch_bool: default bool when path is not matched by neither includes nor excludes
        - ignore_case: ignore case when matching
        - use_gitignore: whether to add .gitignore to excludes
        - verbose: whether to log process
        - indent: logging indent spaces

    Yields:
        - (path, match_bool, level)

    In a previous version, there are two more args:
        - include_func: function to call when a path is included
        - exclude_func: function to call when a path is excluded
    These two args are removed, as this target could be reached more easily, by just iterate the iterator and operate on the yielded (path, match_bool, level) tuples.
    """
    includes, excludes = unify_includes_excludes(
        root, includes=includes, excludes=excludes, use_gitignore=use_gitignore
    )
    match_func: MatchPathFuncType = partial(
        match_path,
        includes=includes,
        excludes=excludes,
        unmatch_bool=unmatch_bool,
        ignore_case=ignore_case,
    )
    for p, match_bool, level in inner_iterate_folder(
        root, match_func=match_func, verbose=verbose, indent=indent
    ):
        if not yield_folder and p.is_dir():
            continue
        if verbose and p.is_file():
            if match_bool:
                logger.file(f"+ {p}")
            if not match_bool:
                logger.warn(f"- {p}")
        yield p, match_bool, level


def match_paths(
    root: PathType = ".",
    includes: StrsType = None,
    excludes: StrsType = None,
    unmatch_bool: bool = True,
    ignore_case: bool = True,
    use_gitignore: bool = True,
    to_str: bool = True,
    verbose: bool = True,
    indent: int = 2,
) -> dict:
    """Match paths in a folder with includes and excludes.
    Args:
        - to_str: whether to convert paths to str in result
        - See `iterate_folder()` for other arguments.

    Return dict with keys:

    ```py
    {
        "includes": <list of matched include paths>,
        "excludes": <list of matched exclude paths>,
    }
    ```
    """

    res = {
        "includes": [],
        "excludes": [],
    }
    for p, match_bool, level in iterate_folder(
        root,
        includes=includes,
        excludes=excludes,
        unmatch_bool=unmatch_bool,
        ignore_case=ignore_case,
        use_gitignore=use_gitignore,
        verbose=verbose,
        indent=indent,
    ):
        if match_bool:
            res["includes"].append(p)
        else:
            res["excludes"].append(p)

    if to_str:
        res["includes"] = [str(p) for p in res["includes"]]
        res["excludes"] = [str(p) for p in res["excludes"]]

    return res
