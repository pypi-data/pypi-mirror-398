from abc import ABC, abstractmethod
from typing import Any, Iterable


class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, constraints: Iterable) -> None:
        """Translate constraints to solver model."""
        pass

    @abstractmethod
    def solve(self) -> dict[str, Any]:
        """Solve the model and return variable assignments."""
        pass
