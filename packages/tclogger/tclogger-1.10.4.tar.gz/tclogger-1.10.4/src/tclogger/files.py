import threading

from pathlib import Path
from typing import Literal, Union

from .times import get_now_str


MSG_PREFIXES = {"note": ">", "error": "×", "success": "√"}


class FileLogger:
    def __init__(self, log_path: Union[str, Path], lock: threading.Lock = None):
        if not isinstance(log_path, Path):
            log_path = Path(log_path)
        self.log_path = log_path
        if not self.log_path.parent.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = lock or threading.Lock()

    def log(
        self,
        msg: str,
        msg_type: Literal["note", "error", "success"] = None,
        prefix: str = None,
        add_now: bool = True,
    ):
        if prefix:
            prefix_str = f"{prefix} "
        elif msg_type:
            prefix_str = MSG_PREFIXES.get(msg_type, "*") + " "
        else:
            prefix_str = ""

        if add_now:
            line = f"{prefix_str}[{get_now_str()}] {msg}\n"
        else:
            line = f"{prefix_str}{msg}\n"
        with self.lock:
            with open(self.log_path, "a") as f:
                f.write(line)
