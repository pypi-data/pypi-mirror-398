from pathlib import Path
from typing import Union

KeyType = Union[str, int]
KeysType = Union[KeyType, list[KeyType]]

PathType = Union[str, Path]
PathsType = Union[PathType, list[PathType]]

StrsType = Union[str, list[str]]
IntsType = Union[int, list[int]]

DictListType = Union[dict, list]

LIST_TYPES = (list, tuple, set)
