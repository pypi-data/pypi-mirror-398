import re
from typing import Any, List, Optional

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter
from ..utils.text_segmenter import TextSegmenter


@register_component("splitter")
class MarkdownSplitter(BaseSplitter):
    """
    Markdown-aware Splitter.

    Specialized for Markdown documents. It respects headers (#, ##),
    protects code blocks and tables from being split, and enriches chunks
    with semantic metadata (e.g., 'section_title', 'parent_id').
    """

    component_name = "MarkdownSplitter"
    SUPPORTED_TYPES = ["markdown", "md"]

    MARKDOWN_SEPARATORS = [
        r"(?m)^\s*#{1,6}\s+",
        r"(?m)\n\s*\n",
        "\n",
        r"(?<=[.?!])\s+",
        " ",
        "",
    ]
    PROTECTED_PATTERNS = [
        r"(?s)```.*?```",
        r"(?m)^(?:\|[^\n]*\|(?:\n|$))+",
        r"data:image\/[a-zA-Z]+;base64,[a-zA-Z0-9+/=]+",
        r"(?:(?:[A-Za-z0-9+/]{4}){100,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?)",
    ]
    SECTION_SPLIT_PATTERN = r"(?m)^(?=#{1,6} |[-*] |\d+\. )"

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        """
        Smart detection logic to identify Markdown/Structural content.

        Prioritizes:
        1. Explicit strategy requests.
        2. SayouBlock metadata (from Refinery).
        3. Raw string regex patterns (Headers, Tables, Fences).
        """
        if strategy in ["markdown", "md"]:
            return 1.0

        if isinstance(input_data, SayouBlock):
            if input_data.type in ["md", "markdown"]:
                return 1.0

            if isinstance(input_data.content, str):
                score = 0.0
                if re.search(r"(?m)^#{1,6}\s", input_data.content):
                    score = 0.95
                return score

        if isinstance(input_data, str):
            if re.search(r"(?m)^#{1,6}\s", input_data):
                return 0.95

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Split by Markdown headers first, then recursively split content.
        """
        pipeline_config = getattr(self, "config", {})
        doc_config = doc.metadata.get("config", {})
        chunk_size = doc_config.get(
            "chunk_size", pipeline_config.get("chunk_size", 1000)
        )
        doc_id = doc.metadata.get("id", "doc")

        # 1. 헤더 단위 1차 분할
        raw_sections = re.split(self.SECTION_SPLIT_PATTERN, doc.content)
        raw_sections = [s for s in raw_sections if s.strip()]

        final_chunks = []
        global_idx = 0

        # Context Stack: 현재 유효한 헤더 ID를 추적하기 위한 변수
        # (단순화를 위해 직전 헤더만 추적하지만, 필요시 스택으로 H1>H2>H3 구현 가능)
        current_parent_id: Optional[str] = None
        current_parent_text: Optional[str] = None

        body_separators = self.MARKDOWN_SEPARATORS[1:]

        for section in raw_sections:
            header_match = re.match(r"^(#{1,6})\s+(.*)", section.strip().split("\n")[0])

            if header_match:
                header_level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                header_chunk_id = f"{doc_id}_h_{global_idx}"

                header_chunk = SayouChunk(
                    content=f"{header_match.group(1)} {header_text}",
                    metadata={
                        **self._clean_meta(doc.metadata),
                        "chunk_id": header_chunk_id,
                        "part_index": global_idx,
                        "semantic_type": f"h{header_level}",
                        "is_header": True,
                        "level": header_level,
                    },
                )
                final_chunks.append(header_chunk)
                current_parent_id = header_chunk_id
                current_parent_text = header_text
                global_idx += 1

                body_content = section[header_match.end() :].strip()
            else:
                body_content = section

            if not body_content:
                continue

            # 본문(Body) 미세 분할 (리스트, 텍스트 등)
            # 여기서 Structure-First 전략: 리스트(-) 단위로도 먼저 쪼개고 싶다면 로직 추가 가능
            # 일단은 TextSegmenter로 안전하게 자름
            body_parts = TextSegmenter.split_with_protection(
                text=body_content,
                separators=body_separators,
                protected_patterns=self.PROTECTED_PATTERNS,
                chunk_size=chunk_size,
                chunk_overlap=0,
            )

            for part in body_parts:
                part = part.strip()
                if not part:
                    continue

                semantic_type = self._classify_chunk(part)

                meta = self._clean_meta(doc.metadata)
                meta.update(
                    {
                        "chunk_id": f"{doc_id}_part_{global_idx}",
                        "part_index": global_idx,
                        "semantic_type": semantic_type,
                        "parent_id": current_parent_id,
                        "section_title": current_parent_text,
                    }
                )

                if semantic_type == "image":
                    meta["image_length"] = len(part)

                final_chunks.append(SayouChunk(content=part, metadata=meta))
                global_idx += 1

        return final_chunks

    def _clean_meta(self, meta: dict) -> dict:
        """Remove temporary config data from metadata before saving."""
        m = meta.copy()
        m.pop("config", None)
        return m

    def _classify_chunk(self, text: str) -> str:
        """Identify if a text segment is a table, list, code, or plain text."""
        if text.startswith("|"):
            return "table"
        if text.startswith("```"):
            return "code_block"
        if re.match(r"^[-*] ", text):
            return "list_item"
        return "text"
