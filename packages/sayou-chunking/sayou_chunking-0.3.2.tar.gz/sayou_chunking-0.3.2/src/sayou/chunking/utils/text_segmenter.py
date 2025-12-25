import re
from typing import List


class TextSegmenter:
    """
    (Utility) A stateless engine for regex-based text segmentation.

    Provides core logic for recursive splitting while respecting 'protected'
    blocks (like tables or code snippets) that should not be fragmented.
    """

    @staticmethod
    def split_with_protection(
        text: str,
        separators: List[str],
        protected_patterns: List[str],
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        """
        Split text while preserving specific patterns intact.

        1. Identifies blocks matching `protected_patterns` (e.g., Tables).
        2. Isolates them so they are not split.
        3. Recursively splits the remaining text using `separators`.

        Args:
            text (str): The text to split.
            separators (List[str]): List of separators in order of precedence.
            protected_patterns (List[str]): Regex patterns to protect from splitting.
            chunk_size (int): Target size for each chunk.
            chunk_overlap (int): Number of overlapping characters.

        Returns:
            List[str]: A list of text segments.
        """
        if not text:
            return []

        if not protected_patterns:
            return TextSegmenter.recursive_split(
                text, separators, chunk_size, chunk_overlap
            )

        combined_pattern = f"({'|'.join(protected_patterns)})"
        parts = re.split(combined_pattern, text, flags=re.MULTILINE | re.DOTALL)

        final_chunks = []
        for i, part in enumerate(parts):
            if not part:
                continue
            if i % 2 == 1:
                final_chunks.append(part)
            else:
                sub_chunks = TextSegmenter.recursive_split(
                    part, separators, chunk_size, chunk_overlap
                )
                final_chunks.extend(sub_chunks)
        return final_chunks

    @staticmethod
    def recursive_split(
        text: str,
        separators: List[str],
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        """
        Recursively split text using a list of separators.

        Tries to split by the first separator. If chunks are still too large,
        it moves to the next separator in the list.

        Args:
            text (str): The text to split.
            separators (List[str]): Separators (e.g., ["\n\n", "\n", " "]).
            chunk_size (int): Maximum size of a chunk.
            chunk_overlap (int): Overlap size.

        Returns:
            List[str]: A list of text segments.
        """
        if len(text) <= chunk_size:
            return [text]

        # -------------------------------------------------------------------------
        # Prevent 'character-based decomposition'
        # -------------------------------------------------------------------------
        def safe_slice(txt, size, overlap):
            step = size - overlap
            return [txt[i : i + size] for i in range(0, len(txt), step)]

        if not separators:
            print(f"✂️ [Force Slice] No separators left. Slicing {len(text)} chars.")
            return safe_slice(text, chunk_size, chunk_overlap)

        separator = separators[0]
        next_separators = separators[1:]

        if separator == "":
            return safe_slice(text, chunk_size, chunk_overlap)

        # -------------------------------------------------------------------------
        # Verify text identity (identify cause of delimiter failure)
        # -------------------------------------------------------------------------
        try:
            splits = re.split(f"({separator})", text)
        except Exception:
            splits = [text]

        # Cause analysis log when segmentation fails
        if len(splits) == 1 and len(text) > chunk_size:
            snippet = repr(text[:50])
            print(f"⚠️ [Split Failed] Sep='{separator}' failed on text start: {snippet}")

            return TextSegmenter.recursive_split(
                text, next_separators, chunk_size, chunk_overlap
            )

        # -------------------------------------------------------------------------
        # Merge split results
        # -------------------------------------------------------------------------
        final_chunks = []
        current_doc = []
        total_len = 0

        for i, split in enumerate(splits):
            if not split:
                continue

            is_separator = i % 2 == 1

            if is_separator:
                if current_doc:
                    current_doc[-1] += split
                continue

            split_len = len(split)

            if total_len + split_len > chunk_size:
                if current_doc:
                    final_chunks.append("".join(current_doc))
                    current_doc = []
                    total_len = 0

                if split_len > chunk_size:
                    sub_chunks = TextSegmenter.recursive_split(
                        split, next_separators, chunk_size, chunk_overlap
                    )
                    final_chunks.extend(sub_chunks)
                else:
                    current_doc.append(split)
                    total_len += split_len
            else:
                current_doc.append(split)
                total_len += split_len

        if current_doc:
            final_chunks.append("".join(current_doc))

        return final_chunks
