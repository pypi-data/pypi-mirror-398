# sayou-assembler

[![PyPI version](https://img.shields.io/pypi/v/sayou-assembler.svg?color=blue)](https://pypi.org/project/sayou-assembler/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/assembler/)

**The Knowledge Builder for Sayou Fabric.**

`sayou-assembler` is the construction site of the data pipeline. It takes the standardized `SayouNode` objects produced by the Wrapper and assembles them into target-specific formats ready for loading into databases.

It bridges the gap between the abstract data model and concrete storage technologies (Graph DBs, Vector DBs).

## 💡 Core Philosophy

**"Build Once, Deploy Anywhere."**

The Assembler decouples the *structure* of knowledge from the *syntax* of the database.
* **Graph Builder:** Constructs a topology of Nodes and Edges (including automatic reverse linking).
* **Vector Builder:** Transforms nodes into embeddings and metadata payloads.
* **Query Builder:** Generates specific query languages like Cypher or SQL.

## 📦 Installation

```bash
pip install sayou-assembler
```

## ⚡ Quick Start

The `AssemblerPipeline` converts standardized data into database payloads.

```python
from sayou.assembler.pipeline import AssemblerPipeline

def run_demo():
    # 1. Initialize (Inject embedding function for Vector Builder)
    pipeline = AssemblerPipeline()
    pipeline.initialize(embedding_fn=my_embedding_func)

    # 2. Input Data (from sayou-wrapper)
    wrapper_output = {
        "nodes": [
            {"node_id": "doc_1", "node_class": "sayou:Document", "attributes": {"text": "..."}},
            # ...
        ]
    }

    # 3. Build for Graph DB (Nodes + Edges)
    graph_data = pipeline.run(wrapper_output, strategy="graph")
    print(f"Edges created: {len(graph_data['edges'])}")
    
    # 4. Build for Vector DB (Embeddings)
    vector_data = pipeline.run(wrapper_output, strategy="vector")
    print(f"Vectors created: {len(vector_data)}")

if __name__ == "__main__":
    def my_embedding_func(text): return [0.1, 0.2, 0.3] # Dummy
    run_demo()
```

## 🔑 Key Components

### Builders
* **`GraphBuilder`**: Converts nodes into a generic graph structure (Dictionary). Automatically creates reverse edges (e.g., `hasChild` from `hasParent`) to ensure bi-directional traversability.
* **`VectorBuilder`**: Extracts text from nodes, computes embeddings, and formats payloads for Vector DBs.

### Plugins
* **`CypherBuilder`**: Generates Neo4j `MERGE` queries to insert nodes and relationships idempotently.

## 🤝 Contributing

We welcome builders for other targets (e.g., `SqlBuilder`, `GremlinBuilder`).

## 📜 License

Apache 2.0 License © 2025 Sayouzone