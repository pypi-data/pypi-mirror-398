from abc import abstractmethod
from typing import List

from beekeeper.core.document import BaseDocument


class TransformerComponent:
    @abstractmethod
    def __call__(self, documents: List[BaseDocument]) -> List[BaseDocument]:
        """Transform documents."""
