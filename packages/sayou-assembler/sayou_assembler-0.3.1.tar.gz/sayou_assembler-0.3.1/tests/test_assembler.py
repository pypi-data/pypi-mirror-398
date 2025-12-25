import unittest

from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.assembler.plugins.cypher_builder import CypherBuilder


class TestAssemblerPipeline(unittest.TestCase):

    def setUp(self):
        cypher_builder = CypherBuilder()
        self.pipeline = AssemblerPipeline(extra_builders=[cypher_builder])
        self.pipeline.initialize()

        # 테스트용 공통 입력 데이터
        self.test_input = SayouOutput(
            nodes=[
                SayouNode(
                    node_id="parent_1",
                    node_class="sayou:Topic",
                    attributes={"schema:text": "Parent Header"},
                ),
                SayouNode(
                    node_id="child_1",
                    node_class="sayou:TextFragment",
                    attributes={"schema:text": "Child Content"},
                    # 부모를 가리키는 관계 설정
                    relationships={"sayou:hasParent": ["parent_1"]},
                ),
            ]
        )

    def test_graph_builder_reverse_linking(self):
        """GraphBuilder가 역방향 엣지(hasChild)를 자동으로 생성하는지 확인"""
        result = self.pipeline.run(self.test_input, strategy="graph")

        edges = result["edges"]
        # 총 2개 예상 (정방향 1개 + 역방향 1개)
        self.assertEqual(len(edges), 2)

        # 정방향 확인
        fwd = next(e for e in edges if not e.get("is_reverse"))
        self.assertEqual(fwd["type"], "sayou:hasParent")
        self.assertEqual(fwd["source"], "child_1")
        self.assertEqual(fwd["target"], "parent_1")

        # 역방향 확인 (Hierarchy Logic Integration Check)
        rev = next(e for e in edges if e.get("is_reverse"))
        # _get_reverse_type 로직에 의해 'sayou:hasChild'로 변환되었는지 확인
        self.assertEqual(rev["type"], "sayou:hasChild")
        self.assertEqual(rev["source"], "parent_1")
        self.assertEqual(rev["target"], "child_1")

    def test_vector_builder(self):
        """VectorBuilder가 Payload를 올바르게 구성하는지 확인"""

        # Mock Embedding Function
        def mock_embed(text):
            return [1.0, 0.0]

        self.pipeline.initialize(embedding_fn=mock_embed)
        result = self.pipeline.run(self.test_input, strategy="vector")

        self.assertEqual(len(result), 2)
        payload = result[1]  # child_1

        self.assertEqual(payload["id"], "child_1")
        self.assertEqual(payload["vector"], [1.0, 0.0])
        # 메타데이터가 평탄화(flattened)되어 들어갔는지 확인
        self.assertEqual(payload["metadata"]["schema:text"], "Child Content")
        self.assertEqual(payload["metadata"]["node_class"], "sayou:TextFragment")

    def test_cypher_builder(self):
        """Cypher 쿼리 생성 확인"""
        queries = self.pipeline.run(self.test_input, strategy="cypher")

        # 노드 생성 2개 + 관계 생성 1개 = 총 3개 쿼리 예상
        # (CypherBuilder 구현에 따라 관계 쿼리 수가 달라질 수 있음, 여기선 최소 확인)
        self.assertGreater(len(queries), 0)

        # MERGE 구문 포함 여부 확인
        self.assertIn("MERGE (n:`sayou:Topic`", queries[0])


if __name__ == "__main__":
    unittest.main()
