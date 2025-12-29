from abc import ABC, abstractmethod
from typing import List, Tuple

from beekeeper.core.document import Document
from deprecated import deprecated


class BaseVectorStore(ABC):
    """Abstract base class defining the interface for vector store."""

    @classmethod
    def class_name(cls) -> str:
        return "BaseVectorStore"

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to vector store."""

    @abstractmethod
    def query_documents(self, query: str, top_k: int = 4) -> List[Document]:
        """Query for similar documents in the vector store based on the input query provided."""

    @deprecated(
        reason="'search_documents()' is deprecated and will be removed in a future version. Use 'query_documents' instead.",
        version="1.0.2",
        action="always",
    )
    def search_documents(self, query: str, top_k: int = 4) -> List[Document]:
        return self.query_documents(query, top_k)

    @abstractmethod
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from vector store."""

    @abstractmethod
    def get_all_documents(self, include_fields: List[str]) -> List[Document]:
        """Get all documents from vector store."""

    def get_all_document_hashes(self) -> Tuple[List[str], List[str], List[str]]:
        """Get all ref hashes from vector store."""
        hits = self.get_all_documents()

        ids = [doc.id_ for doc in hits]
        hashes = [doc.metadata.get("hash") for doc in hits]
        ref_hashes = [doc.metadata.get("ref_doc_hash") for doc in hits]

        return ids, hashes, ref_hashes
