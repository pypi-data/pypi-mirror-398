import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY
from sayou.core.schemas import SayouBlock, SayouChunk

from .core.exceptions import SplitterError
from .interfaces.base_splitter import BaseSplitter


class ChunkingPipeline(BaseComponent):
    """
    Orchestrates the text chunking process via dynamic registry.

    This pipeline acts as a factory and dispatcher, routing input data
    to the most appropriate splitter strategy (Recursive, Semantic, Markdown, etc.)
    based on 'can_handle' scores or explicit strategy requests.
    """

    component_name = "ChunkingPipeline"

    def __init__(
        self,
        extra_splitters: Optional[List[Type[BaseSplitter]]] = None,
        **kwargs,
    ):
        """
        Initialize the pipeline and discover available splitters.

        Args:
            extra_splitters: List of custom splitter CLASSES (not instances).
            **kwargs: Global configuration.
        """
        super().__init__()

        self.splitters_cls_map: Dict[str, Type[BaseSplitter]] = {}

        self._register("sayou.chunking.splitter")
        self._register("sayou.chunking.plugins")

        self._load_from_registry()

        if extra_splitters:
            for cls in extra_splitters:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid splitter: {cls}. "
                f"Please pass the CLASS itself (e.g., MySplitter), not an instance (MySplitter())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.splitters_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> List[SayouChunk]:
        """
        [Facade] One-line execution method.

        Instantiates the pipeline and runs the chunking process immediately.

        Args:
            input_data (Any): Input text or data structure to chunk.
            strategy (str): Splitting strategy hint (default: 'auto').
            **kwargs: Configuration options (chunk_size, etc.).

        Returns:
            List[SayouChunk]: A list of generated text chunks.
        """
        instance = cls(**kwargs)
        return instance.run(input_data, strategy, **kwargs)

    def _register(self, package_name: str):
        """
        Automatically discovers and registers plugins from the specified package.

        Args:
            package_name (str): The dot-separated package path.
        """
        try:
            package = importlib.import_module(package_name)
            if hasattr(package, "__path__"):
                for _, name, _ in pkgutil.iter_modules(package.__path__):
                    full_name = f"{package_name}.{name}"
                    try:
                        importlib.import_module(full_name)
                        self._log(f"Discovered module: {full_name}", level="debug")
                    except Exception as e:
                        self._log(
                            f"Failed to import module {full_name}: {e}", level="warning"
                        )
        except ImportError as e:
            self._log(f"Package not found: {package_name} ({e})", level="debug")

    def _load_from_registry(self):
        """
        Populates local component maps from the global registry.
        """
        if "splitter" in COMPONENT_REGISTRY:
            self.splitters_cls_map.update(COMPONENT_REGISTRY["splitter"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all sub-components (Splitters).

        Updates global configuration and logs status.
        Actual component instantiation happens lazily during run().

        Args:
            **kwargs: Updates to the global configuration.
        """
        self.global_config.update(kwargs)

        n_split = len(self.splitters_cls_map)
        self._log(f"ChunkingPipeline initialized. Available: {n_split} Splitters")

    def run(
        self,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> List[SayouChunk]:
        """
        Execute the chunking strategy on the input data.

        Orchestration Flow:
        1. Merge Configurations (Global + Runtime).
        2. Resolve Splitter (Strategy > Score).
        3. Instantiate & Initialize Splitter.
        4. Execute Splitter.

        Args:
            input_data (Any): Text string, Dict, or SayouBlock list.
            strategy (str): The splitting strategy to use (default: 'auto').
            **kwargs: Runtime configuration options.

        Returns:
            List[SayouChunk]: A list of generated Chunk objects.

        Raises:
            SplitterError: If no suitable splitter is found or execution fails.
        """
        if not input_data:
            return []

        # 1. Config Merge
        run_config = {**self.global_config, **kwargs}
        self._emit("on_start", input_data={"strategy": strategy})

        # ----------------------------------------------------------------------
        # 2. Flattening & Content Extraction (The Critical Fix)
        # ----------------------------------------------------------------------

        raw_items = input_data if isinstance(input_data, list) else [input_data]
        flattened_blocks: List[SayouBlock] = []

        def _extract_and_flatten(item: Any, parent_meta: dict = None):
            """Helper to recursively extract content and maintain metadata."""
            if parent_meta is None:
                parent_meta = {}

            # Case A: List -> Recurse
            if isinstance(item, list):
                for sub in item:
                    _extract_and_flatten(sub, parent_meta)
                return

            # Case B: Dict -> Extract keys -> Recurse or Create Block
            if isinstance(item, dict):
                content = item.get("content")
                current_meta = parent_meta.copy()
                current_meta.update(item.get("metadata", {}))

                doc_type = item.get("type", "text")

                if isinstance(content, list):
                    _extract_and_flatten(content, current_meta)
                elif content:
                    flattened_blocks.append(
                        SayouBlock(
                            content=str(content), metadata=current_meta, type=doc_type
                        )
                    )
                return

            # Case C: SayouBlock -> Check content
            if isinstance(item, SayouBlock):
                if isinstance(item.content, list):
                    _extract_and_flatten(item.content, item.metadata)
                else:
                    flattened_blocks.append(item)
                return

            # Case D: String -> Create Block
            if isinstance(item, str) and item.strip():
                flattened_blocks.append(
                    SayouBlock(content=item, metadata=parent_meta, type="text")
                )

        for raw in raw_items:
            try:
                _extract_and_flatten(raw)
            except Exception as e:
                self._log(f"❌ Error during flattening: {e}", level="error")

        self._log(
            f"🔎 [PIPELINE] Flattened input into {len(flattened_blocks)} clean blocks."
        )

        # ----------------------------------------------------------------------
        # 3. Process Flattened Blocks
        # ----------------------------------------------------------------------
        all_results = []

        for i, target_block in enumerate(flattened_blocks):
            if not target_block.content:
                continue

            splitter_cls = self._resolve_splitter(target_block, strategy)

            if not splitter_cls:
                self._log(
                    f"⚠️ No suitable splitter for item {i}. Preserving.", level="warning"
                )
                all_results.append(
                    SayouChunk(
                        content=target_block.content,
                        metadata={**target_block.metadata, "error": "no_splitter"},
                    )
                )
                continue

            self._log(
                f"Routing Item {i} ({target_block.type}) -> {splitter_cls.component_name}"
            )

            splitter = splitter_cls()
            splitter.initialize(**run_config)

            try:
                chunks = splitter.split(target_block)

                if isinstance(chunks, list):
                    all_results.extend(chunks)
                else:
                    all_results.append(chunks)

            except Exception as e:
                self._log(f"❌ Splitter Execution Failed: {e}", level="error")
                self._emit("on_error", error=e)
                all_results.append(
                    SayouChunk(
                        content=target_block.content,
                        metadata={
                            "error": str(e),
                            "failed_splitter": splitter.component_name,
                        },
                    )
                )

        self._log(f"🔎 [PIPELINE] Finished. Generated {len(all_results)} chunks.")

        for idx, res in enumerate(all_results):
            if not hasattr(res, "model_dump"):
                self._log(
                    f"🚨 [CRITICAL] Result {idx} is NOT a Pydantic model! Type: {type(res)}",
                    level="error",
                )

        self._emit(
            "on_finish", result_data={"chunks_count": len(all_results)}, success=True
        )

        return all_results

    def _is_valid_item(self, item: Any) -> bool:
        if isinstance(item, (SayouBlock, SayouChunk)):
            return bool(item.content)
        if isinstance(item, dict):
            return "content" in item
        if isinstance(item, str):
            return True
        return False

    def _resolve_splitter(
        self,
        raw_data: Any,
        strategy: str,
    ) -> Optional[Type[BaseSplitter]]:
        """
        Selects the best splitter based on score or explicit type match.

        Args:
            raw_data (Any): The input data to evaluate.
            strategy (str): The requested strategy name.

        Returns:
            Optional[Type[BaseSplitter]]: The selected splitter class or None.
        """
        if strategy in self.splitters_cls_map:
            return self.splitters_cls_map[strategy]

        best_score = 0.0
        best_cls = None

        log_lines = [
            f"Scoring for Item (Type: {raw_data.type}, Len: {len(raw_data.content)}):",
            f"Content: {raw_data.content[:30]}",
        ]

        for cls in set(self.splitters_cls_map.values()):
            try:
                score = cls.can_handle(raw_data, strategy)

                mark = ""
                if score > best_score:
                    best_score = score
                    best_cls = cls
                    mark = "👑"

                log_lines.append(f"   - {cls.__name__}: {score} {mark}")

            except Exception as e:
                log_lines.append(f"   - {cls.__name__}: Error ({e})")

        self._log("\n".join(log_lines))

        if best_cls and best_score > 0.0:
            return best_cls

        self._log(
            "⚠️ No suitable splitter found (Score 0). Fallback to RecursiveSplitter.",
            level="warning",
        )
        return None
