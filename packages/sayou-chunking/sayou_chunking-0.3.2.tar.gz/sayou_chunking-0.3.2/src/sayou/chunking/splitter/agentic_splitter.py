from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter


@register_component("splitter")
class AgenticSplitter(BaseSplitter):
    """
    LLM-based Splitter (Placeholder).

    Intended to use an LLM Agent to determine the most semantically
    meaningful breakpoints in the text.
    """

    component_name = "AgenticSplitter"
    SUPPORTED_TYPES = ["llm_agent"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["llm_agent"]:
            return 1.0
        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Delegate splitting logic to an LLM (Mock implementation).
        """
        # TODO: 실제 LLM Client 연동 필요
        self._log(
            "Agentic splitting is not fully implemented yet. Returning raw content."
        )

        return [SayouChunk(content=doc.content, metadata=doc.metadata)]
