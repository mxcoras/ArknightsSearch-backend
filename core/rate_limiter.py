import asyncio
from collections import deque
from collections.abc import Callable, Hashable

from fastapi import Depends, HTTPException, Request

from .util import Date


class Limiter:
    def __init__(self, interval: float, query: int, key: Callable[[Request], Hashable] | None = None):
        self.interval: float = interval
        self.query: int = query
        self.queue_dict: dict[Hashable, deque] = {}
        self.key: Callable[[Request], Hashable] = key or self.default_key

    def clean(self):
        for k, queue in self.queue_dict.copy().items():
            if Date.now - queue[-1] > self.interval:
                self.queue_dict.pop(k)

    def apply(self, key: Hashable) -> bool:
        queue = self.queue_dict.setdefault(key, deque(maxlen=self.query))
        if len(queue) == self.query:
            if Date.now - queue[0] < self.interval:
                return False
            queue.popleft()

        queue.append(Date.now)
        return True

    @staticmethod
    def default_key(request: Request) -> str:
        return request.client.host if request.client is not None else "unknown"

    def check(self, request: Request):
        if not self.apply(self.key(request)):
            raise HTTPException(status_code=429)

    @classmethod
    def depends(cls, interval: float, query: int):
        self = cls.__new__(cls)
        self.__init__(interval, query)
        return Depends(self.check)


class LimiterManager:
    limiters: list[Limiter] = []
    cd: int = 60

    @classmethod
    def clean(cls):
        for i in cls.limiters:
            i.clean()

    @classmethod
    async def scavenger(cls):
        while True:
            await asyncio.sleep(cls.cd)
            cls.clean()

    @classmethod
    def add(cls, limiter: Limiter):
        cls.limiters.append(limiter)
