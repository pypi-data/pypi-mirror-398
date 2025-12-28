from __future__ import annotations

from abc import ABC, abstractmethod

from ..events import UsageEvent


class Sink(ABC):
    @abstractmethod
    def write(self, event: UsageEvent) -> None:
        raise NotImplementedError
