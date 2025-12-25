from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouOutput

from ..interfaces.base_builder import BaseBuilder


@register_component("builder")
class GraphBuilder(BaseBuilder):
    """
    Assembles SayouNodes into a standard Graph Structure (Nodes + Edges).

    Suitable for loading into graph databases (like NetworkX) or visualization.
    Automatically generates reverse relationships (e.g., hasParent -> hasChild)
    to ensure bi-directional traversal capabilities.
    """

    component_name = "GraphBuilder"
    SUPPORTED_TYPES = ["graph", "hierarchy"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if isinstance(input_data, SayouOutput) or (
            isinstance(input_data, dict) and "nodes" in input_data
        ):
            return 0.9

        return 0.0

    def _do_build(self, data: SayouOutput) -> Dict[str, Any]:
        """
        Convert Nodes and Relationships into a flat Node/Edge list dictionary.
        """
        nodes_map = {}
        edges_list = []

        # 1. Node Processing
        for node in data.nodes:
            # Pydantic model_dump를 사용하여 순수 dict로 변환
            n_dict = node.model_dump()
            # relationships는 엣지로 변환되므로 노드 속성에서는 제외
            n_dict.pop("relationships", None)

            nodes_map[node.node_id] = n_dict

            # 2. Edge Processing (Forward & Reverse)
            source_id = node.node_id
            for rel_type, targets in node.relationships.items():
                if isinstance(targets, str):
                    targets = [targets]

                for target_id in targets:
                    # 정방향 엣지
                    edges_list.append(
                        {
                            "source": source_id,
                            "target": target_id,
                            "type": rel_type,
                            "is_reverse": False,
                        }
                    )

                    # 역방향 엣지 생성
                    rev_type = self._get_reverse_type(rel_type)
                    edges_list.append(
                        {
                            "source": target_id,
                            "target": source_id,
                            "type": rev_type,
                            "is_reverse": True,
                        }
                    )

        return {
            "nodes": list(nodes_map.values()),
            "edges": edges_list,
            "metadata": data.metadata,
            "stats": {"node_count": len(nodes_map), "edge_count": len(edges_list)},
        }

    def _get_reverse_type(self, rel_type: str) -> str:
        """
        Determine the name of the reverse relationship.
        e.g., 'sayou:hasParent' -> 'sayou:hasChild'.
        """
        if "hasParent" in rel_type:
            return "sayou:hasChild"
        if "belongsTo" in rel_type:
            return "sayou:contains"
        if "next" in rel_type:
            return "sayou:previous"
        return f"{rel_type}_REV"
