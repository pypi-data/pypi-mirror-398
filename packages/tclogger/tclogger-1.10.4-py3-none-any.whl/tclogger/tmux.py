import argparse
import os
import re
from pathlib import Path

from .colors import decolored
from .envs import shell_cmd

# Constants
OUTPUT_FILE = "cli.log"
LAST_LINES = 1000
MAX_LINES = 10000

TMUX = "TMUX"
CWD = Path.cwd()

# "$", "(\w+)", "~", "/", "<user>@<host>"
RE_MARK = r"[\$]"  # starts with $
RE_PATH = r"[\~\/]"  # starts with ~ or /
RE_CENV = r"\(\w+\)"  # starts with (env)
RE_USER = r"\w+\@\w+"  # starts with user@host
CMD_PATTERNS = [rf"^\s*({RE_MARK}|{RE_PATH}|{RE_CENV}|{RE_USER})"]
TMUX_CMD_PATTERNS = [" -m tclogger.tmux"]


class CmdPromptChecker:
    """Check command prompt line based on regex."""

    def __init__(self, pattern: str = None) -> None:
        if pattern:
            self.cmd_re = re.compile(pattern)
        else:
            self.cmd_re = re.compile("|".join(p for p in CMD_PATTERNS))

    def is_cmd_prompt(self, line: str) -> bool:
        return bool(self.cmd_re.match(line))

    def is_tmux_cmd(self, cmd: str) -> bool:
        return any(p in cmd for p in TMUX_CMD_PATTERNS)


class TmuxLogger:
    """Capture and log tmux pane commands history."""

    def __init__(
        self,
        output_file: str = OUTPUT_FILE,
        cmd_num: int = None,
        last_lines: int = LAST_LINES,
        max_lines: int = MAX_LINES,
        cmd_only: bool = False,
        must_have_output: bool = True,
        cmd_pattern: str = None,
        include_pattern: str = None,
        exclude_pattern: str = None,
        skip_tmux_cmds: bool = True,
    ) -> None:
        """
        Args:
        - `output_file`: Output file name (default: cli.log)
        - `cmd_num`: Number of recent cmds to include (default: None, will use all cmds from last_lines)
        - `last_lines`: Number of history lines to capture from tmux (default: 1000)
        - `max_lines`: Maximum number of lines to capture when searching for cmds (default: 10000)
        - `cmd_only`: If True, only capture cmds without outputs
        - `must_have_output`: If True, only keep cmd/output pairs where output has non-whitespace content
        - `cmd_pattern`: Custom regex pattern to identify cmd lines (default: None, uses built-in pattern)
        - `include_pattern`: Regex pattern to filter cmds to include (default: None, includes all)
        - `exclude_pattern`: Regex pattern to filter cmds to exclude (default: None, excludes none)
        - `skip_tmux_cmds`: If True, exclude tmux commands and outputs (default: True)
        """
        self.output_file = output_file
        self.cmd_num = cmd_num
        self.last_lines = last_lines
        self.max_lines = max_lines
        self.cmd_only = cmd_only
        self.must_have_output = must_have_output
        self.cmd_pattern = cmd_pattern
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.skip_tmux_cmds = skip_tmux_cmds
        self.current_lines = last_lines
        self.log_path = CWD / self.output_file
        self.cmd_checker = CmdPromptChecker(pattern=cmd_pattern)

    @staticmethod
    def _has_effective_output(output: str) -> bool:
        return bool(output and output.strip())

    @staticmethod
    def is_in_tmux() -> bool:
        return TMUX in os.environ

    def capture_pane_to_file(self) -> bool:
        """Capture tmux pane output to file via `tmux capture-pane`.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_in_tmux():
            return False

        try:
            cmd = f"tmux capture-pane -p -J -S -{self.current_lines} > {self.log_path}"
            # -p    : print to stdout
            # -S -N : N lines starting from bottom
            # -J    : join wrapped lines
            shell_cmd(cmd, showcmd=False)
            return True
        except Exception as e:
            return False

    def parse_cmds_outputs_from_file(self) -> list[tuple[str, str]]:
        """Parse cmds from tmux output file by search cmd prompts.

        Returns: list of (cmd, output) tuples
        """
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                output = f.read()
        except Exception:
            return []

        if not output:
            return []

        lines = output.split("\n")
        results = []

        current_cmd = None
        current_output = []

        for line in lines:
            line_rstrip = line.rstrip()
            if self.cmd_checker.is_cmd_prompt(line_rstrip):
                # Save previous cmd and output
                if current_cmd is not None:
                    results.append((current_cmd.rstrip(), "\n".join(current_output)))
                # Start new cmd (use whole line as cmd)
                current_cmd = line_rstrip
                current_output = []
            else:
                # This is output from current cmd
                if current_cmd is not None:
                    current_output.append(line_rstrip)

        # Append last cmd
        if current_cmd is not None:
            results.append((current_cmd.rstrip(), "\n".join(current_output)))

        # Remove tmux cmds
        if self.skip_tmux_cmds and results:
            results = [
                (cmd, output)
                for cmd, output in results
                if not self.cmd_checker.is_tmux_cmd(cmd)
            ]

        # Keep only pairs that have effective output
        if self.must_have_output and results:
            results = [
                (cmd, output)
                for cmd, output in results
                if self._has_effective_output(output)
            ]

        # Apply include pattern filter
        if self.include_pattern:
            include_re = re.compile(self.include_pattern)
            results = [
                (cmd, output) for cmd, output in results if include_re.search(cmd)
            ]

        # Apply exclude pattern filter
        if self.exclude_pattern:
            exclude_re = re.compile(self.exclude_pattern)
            results = [
                (cmd, output) for cmd, output in results if not exclude_re.search(cmd)
            ]

        # Return last N cmds
        if self.cmd_num is None:
            return results
        else:
            return results[-self.cmd_num :] if results else []

    def log(self) -> None:
        """Create log file with recent cmd history."""
        cmd_output_pairs = []

        # capture enough history to get the required number of cmds
        while self.current_lines <= self.max_lines:
            if not self.capture_pane_to_file():
                return
            cmd_output_pairs = self.parse_cmds_outputs_from_file()
            if self.cmd_num is None:
                break
            if len(cmd_output_pairs) >= self.cmd_num:
                break
            if self.current_lines < self.max_lines:
                self.current_lines = min(self.current_lines * 2, self.max_lines)
            else:
                break

        if not cmd_output_pairs:
            return

        # concat and decolor
        log_lines = []
        for cmd, output in cmd_output_pairs:
            log_lines.append(f"{cmd}\n{output}\n")
        log_content = "".join(log_lines)
        log_content = decolored(log_content)

        # save to file
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(log_content)


class TmuxLoggerArgParser:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description="Create log file with tmux cmd and outputs history"
        )
        self._add_arguments()

    def _add_arguments(self) -> None:
        self.parser.add_argument(
            "-o",
            "--output",
            type=str,
            default=OUTPUT_FILE,
            help=f"Output file (default: {OUTPUT_FILE})",
        )
        self.parser.add_argument(
            "-n",
            "--cmd-num",
            type=int,
            default=None,
            help="Number of recent cmds to include (default: None, will use all cmds from last-lines)",
        )
        self.parser.add_argument(
            "-l",
            "--last-lines",
            type=int,
            default=LAST_LINES,
            help=f"Number of history lines to capture from tmux (default: {LAST_LINES})",
        )
        self.parser.add_argument(
            "-m",
            "--max-lines",
            type=int,
            default=MAX_LINES,
            help=f"Maximum number of lines to capture when searching for cmds (default: {MAX_LINES})",
        )
        self.parser.add_argument(
            "-c",
            "--cmd-only",
            action="store_true",
            help="Capture cmds only, no outputs",
        )
        self.parser.add_argument(
            "-u",
            "--must-have-output",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Keep only cmd/output pairs whose output is non-whitespace (default: True)",
        )
        self.parser.add_argument(
            "-p",
            "--cmd-pattern",
            type=str,
            default=None,
            help="Custom regex pattern to identify cmd lines (default: None, uses built-in pattern)",
        )
        self.parser.add_argument(
            "-i",
            "--include-pattern",
            type=str,
            default=None,
            help="Regex pattern to filter cmds to include (default: None, includes all)",
        )
        self.parser.add_argument(
            "-e",
            "--exclude-pattern",
            type=str,
            default=None,
            help="Regex pattern to filter cmds to exclude (default: None, excludes none)",
        )

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args()


def log_tmux() -> None:
    """Main entry point for the tmux CLI tool."""
    arg_parser = TmuxLoggerArgParser()
    args = arg_parser.parse_args()

    tmlogger = TmuxLogger(
        output_file=args.output,
        cmd_num=args.cmd_num,
        last_lines=args.last_lines,
        max_lines=args.max_lines,
        cmd_only=args.cmd_only,
        must_have_output=args.must_have_output,
        cmd_pattern=args.cmd_pattern,
        include_pattern=args.include_pattern,
        exclude_pattern=args.exclude_pattern,
    )
    tmlogger.log()


if __name__ == "__main__":
    log_tmux()

    # python -m tclogger.tmux -n 5
    # python -m tclogger.tmux -n 5 -i "python"
