from datetime import datetime, timedelta
from typing import Literal, Union

from .colors import colored
from .logs import logger, add_fills
from .times import get_now, t_to_str, dt_to_str, dt_to_sec


class Runtimer:
    def __init__(self, verbose=True):
        self.verbose = verbose

    def __enter__(self):
        self.start_time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end_time()
        self.elapsed_time()

    def start_time(self):
        self.t1 = get_now()
        self.logger_time("start", self.t1)
        return self.t1

    def end_time(self):
        self.t2 = get_now()
        self.logger_time("end", self.t2)
        return self.t2

    def elapsed_time(self):
        self.dt = self.t2 - self.t1
        self.logger_time("elapsed", self.dt)
        return self.dt

    @property
    def elapsed_seconds(self) -> float:
        if hasattr(self, "dt"):
            pass
        else:
            self.dt = self.end_time() - self.start_time()
        return dt_to_sec(self.dt, precision=2)

    def logger_time(
        self,
        time_type: Literal["start", "end", "elapsed"],
        t: Union[datetime, timedelta],
    ):
        if not self.verbose:
            return
        time_types = {
            "start": "Start",
            "end": "End",
            "elapsed": "Elapsed",
        }

        if isinstance(t, datetime):
            t_str = t_to_str(t)
        elif isinstance(t, timedelta):
            t_str = dt_to_str(t)
        else:
            t_str = str(t)

        if time_type == "elapsed":
            time_color = "light_green"
            fill_color = "light_green"
        else:
            time_color = "light_magenta"
            fill_color = "light_magenta"
        time_str = colored(f"{time_types[time_type]} time: [ {t_str} ]", time_color)

        filled_time_str = add_fills(
            time_str,
            filler="* ",
            fill_side="both",
            is_text_colored=True,
            fill_color=fill_color,
        )
        logger.line(filled_time_str)
