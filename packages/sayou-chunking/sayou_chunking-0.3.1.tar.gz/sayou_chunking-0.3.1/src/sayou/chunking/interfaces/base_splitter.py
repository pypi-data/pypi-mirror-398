from abc import abstractmethod
from typing import Any, Dict, List, Union

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouBlock, SayouChunk

from ..core.exceptions import SplitterError


class BaseSplitter(BaseComponent):
    """
    (Tier 1) Abstract base class for all chunking strategies.

    Implements the Template Method pattern:
    1. `split()`: Validates input, normalizes it to `SayouBlock`, and handles errors.
    2. `_do_split()`: Abstract hook where subclasses implement the algorithm.
    """

    component_name = "BaseSplitter"
    SUPPORTED_TYPES: List[str] = []

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        return 0.0

    @measure_time
    def split(self, input_data: Union[Dict[str, Any], SayouBlock]) -> List[SayouChunk]:
        """
        [Template Method] Execute the splitting process.

        Args:
            input_data (Union[Dict, SayouBlock]): Raw input containing content.

        Returns:
            List[SayouChunk]: The resulting chunks.
        """
        self._emit("on_start", input_data={"strategy": self.component_name})

        doc = self._normalize_input(input_data)
        split_config = (
            input_data.get("config", {}) if isinstance(input_data, dict) else {}
        )
        if split_config:
            doc.metadata["config"] = {**doc.metadata.get("config", {}), **split_config}

        try:
            chunks = self._do_split(doc)

            self._emit("on_finish", result_data={"chunks": len(chunks)}, success=True)
            return chunks
        except Exception as e:
            self._emit("on_error", error=e)
            self.logger.error(f"Split failed: {e}", exc_info=True)
            raise SplitterError(f"[{self.component_name}] {e}")

    @abstractmethod
    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        [Abstract Hook] Implement the specific splitting logic.

        Args:
            doc (SayouBlock): The normalized input document.

        Returns:
            List[SayouChunk]: The generated chunks.
        """
        raise NotImplementedError

    def _normalize_input(self, input_data: Any) -> SayouBlock:
        """
        Convert various input formats (Dict, SayouBlock) into SayouBlock.

        Args:
            input_data (Any): Raw input.

        Returns:
            SayouBlock: Normalized object.
        """
        if isinstance(input_data, SayouBlock):
            if not isinstance(input_data.content, str):
                input_data.content = str(input_data.content)
            return input_data

        content = getattr(input_data, "content", None) or input_data.get("content")

        metadata = getattr(input_data, "metadata", None) or input_data.get(
            "metadata", {}
        )

        if content is None:
            content = ""

        if not isinstance(content, str):
            content = str(content)

        return SayouBlock(type="text", content=content, metadata=metadata)
