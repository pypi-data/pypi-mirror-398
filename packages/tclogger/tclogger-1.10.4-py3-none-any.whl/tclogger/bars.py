import math
import os
import sys
import threading

from datetime import timedelta
from typing import Union, Literal

from .times import get_now, t_to_str, dt_to_str, dt_to_sec
from .maths import int_bits
from .logs import logstr
from .colors import decolored
from .cursors import CursorController


class TCLogbar:
    PROGRESS_LOGSTR = {
        0: logstr.file,
        25: logstr.note,
        50: logstr.hint,
        75: logstr.err,
        100: logstr.success,
    }

    def __init__(
        self,
        count: int = 0,
        total: int = None,
        start_count: int = 0,
        head: str = "",
        desc: str = "",
        cols: int = 35,
        auto_cols: bool = False,
        show_at_init: bool = False,
        show_datetime: bool = False,
        show_iter_per_second: bool = True,
        show_color: bool = True,
        flush_interval: float = 0.1,
        grid_symbols: str = " ▏▎▍▌▋▊▉█",
        grid_shades: str = "░▒▓█",
        grid_mode: Literal["symbol", "shade"] = "symbol",
        verbose: bool = True,
    ):
        self.total = total
        self.start_count = start_count
        self.count = count or start_count
        self.head = head
        self.desc = desc
        self.cols = cols
        self.auto_cols = auto_cols
        self.show_at_init = show_at_init
        self.show_datetime = show_datetime
        self.show_iter_per_second = show_iter_per_second
        self.show_color = show_color
        self.flush_interval = flush_interval
        self.grid_symbols = grid_symbols
        self.grid_shades = grid_shades
        self.grid_mode = grid_mode
        self.verbose = verbose
        self.bar_str = None
        self.init_t = get_now()
        self.start_t = self.init_t
        self.flush_t = self.init_t
        self.cursor = CursorController()
        self.line_height: int = 1
        self.group: TCLogbarGroup = None
        self.node_idx: int = None
        if self.show_at_init:
            self.update(flush=True)

    def is_num(self, num: Union[int, float]):
        return isinstance(num, (int, float))

    def is_grouped(self):
        return self.group is not None and self.node_idx is not None

    def elapsed_count(self):
        return self.count - self.start_count

    def remain_count(self):
        return self.total - self.count

    def move_cursor(self):
        self.cursor.move(row=self.line_height - 1)
        self.cursor.erase_line()
        self.cursor.move_to_beg()

    def write(self, msg: str):
        sys.stdout.write(msg)
        sys.stdout.flush()

    def log(self, msg: str = None):
        if msg is None:
            return
        if self.is_grouped():
            if not self.group.verbose:
                return
            self.group.move_cursor(self.node_idx)
            self.group.write(msg)
        else:
            if not self.verbose:
                return
            self.move_cursor()
            self.write(msg)

        terminal_width = os.get_terminal_size().columns
        if len(decolored(msg)) > terminal_width:
            self.line_height = math.ceil(len(decolored(msg)) / terminal_width)
        else:
            self.line_height = 1

    def flush(self):
        if self.verbose or (self.is_grouped() and self.group.verbose):
            self.construct_bar_str()
            self.log(self.bar_str)

    def linebreak(self):
        if self.is_grouped():
            if self.group.verbose:
                self.group.write("\n")
        else:
            if self.verbose:
                self.write("\n")

    def update(
        self,
        increment: int = None,
        count: int = None,
        head: str = None,
        desc: str = None,
        remain_seconds: float = None,
        flush: bool = False,
        linebreak: bool = False,
    ):
        self.now = get_now()

        if count is not None:
            self.count = count
        elif increment is not None:
            self.count += increment
        else:
            pass

        if self.is_num(self.total) and self.is_num(self.count) and self.total > 0:
            self.percent_float = self.count / self.total * 100
            self.percent = int(self.percent_float)
        else:
            self.percent_float = None
            self.percent = None

        if flush is True:
            pass
        elif self.is_num(self.percent_float) and (
            self.percent_float >= 100 or self.percent_float <= 0
        ):
            flush = True
        elif self.flush_interval is not None:
            flush_dt = self.now - self.flush_t
            flush_seconds = flush_dt.seconds + flush_dt.microseconds / 1000000
            if flush_seconds < self.flush_interval:
                flush = False
            else:
                flush = True
                self.flush_t = self.now
        else:
            pass

        if flush is True:
            if head is not None:
                self.head = head
            if desc is not None:
                self.desc = desc

            self.dt = self.now - self.start_t
            dt_seconds = dt_to_sec(self.dt, precision=3)

            if remain_seconds is not None and self.is_num(remain_seconds):
                self.remain_seconds = remain_seconds
            elif (
                self.is_num(self.total)
                and self.is_num(self.count)
                and self.elapsed_count() > 0
                and self.remain_count() >= 0
            ):
                self.remain_seconds = (
                    dt_seconds * self.remain_count() / self.elapsed_count()
                )
            else:
                self.remain_seconds = None

            if self.is_num(self.count) and self.count > 0 and dt_seconds > 0:
                self.iter_per_second = round(
                    self.elapsed_count() / dt_seconds, ndigits=1
                )
            else:
                self.iter_per_second = None

            self.flush()

            if linebreak:
                self.linebreak()

    def construct_grid_str(self):
        if self.grid_mode == "shade":
            grids = self.grid_shades
        else:
            grids = self.grid_symbols

        if self.percent is not None:
            count_total_col = min(self.count / self.total, 1) * self.cols
            full_grid_cols = int(count_total_col)
            active_grid_idx = min(
                int(((count_total_col) - int(count_total_col)) * (len(grids) - 1)),
                len(grids) - 2,
            )
            if active_grid_idx < 1:
                active_grid_str = ""
            else:
                active_grid_str = grids[active_grid_idx]
            full_grid_str = full_grid_cols * grids[-1]
            grid_percent_str = f"{self.percent}%"
            visible_grid_str = full_grid_str + active_grid_str
            if len(visible_grid_str) + len(grid_percent_str) > self.cols:
                grid_percent_str = ""
            fill_grid_str = (
                self.cols - len(visible_grid_str) - len(grid_percent_str)
            ) * grids[0]
            grid_str = visible_grid_str + grid_percent_str + fill_grid_str
        else:
            grid_str = self.cols * grids[0]

        return grid_str

    def construct_bar_str(self):
        if self.show_datetime:
            now_str = f"[{t_to_str(self.now)}]"
            if self.head:
                now_str = f" {now_str}"
        else:
            now_str = ""

        elapsed_str = dt_to_str(self.dt)

        if self.percent is not None:
            percent_str = f"{self.percent:>3}%"
        else:
            percent_str = f"{'?':>3}%"

        grid_str = self.construct_grid_str()

        if self.remain_seconds is not None:
            remain_str = dt_to_str(self.remain_seconds)
        else:
            remain_str = "??:??"

        if self.is_num(self.total):
            total_bits = int_bits(self.total)
            total_str = str(self.total)
        else:
            total_bits = 0
            total_str = "?"

        if self.is_num(self.count):
            count_str = f"{self.count:_>{total_bits}}"
        else:
            count_str = "?"

        if self.iter_per_second is not None:
            if self.iter_per_second > 1 or self.iter_per_second == 0:
                iter_per_second_str = f"({round(self.iter_per_second)} it/s)"
            else:
                iter_per_second_str = f"({round(1/self.iter_per_second)} s/it)"
        else:
            iter_per_second_str = ""

        if self.head:
            head_str = f"{self.head}"
        else:
            head_str = ""

        if self.desc:
            desc_str = f"{self.desc}"
            if self.head or self.show_datetime:
                desc_str = f" {desc_str}"
        else:
            desc_str = ""

        if self.show_color:
            if not self.is_num(self.percent):
                progress_logstr_key = 0
            else:
                progress_logstr_key = min(self.percent // 25 * 25, 100)
            logstr_progress = self.PROGRESS_LOGSTR[progress_logstr_key]
            count_str = logstr_progress(count_str)
            total_str = logstr.mesg(total_str)
            now_str = logstr.mesg(now_str)
            percent_str = logstr_progress(percent_str)
            grid_str = logstr_progress(grid_str)
            elapsed_str = logstr.mesg(elapsed_str)
            remain_str = logstr_progress(remain_str)
            iter_per_second_str = logstr.mesg(iter_per_second_str)

        self.bar_str = (
            f"{head_str}"
            f"{now_str}{desc_str}: "
            f"{percent_str} "
            f"▌{grid_str}▐ "
            f"{count_str}/{total_str} "
            f"[{elapsed_str}<{remain_str}] "
            f"{iter_per_second_str}"
        )

    def reset(self, linebreak: bool = False):
        if linebreak:
            self.linebreak()
        self.count = 0
        self.start_t = get_now()

    def set_cols(self, cols: int = None):
        self.cols = cols

    def set_total(self, total: int = None):
        self.total = total

    def set_count(self, count: int = None):
        self.count = count

    def set_start_count(self, start_count: int = None):
        self.start_count = start_count

    def increment(self, increment: int = None):
        self.count += increment

    def set_desc(self, desc: str = None):
        self.desc = desc

    def set_head(self, head: str = None):
        self.head = head

    def hide(self):
        pass

    def show(self):
        pass


class TCLogbarGroup:
    def __init__(
        self, bars: list[TCLogbar], show_at_init: bool = True, verbose: bool = True
    ):
        self.bars = bars
        self.show_at_init = show_at_init
        self.verbose = verbose
        self.cursor = CursorController()
        self.lock = threading.Lock()
        self.init_bars()

    def init_bars(self):
        for idx, bar in enumerate(self.bars):
            bar.group = self
            bar.node_idx = idx
        self.log_node_idx = None
        self.total_line_height = 0
        for bar in self.bars:
            self.total_line_height += bar.line_height
        if self.show_at_init:
            for bar in self.bars:
                bar.update(flush=True)

    def write(self, msg: str, flush: bool = True):
        with self.lock:
            sys.stdout.write(msg)
            if flush:
                sys.stdout.flush()

    def move_cursor(self, node_idx: int):
        # prepare blank area for logbars
        if self.log_node_idx is None:
            self.write(self.total_line_height * "\n")
            self.cursor.move(row=self.total_line_height)
            self.cursor.move_to_beg()
            self.log_node_idx = 0

        if node_idx > self.log_node_idx:
            down_rows = 1  # from last line end to next line beg
            for node in self.bars[self.log_node_idx + 1 : node_idx]:
                down_rows += node.line_height
            self.cursor.move(row=-down_rows)
        elif node_idx < self.log_node_idx:
            up_rows = 0
            for node in self.bars[node_idx : self.log_node_idx + 1]:
                up_rows += node.line_height
            up_rows -= 1  # as previous cursor already at last line end of previous node
            self.cursor.move(row=up_rows)
        else:
            up_rows = self.bars[node_idx].line_height - 1
            self.cursor.move(row=up_rows)

        self.cursor.erase_line()
        self.cursor.move_to_beg()
        self.log_node_idx = node_idx
