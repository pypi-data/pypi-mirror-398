import sys
import time
import os
import random
import logging
from typing import List

from ..utils import logger


# See https://antofthy.gitlab.io/info/ascii/Spinners.txt for more spinners
_SPINNERS = [
    "䷜䷲䷳",
    "█▓▒░ ░▒▓",
    "⣶⣧⣏⡟⠿⢻⣹⣼",
    "⢸⣸⢼⢺⢹⢺⢼⣸⢸⡇⣇⡧⡗⡏⡗⡧⣇⡇",
    "⠁⠂⠄⡀⡈⡐⡠⣀⣁⣂⣄⣌⣔⣤⣥⣦⣮⣶⣷⣿⡿⠿⢟⠟⡛⠛⠫⢋⠋⠍⡉⠉⠑⠡⢁",
    "🌑🌒🌓🌔🌕🌖🌗🌘",
]


def _format_duration(seconds):
    """Format seconds into a human-readable string."""
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


class Waiter:

    def __init__(
        self,
        prefix: str,
        refresh_time: float,
        terminal_statuses: List[str],
        delay: float = 0.1,
        timeout: float | None = None,
        verbose: bool = False,
        symbols=None,
    ):
        self.terminal_statuses = terminal_statuses
        self.refresh_time = refresh_time
        self.timeout = timeout
        self.verbose = verbose
        if os.environ.get("SPHINX_GALLERY_RUNNING", "0") == "1":
            self.verbose = False
        self.prefix = prefix
        self.delay = delay

        if symbols is None:
            symbols = random.choice(_SPINNERS)
        self.symbols = symbols
        self._current_status: str | None = None
        self._current_rank: int | None = None
        self._status_start: float | None = None
        self._start_time = time.monotonic()
        self._done = False
        self._i = 0

        if self.verbose:
            logger.info("")  # reserve a line for spinner

    def _spin_during(self, duration: float, text: str):
        t0 = time.monotonic()
        i = 0
        while time.monotonic() - t0 < duration:
            sys.stdout.write(f"\r{text:<12} {self.symbols[i % len(self.symbols)]}")
            sys.stdout.flush()
            time.sleep(self.delay)
            i += 1
        sys.stdout.write("\n")
        sys.stdout.flush()

    def update_status(self, status: str):
        """Update internal state when the status changes."""
        if status != self._current_status:
            now = time.monotonic()
            if self._current_status is not None and self.verbose:
                elapsed = int(now - self._status_start)
                sys.stdout.write(
                    f"\r{self.prefix}{self._current_status} ⏱️  {_format_duration(elapsed)}\n"
                )
                sys.stdout.flush()
            self._current_status = status
            self._status_start = now

        if status in self.terminal_statuses:
            self._done = True
            if self.verbose:
                sys.stdout.write(f"\r{self.prefix}{status}\n")
                sys.stdout.flush()

    def update_rank(self, rank: int):
        """Update internal state when the status changes."""
        if rank != self._current_rank:
            now = time.monotonic()
            if self._current_rank is not None and self._current_rank > 0 and self.verbose:
                elapsed = int(now - self._status_start)
                sys.stdout.write(
                    f"\rRank in queue: {self._current_rank} ⏱️  {_format_duration(elapsed)}\n"
                )
                sys.stdout.flush()
            self._current_rank = rank

    def not_complete(self) -> bool:
        """Spin + sleep, return True if still waiting, False if done."""
        if self._done:
            return False

        if self.timeout is not None:
            remaining = self.timeout - (time.monotonic() - self._start_time)
            if remaining <= 0:
                self._done = True
                if self.verbose:
                    logger.info("Timeout reached.")
                return False
            wait_time = min(self.refresh_time, remaining)
        else:
            wait_time = self.refresh_time

        # spin if verbose, else just sleep
        if self.verbose and self._current_status is not None:
            t0 = time.monotonic()
            while time.monotonic() - t0 < wait_time and not self._done:
                symbol = self.symbols[self._i % len(self.symbols)]
                sys.stdout.write(f"\r{self.prefix}{self._current_status:<12} {symbol}")
                sys.stdout.flush()
                time.sleep(self.delay)
                self._i += 1
        else:
            time.sleep(wait_time)

        return not self._done
