from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter
from ..splitter.recursive_splitter import RecursiveSplitter
from ..splitter.structure_splitter import StructureSplitter


@register_component("splitter")
class ParentDocumentSplitter(BaseSplitter):
    """
    Parent-Child Chunking Strategy.

    Creates larger 'Parent' chunks to preserve context, and smaller 'Child'
    chunks for precise retrieval. The child chunks link back to their parent.
    """

    component_name = "ParentDocumentSplitter"
    SUPPORTED_TYPES = ["parent_document"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["parent_document"]:
            return 1.0
        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Generate parent chunks first, then recursively split them into children.
        """
        config = doc.metadata.get("config", {})

        parent_strategy = config.get("parent_strategy", "recursive")

        if parent_strategy == "structure":
            parent_splitter = StructureSplitter()
        else:
            parent_splitter = RecursiveSplitter()

        child_splitter = RecursiveSplitter()

        final_chunks = []

        parent_config = config.copy()
        parent_config["chunk_size"] = config.get("parent_chunk_size", 2000)

        parent_doc = SayouBlock(
            type=doc.type,
            content=doc.content,
            metadata={**doc.metadata, "config": parent_config},
        )

        parent_chunks = parent_splitter._do_split(parent_doc)

        for p_idx, p_chunk in enumerate(parent_chunks):
            doc_id = doc.metadata.get("id", "doc")
            parent_id = f"{doc_id}_parent_{p_idx}"

            p_chunk.update_metadata(chunk_id=parent_id, doc_level="parent")
            final_chunks.append(p_chunk)

            child_doc = SayouBlock(
                type=doc.type,
                content=p_chunk.content,
                metadata={**doc.metadata, "config": config, "parent_id": parent_id},
            )
            child_chunks = child_splitter._do_split(child_doc)

            child_ids_list = []
            for c_idx, c_chunk in enumerate(child_chunks):
                child_id = f"{parent_id}_c{c_idx}"
                child_ids_list.append(child_id)

                c_chunk.update_metadata(
                    chunk_id=child_id,
                    part_index=c_idx,
                    doc_level="child",
                    parent_id=parent_id,
                )
                final_chunks.append(c_chunk)

            p_chunk.update_metadata(child_ids=child_ids_list)

        return final_chunks
