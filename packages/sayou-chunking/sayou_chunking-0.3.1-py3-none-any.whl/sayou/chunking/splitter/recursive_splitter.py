from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter
from ..utils.text_segmenter import TextSegmenter


@register_component("splitter")
class RecursiveSplitter(BaseSplitter):
    """
    Standard Recursive Character Splitter.

    Splits text by iteratively trying a list of separators (Paragraph -> Line -> Sentence).
    It ensures that semantically related text stays together as much as possible
    within the given `chunk_size`.
    """

    component_name = "RecursiveSplitter"
    SUPPORTED_TYPES = ["recursive"]

    DEFAULT_SEPARATORS = ["\n\n", "\n", r"(?<=[.?!])\s+", " ", ""]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["recursive"]:
            return 1.0

        if isinstance(input_data, SayouBlock):
            if input_data.type in ["text", "txt", "string"]:
                return 1.0
            return 0.1

        if isinstance(input_data, str):
            return 0.6

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Execute recursive splitting using `TextSegmenter`.
        """
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")

        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 100)
        separators = config.get("separators", self.DEFAULT_SEPARATORS)
        protected_patterns = config.get("protected_patterns", [])

        text_chunks = TextSegmenter.split_with_protection(
            text=doc.content,
            separators=separators,
            protected_patterns=protected_patterns,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        return [
            SayouChunk(
                content=text.strip(),
                metadata={
                    **doc.metadata,
                    "chunk_id": f"{doc_id}_{i}",
                    "chunk_size": len(text.strip()),
                    "part_index": i,
                },
            )
            for i, text in enumerate(text_chunks)
        ]
