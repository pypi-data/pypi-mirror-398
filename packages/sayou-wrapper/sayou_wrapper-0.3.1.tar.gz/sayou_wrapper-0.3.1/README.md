# sayou-wrapper

[![PyPI version](https://img.shields.io/pypi/v/sayou-wrapper.svg?color=blue)](https://pypi.org/project/sayou-wrapper/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/wrapper/)

**The Ontology Mapper for Sayou Fabric.**

`sayou-wrapper` takes the fragmented chunks produced by `sayou-chunking` and wraps them into a standardized graph structure (**SayouNode**). This is the final preparation step before data is assembled into a Knowledge Graph or loaded into a Vector DB.

It applies the **Sayou Ontology Schema** (Namespace -> Class -> Predicate) to raw data, turning simple text into semantically rich entities.

## 💡 Core Philosophy

**"From Data to Knowledge."**

While Chunking slices the data, Wrapper gives it meaning.
* It assigns **Ontology Classes** (e.g., `sayou:Topic`, `sayou:Table`) based on metadata.
* It defines **Relationships** (e.g., `sayou:hasParent`) to preserve context.
* It normalizes IDs into **URIs** (e.g., `sayou:doc:123`) for global uniqueness.

## 📦 Installation

```bash
pip install sayou-wrapper
```

## ⚡ Quick Start

```python
from sayou.wrapper.pipeline import WrapperPipeline

def run_demo():
    # 1. Initialize
    pipeline = WrapperPipeline()
    pipeline.initialize()

    # 2. Input Data (Simulated output from sayou-chunking)
    chunks = [
        {
            "content": "# Introduction",
            "metadata": {
                "chunk_id": "h_1", 
                "semantic_type": "heading", 
                "is_header": True
            }
        },
        {
            "content": "Sayou is great.",
            "metadata": {
                "chunk_id": "p_1", 
                "parent_id": "h_1",
                "semantic_type": "text"
            }
        }
    ]

    # 3. Run Wrapper
    output = pipeline.run(chunks, strategy="document_chunk")

    # 4. Result (SayouNodes)
    for node in output.nodes:
        print(f"[{node.node_class}] {node.node_id}")
        print(f"   Attrs: {node.attributes}")
        print(f"   Rels : {node.relationships}")

if __name__ == "__main__":
    run_demo()
```

## 🔑 Key Components

### Adapters
* **`DocumentChunkAdapter`**: The standard adapter. Converts document chunks into `sayou:Topic`, `sayou:TextFragment`, etc., and links them via `sayou:hasParent`.

### Schema (Sayouzone Standard)
* **`SayouNode`**: The atomic unit of the Knowledge Graph. Contains ID, Class, Attributes, and Relationships.
* **`WrapperOutput`**: A container holding a list of nodes and global metadata.

## 🤝 Contributing

We welcome adapters for other data sources (e.g., `SqlRecordAdapter`, `LogAdapter`).

## 📜 License

Apache 2.0 License © 2025 Sayouzone