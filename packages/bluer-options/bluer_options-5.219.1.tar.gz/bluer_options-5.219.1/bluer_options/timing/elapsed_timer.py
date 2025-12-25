import time
from bluer_options import string


class ElapsedTimer:
    def __init__(self):
        self.start_time = time.time()
        self.elapsed_time_ = None

    def as_str(
        self,
        stop: bool = True,
        **kwargs,
    ):
        if stop:
            self.stop()

        elapsed_time = self.elapsed_time

        return (
            "None"
            if elapsed_time is None
            else string.pretty_duration(elapsed_time, **kwargs)
        )

    @property
    def elapsed_time(self) -> float:
        if self.start_time is None:
            return self.elapsed_time_

        return time.time() - self.start_time

    def reset(self):
        self.start_time = time.time()
        self.elapsed_time_ = None

    def stop(self):
        if self.start_time is None:
            return

        self.elapsed_time_ = self.elapsed_time
        self.start_time = None
