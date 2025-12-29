from abc import ABC, abstractmethod

from beekeeper.core.guardrails.types import GuardrailResponse


class BaseGuardrail(ABC):
    """Abstract base class defining the interface for LLMs."""

    @classmethod
    def class_name(cls) -> str:
        return "BaseGuardrail"

    @abstractmethod
    def enforce(self, text: str, direction: str) -> GuardrailResponse:
        """Runs policies enforcement to specified guardrail."""
