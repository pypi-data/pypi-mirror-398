from typing import List

from beekeeper.core.document import Document
from beekeeper.core.text_chunkers.base import BaseTextChunker
from beekeeper.core.text_chunkers.utils import (
    merge_splits,
    split_by_char,
    split_by_fns,
    split_by_sep,
    tokenizer,
)


class TokenTextChunker(BaseTextChunker):
    r"""
    This is the simplest splitting method. Designed to split input text into smaller chunks
    by looking at word tokens.

    Attributes:
        chunk_size (int, optional): Size of each chunk. Default is `512`.
        chunk_overlap (int, optional): Amount of overlap between chunks. Default is `256`.
        separator (str, optional): Separators used for splitting into words. Default is `\\n\\n`.

    Example:
        ```python
        from beekeeper.core.text_chunkers import TokenTextChunker

        text_chunker = TokenTextChunker()
        ```
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 256,
        separator="\n\n",
    ) -> None:
        if chunk_overlap > chunk_size:
            raise ValueError(
                f"Got a larger `chunk_overlap` ({chunk_overlap}) than `chunk_size` "
                f"({chunk_size}). `chunk_overlap` should be smaller.",
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._split_fns = [split_by_sep(separator)]

        self._sub_split_fns = [split_by_char()]

    def chunk_text(self, text: str) -> List[str]:
        """
        Split a single string of text into smaller chunks.

        Args:
            text (str): Input text to split.

        Returns:
            List[str]: List of text chunks.

        Example:
            ```python
            chunks = text_chunker.chunk_text(
                "Beekeeper is a data framework to load any data in one line of code and connect with AI applications."
            )
            ```
        """
        splits = self._split(text)

        return merge_splits(splits, self.chunk_size, self.chunk_overlap)

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into smaller document chunks.

        Args:
            documents (List[Document]): List of `Document` objects to split.

        Returns:
            List[Document]: List of chunked documents objects.
        """
        chunks = []

        for document in documents:
            texts = self.chunk_text(document.get_content())
            metadata = {**document.get_metadata()}

            for text in texts:
                if len(texts) > 1:
                    metadata["ref_doc_id"] = document.id_
                    metadata["ref_doc_hash"] = document.hash

                chunks.append(
                    Document(
                        text=text,
                        metadata=metadata,
                    ),
                )

        return chunks

    def _split(self, text: str) -> List[dict]:
        text_len = len(tokenizer(text))
        if text_len <= self.chunk_size:
            return [{"text": text, "is_sentence": True, "token_size": text_len}]

        text_splits = []
        text_splits_by_fns, is_sentence = split_by_fns(
            text,
            self._split_fns,
            self._sub_split_fns,
        )

        for text_split_by_fns in text_splits_by_fns:
            split_len = len(tokenizer(text_split_by_fns))
            if split_len <= self.chunk_size:
                text_splits.append(
                    {
                        "text": text_split_by_fns,
                        "is_sentence": False,
                        "token_size": split_len,
                    },
                )
            else:
                recursive_text_splits = self._split(text_split_by_fns)
                text_splits.extend(recursive_text_splits)

        return text_splits
