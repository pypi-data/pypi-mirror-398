from abc import ABC, abstractmethod
from typing import List

from beekeeper.core.document import Document
from pydantic.v1 import BaseModel


class BaseReader(ABC, BaseModel):
    """Abstract base class defining the interface for document reader."""

    @classmethod
    def class_name(cls) -> str:
        return "BaseReader"

    @abstractmethod
    def load_data(self) -> List[Document]:
        """Loads data."""
