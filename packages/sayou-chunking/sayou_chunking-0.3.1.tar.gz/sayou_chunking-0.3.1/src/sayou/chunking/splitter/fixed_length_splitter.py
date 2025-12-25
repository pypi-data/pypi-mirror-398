from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter


@register_component("splitter")
class FixedLengthSplitter(BaseSplitter):
    """
    Simple Fixed-Length Splitter.

    Splits text strictly by character count, ignoring semantic boundaries.
    Useful for precise token count control but may break sentences.
    """

    component_name = "FixedLengthSplitter"
    SUPPORTED_TYPES = ["fixed_length"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["fixed_length"]:
            return 1.0

        if isinstance(input_data, str) or isinstance(input_data, list):
            return 0.4

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Slice content by `chunk_size` with `chunk_overlap`.
        """
        config = doc.metadata.get("config", {})
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 0)
        content = doc.content

        text_chunks = []
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        step = chunk_size - chunk_overlap
        for i in range(0, len(content), step):
            text_chunks.append(content[i : i + chunk_size])

        return [SayouChunk(content=t, metadata=doc.metadata) for t in text_chunks]
