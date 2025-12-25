import logging
from typing import List

from sayou.assembler.pipeline import AssemblerPipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")


def dummy_embedding_fn(text: str) -> List[float]:
    """(Mock) 텍스트 길이 기반 더미 임베딩 함수"""
    val = float(len(text))
    return [val, val * 0.1, val * 0.2]


def run_demo():
    print(">>> Initializing Sayou Assembler Pipeline...")

    pipeline = AssemblerPipeline()
    pipeline.initialize(embedding_fn=dummy_embedding_fn)

    dummy_input = {
        "metadata": {"source": "demo_doc.pdf"},
        "nodes": [
            {
                "node_id": "sayou:doc:1_h_0",
                "node_class": "sayou:Topic",
                "friendly_name": "Introduction",
                "attributes": {"schema:text": "Introduction Header"},
                "relationships": {},
            },
            {
                "node_id": "sayou:doc:1_p_0",
                "node_class": "sayou:TextFragment",
                "attributes": {"schema:text": "This is the content paragraph."},
                "relationships": {"sayou:hasParent": ["sayou:doc:1_h_0"]},
            },
        ],
    }

    # import json
    # import os
    # input_path = os.path.join("examples", "wrapper_output_demo.json")
    # with open(input_path, "r", encoding="utf-8") as f:
    #     dummy_input = json.load(f)

    print(f"\n--- [1] Strategy: Graph (Default) ---")
    graph_result = pipeline.run(dummy_input, strategy="hierarchy")

    print(f"Debug Type: {type(graph_result)}")
    print(f"✅ Nodes: {len(graph_result['nodes'])}")
    print(f"✅ Edges: {len(graph_result['edges'])} (Forward + Reverse)")

    print("\n[Edges Sample]")
    for edge in graph_result["edges"]:
        direction = "<--" if edge.get("is_reverse") else "-->"
        print(
            f"{edge['source']} {direction} [{edge['type']}] {direction} {edge['target']}"
        )

    print(f"\n--- [2] Strategy: Vector ---")
    vector_result = pipeline.run(dummy_input, strategy="vector")

    print(f"✅ Generated {len(vector_result)} payloads")
    if vector_result:
        sample = vector_result[1]
        print(f"Sample ID: {sample['id']}")
        print(f"Vector: {sample['vector']}")
        print(f"Metadata Keys: {list(sample['metadata'].keys())}")

    print(f"\n--- [3] Strategy: Neo4j Cypher ---")

    from sayou.assembler.plugins.cypher_builder import CypherBuilder

    cypher_builder = CypherBuilder()
    pipeline = AssemblerPipeline(extra_builders=[cypher_builder])
    pipeline.initialize()

    cypher_queries = pipeline.run(dummy_input, strategy="cypher")

    print(f"✅ Generated {len(cypher_queries)} queries")
    for q in cypher_queries[:2]:
        print(f"Q: {q}")

    # output_dir = "examples"
    # os.makedirs(output_dir, exist_ok=True)
    # with open(os.path.join(output_dir, "knowledge_graph_demo.json"), "w", encoding="utf-8") as f:
    #     json.dump(cypher_queries, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    run_demo()
