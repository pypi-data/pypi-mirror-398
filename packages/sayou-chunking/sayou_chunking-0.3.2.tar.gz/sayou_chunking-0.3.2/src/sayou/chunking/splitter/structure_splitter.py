import re
from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter
from ..utils.text_segmenter import TextSegmenter


@register_component("splitter")
class StructureSplitter(BaseSplitter):
    """
    Regex-based Structure Splitter.

    Uses a user-defined regex pattern (e.g., 'Article \d+') to identify
    structural boundaries in the document and splits along those lines first.
    """

    component_name = "StructureSplitter"
    SUPPORTED_TYPES = ["structure"]

    DEFAULT_SEPARATORS = ["\n\n", "\n", r"(?<=[.?!])\s+", " ", ""]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["structure"]:
            return 1.0

        if isinstance(input_data, SayouBlock):
            if input_data.type in ["md", "markdown"]:
                return 0.9

            if input_data.type in ["html", "table", "json"]:
                return 1.0

            content = input_data.content
            if isinstance(content, str):
                if content.strip().startswith(("<html", "<!DOCTYPE", "<div")):
                    return 1.0
                if "```" in content or "~~~" in content:
                    return 0.9

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")
        chunk_size = config.get("chunk_size", 1000)

        structure_pattern = config.get("structure_pattern", r"\n\n")

        try:
            split_regex = f"(?m)(?={structure_pattern})"
            sections = re.split(split_regex, doc.content)
        except Exception:
            sections = doc.content.split("\n\n")

        final_chunks = []

        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            base_meta = doc.metadata.copy()
            base_meta["parent_structure_idx"] = i

            if len(section) > chunk_size:
                sub_parts = TextSegmenter.split_with_protection(
                    text=section,
                    separators=config.get("separators", self.DEFAULT_SEPARATORS),
                    protected_patterns=config.get("protected_patterns", []),
                    chunk_size=chunk_size,
                    chunk_overlap=config.get("chunk_overlap", 50),
                )
                for j, part in enumerate(sub_parts):
                    meta = base_meta.copy()
                    meta.update(
                        {
                            "chunk_id": f"{doc_id}_s{i}_p{j}",
                            "chunk_size": len(part),
                        }
                    )
                    final_chunks.append(SayouChunk(content=part, metadata=meta))
            else:
                base_meta.update(
                    {
                        "chunk_id": f"{doc_id}_s{i}",
                        "chunk_size": len(section),
                    }
                )
                final_chunks.append(SayouChunk(content=section, metadata=base_meta))

        return final_chunks
