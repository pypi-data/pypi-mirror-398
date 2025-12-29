from abc import ABC, abstractmethod
from typing import Optional

from beekeeper.core.monitors.types import PayloadRecord
from beekeeper.core.prompts import PromptTemplate


class BaseMonitor(ABC):
    """Abstract base class defining the interface for monitors."""

    @classmethod
    def class_name(cls) -> str:
        return "BaseMonitor"


class PromptMonitor(BaseMonitor):
    """Abstract base class defining the interface for prompt observability."""

    def __init__(self, prompt_template: Optional[PromptTemplate] = None) -> None:
        self.prompt_template = prompt_template

    @classmethod
    def class_name(cls) -> str:
        return "PromptMonitor"

    @abstractmethod
    def __call__(self, payload: PayloadRecord) -> None:
        """PromptMonitor."""


class TelemetryMonitor(BaseMonitor):
    """Abstract base class defining the interface for telemetry observability."""

    @classmethod
    def class_name(cls) -> str:
        return "TelemetryMonitor"
