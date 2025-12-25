import time
from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..splitter.fixed_length_splitter import FixedLengthSplitter


@register_component("splitter")
class AuditedFixedLengthSplitter(FixedLengthSplitter):
    """
    Fixed Splitter with auditing.

    Inherits standard fixed splitting but adds an audit trail (timestamp,
    original length) to the metadata of each chunk.
    """

    component_name = "AuditedFixedLengthSplitter"
    SUPPORTED_TYPES = ["audited_fixed"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy == "audited_fixed":
            return 1.0
        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Perform fixed splitting and inject audit info into metadata.
        """
        chunks = super()._do_split(doc)

        audit_info = {
            "processed_at": time.time(),
            "original_length": len(doc.content),
            "splitter_version": "1.0.0",
        }

        for chunk in chunks:
            chunk.update_metadata(audit=audit_info)

        return chunks
