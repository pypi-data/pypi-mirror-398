import math
from typing import Any, Callable, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter


@register_component("splitter")
class SemanticSplitter(BaseSplitter):
    """
    Semantic Similarity Splitter.

    Identifies breakpoints where the topic changes by calculating the
    cosine similarity between adjacent sentences.
    """

    component_name = "SemanticSplitter"
    SUPPORTED_TYPES = ["semantic"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["semantic"]:
            return 1.0
        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Segment text based on semantic coherence.
        """
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")

        # 전처리: 문장 분리 (단순화된 버전)
        sentences = [
            s.strip() for s in doc.content.replace("\n", ". ").split(". ") if s.strip()
        ]
        if not sentences:
            return []

        # 인코더 (기본값: 단순 빈도수 기반)
        encoder = config.get("encoder_function", self._simple_frequency_encoder)
        threshold = config.get("semantic_threshold", 0.5)

        # 그룹핑 실행
        grouped_texts = self._cluster_sentences(sentences, encoder, threshold)

        return [
            SayouChunk(
                content=text,
                metadata={
                    **doc.metadata,
                    "chunk_id": f"{doc_id}_{i}",
                    "semantic_type": "semantic_group",
                },
            )
            for i, text in enumerate(grouped_texts)
        ]

    def _cluster_sentences(
        self, sentences: List[str], encoder: Callable, threshold: float
    ) -> List[str]:
        """
        Group sentences together until similarity drops below `threshold`.
        """
        if len(sentences) < 2:
            return sentences
        vectors = [encoder(s) for s in sentences]
        groups = []
        current_group = [sentences[0]]

        for i in range(len(vectors) - 1):
            sim = self._cosine_similarity(vectors[i], vectors[i + 1])
            if sim < threshold:
                groups.append(". ".join(current_group) + ".")
                current_group = [sentences[i + 1]]
            else:
                current_group.append(sentences[i + 1])
        if current_group:
            groups.append(". ".join(current_group) + ".")
        return groups

    def _simple_frequency_encoder(self, text: str) -> List[float]:
        """
        [Mock] A dummy encoder based on character frequency.
        Should be replaced by a real embedding model in production.
        """
        vec = [0.0] * 10
        for char in text:
            vec[ord(char) % 10] += 1.0
        mag = math.sqrt(sum(x * x for x in vec))
        return [x / mag if mag else 0 for x in vec]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        """
        return sum(a * b for a, b in zip(v1, v2))
