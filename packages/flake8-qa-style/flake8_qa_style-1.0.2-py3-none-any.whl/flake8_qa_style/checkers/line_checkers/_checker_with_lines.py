from abc import ABC, abstractmethod
from typing import Generator, Optional


class CheckerWithLines(ABC):
    def __init__(self, filename: Optional[str] = None, lines: Optional[list[str]] = None):
        self.filename: Optional[str] = filename
        self.lines: Optional[list[str]] = lines
        self.errors: list[Error] = []

    @abstractmethod
    def check(self) -> None:
        pass
