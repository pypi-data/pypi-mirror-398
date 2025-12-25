import time
from typing import List, Dict
from collections import defaultdict
from functools import wraps

from bluer_options import string
from bluer_options.logger import logger
from bluer_options.logger.config import log_list
from bluer_options.timing.elapsed_timer import ElapsedTimer


def recursive_to_dict(d):
    if isinstance(d, (defaultdict, dict)):
        d = {k: recursive_to_dict(v) for k, v in d.items()}
    return d


class Timing:
    def __init__(self):
        self._active = {}
        self.stats = defaultdict(lambda: {"count": 0, "total": 0.0})
        self.elapsed_timer = ElapsedTimer()

    def start(self, keyword: str):
        """Start timing a code block identified by 'keyword'."""
        self._active[keyword] = time.perf_counter()

    def stop(self, keyword: str):
        """Stop timing for 'keyword' and record elapsed time."""
        if keyword not in self._active:
            raise RuntimeError(f"No active timer for {keyword}")

        elapsed = time.perf_counter() - self._active.pop(keyword)
        self.stats[keyword]["count"] += 1
        self.stats[keyword]["total"] += elapsed

        return elapsed

    @property
    def as_dict(self) -> Dict:
        self.calculate()

        return recursive_to_dict(self.stats)

    def as_list(self, **kwgrs) -> List[str]:
        self.calculate()

        lines = []
        # sort items by total time (descending)
        for k, v in sorted(
            self.stats.items(),
            key=lambda item: item[1]["total"],
            reverse=True,
        ):
            lines.append(
                "{}: called {:,} time(s), total {}, avg {}".format(
                    k,
                    v["count"],
                    string.pretty_duration(v["total"], **kwgrs),
                    string.pretty_duration(v["average"], **kwgrs),
                )
            )
        return lines

    def calculate(self):
        for v in self.stats.values():
            v["average"] = v["total"] / v["count"] if v["count"] > 0 else 0

    def log(
        self,
        include_ms: bool = True,
        largest: bool = True,
        short: bool = True,
        **kwargs,
    ):
        log_list(
            logger,
            "in {} called".format(
                self.elapsed_timer.as_str(
                    stop=False,
                    include_ms=include_ms,
                    largest=largest,
                    short=short,
                )
            ),
            self.as_list(
                include_ms=include_ms,
                largest=largest,
                short=short,
            ),
            "function(s):",
            max_count=-1,
            **kwargs,
        )

    def reset(self):
        self._active = {}
        self.stats = defaultdict(lambda: {"count": 0, "total": 0.0})
        self.elapsed_timer.reset()

    def time(self, arg=None):
        """Use as @timing.time, @timing.time(), or @timing.time('custom')"""

        # Case 1: @timing.time  (no parentheses, arg is the function)
        if callable(arg):
            func = arg
            name = func.__name__

            @wraps(func)
            def inner(*args, **kwargs):
                self.start(name)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.stop(name)

            return inner

        # Case 2: @timing.time() or @timing.time("custom")
        keyword = arg  # may be None or str

        def decorator(func):
            name = keyword or func.__name__

            @wraps(func)
            def inner(*args, **kwargs):
                self.start(name)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.stop(name)

            return inner

        return decorator
