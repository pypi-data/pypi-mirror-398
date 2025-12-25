# sayou-chunking

[![PyPI version](https://img.shields.io/pypi/v/sayou-chunking.svg?color=blue)](https://pypi.org/project/sayou-chunking/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/chunking/)


**The Intelligent Text Splitter for Sayou Fabric.**

`sayou-chunking` splits large texts into smaller, semantically meaningful units called **Chunks**. This is a critical step for RAG (Retrieval-Augmented Generation) systems, as it directly impacts retrieval accuracy.

It goes beyond simple character splitting by offering structure-aware, semantic, and hierarchical chunking strategies.

## 💡 Core Philosophy

**"Context is King."**

Blindly cutting text at 500 characters breaks sentences and loses meaning. `sayou-chunking` aims to preserve context by:

1.  **Structure Awareness:** Respects document headers, tables, and code blocks (especially in Markdown).
2.  **Semantic Coherence:** Groups sentences that belong to the same topic using similarity metrics.
3.  **Hierarchy:** Maintains Parent-Child relationships to retrieve small precise chunks while providing large context to the LLM.

## 📦 Installation

```bash
pip install sayou-chunking
```

## ⚡ Quick Start

The `ChunkingPipeline` provides a unified interface for various splitting strategies.

```python
from sayou.chunking.pipeline import ChunkingPipeline

def run_demo():
    # 1. Initialize Pipeline
    pipeline = ChunkingPipeline()
    pipeline.initialize()

    # 2. Prepare Input (e.g., from Refinery)
    text_content = """
    # Section 1: Introduction
    Chunking is the process of breaking text down.
    
    ## Benefits
    - Better Retrieval
    - Context Preservation
    """
    
    request = {
        "content": text_content,
        "metadata": {"source": "doc.md"},
        "config": {"chunk_size": 50}
    }

    # 3. Run with Strategy ('markdown', 'recursive', 'semantic', etc.)
    chunks = pipeline.run(request, strategy="markdown")

    # 4. Result
    for i, chunk in enumerate(chunks):
        print(f"[{i}] Type: {chunk.metadata.get('semantic_type')}")
        print(f"    Content: {chunk.content}")

if __name__ == "__main__":
    run_demo()
```

## 🔑 Key Components

### Splitter
* **`RecursiveSplitter`**: The standard strategy. Splits by paragraph -> line -> sentence -> word to keep related text together.
* **`MarkdownSplitter`**: Aware of Markdown syntax. Splits by headers (#) first, protecting tables and code blocks.
* **`FixedLengthSplitter`**: Hard split by character count. Useful when strict token limits are required.
* **`StructureSplitter`**: Splits based on user-defined regex patterns (e.g., "Article \d+").
* **`SemanticSplitter`**: Uses cosine similarity between sentences to find topic breakpoints.
* **`ParentDocumentSplitter`**: Creates large "Parent" chunks for context and small "Child" chunks for retrieval, linking them together.

## 🤝 Contributing

We welcome contributions for New Strategies (e.g., `CodeSplitter` for Python/JS) or Integrations with other embedding models for Semantic Splitting.

## 📜 License

Apache 2.0 License © 2025 Sayouzone