from abc import ABC, abstractmethod
from typing import List

from beekeeper.core.document import Document
from beekeeper.core.schema import TransformerComponent
from deprecated import deprecated


class BaseTextChunker(TransformerComponent, ABC):
    """Abstract base class defining the interface for text chunker."""

    @classmethod
    def class_name(cls) -> str:
        return "BaseTextChunker"

    @abstractmethod
    def chunk_text(self, text: str) -> List[str]:
        """Split a single string of text into smaller chunks."""

    @abstractmethod
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split a list of documents into smaller document chunks."""

    @deprecated(
        reason="'from_text()' is deprecated and will be removed in a future version. Use 'chunk_text' instead.",
        version="1.0.2",
        action="always",
    )
    def from_text(self, text: str) -> List[str]:
        return self.chunk_text(text)

    @deprecated(
        reason="'from_documents()' is deprecated and will be removed in a future version. Use 'chunk_documents' instead.",
        version="1.0.2",
        action="always",
    )
    def from_documents(self, documents: List[Document]) -> List[Document]:
        return self.chunk_documents(documents)

    def __call__(self, documents: List[Document]) -> List[Document]:
        return self.chunk_documents(documents)
