import time
from timeit import default_timer

import simdjson


class Json:
    @staticmethod
    def dump(data, path: str):
        with open(path, mode='wt', encoding='utf-8') as f:
            return simdjson.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(path: str):
        with open(path, mode='rt', encoding='utf-8') as f:
            return simdjson.load(f)


json = Json


class DateInstance:
    @property
    def now(self) -> float:
        return time.time()

    @property
    def timestamp(self) -> int:
        return int(self.now)

    @property
    def second(self) -> int:
        return self.timestamp

    def get_second(self) -> int:
        return self.timestamp

    @property
    def minute(self) -> int:
        return self.timestamp // 60

    def get_minute(self) -> int:
        return self.minute

    @property
    def hour(self) -> int:
        return self.timestamp // 3600

    def get_hour(self) -> int:
        return self.hour

    @property
    def day(self) -> int:
        return self.timestamp // 86400

    def get_day(self) -> int:
        return self.day


Date = DateInstance()


class TimeRecorder:
    def __init__(self, keep: int = 6):
        # 保留x位有效数字
        self.keep: int = keep

    def __enter__(self):
        self.start: float = default_timer()
        return self

    @property
    def diff(self):
        return default_timer() - self.start

    @property
    def string_format(self):
        return '%.6gs' % self.diff

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
