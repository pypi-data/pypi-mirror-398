from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class Polynomial(ABC):
    """Abstract base class for all polynomials."""

    @abstractmethod
    def degree(self) -> int:
        pass

    @abstractmethod
    def coefficients(self) -> Iterable[float]:
        pass

    @abstractmethod
    def value_at(self, x: float) -> float:
        pass
