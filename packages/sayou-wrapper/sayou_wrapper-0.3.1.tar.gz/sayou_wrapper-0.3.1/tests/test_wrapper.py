import unittest

from sayou.core.vocabulary import SayouClass, SayouPredicate

from sayou.wrapper.pipeline import WrapperPipeline


class TestWrapperPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = WrapperPipeline()
        self.pipeline.initialize()

    def test_topic_conversion(self):
        """헤더(is_header=True)가 Topic 노드로 변환되는지 확인"""
        chunk = {
            "content": "# Heading",
            "metadata": {
                "chunk_id": "test_h1",
                "semantic_type": "h1",
                "is_header": True,
            },
        }
        output = self.pipeline.run([chunk], strategy="document_chunk")

        node = output.nodes[0]
        self.assertEqual(node.node_class, SayouClass.TOPIC)
        self.assertEqual(node.node_id, "sayou:doc:test_h1")

    def test_table_conversion(self):
        """테이블(semantic_type='table')이 Table 노드로 변환되는지 확인"""
        chunk = {
            "content": "| Col |",
            "metadata": {"chunk_id": "test_t1", "semantic_type": "table"},
        }
        output = self.pipeline.run([chunk], strategy="document_chunk")

        self.assertEqual(output.nodes[0].node_class, SayouClass.TABLE)

    def test_relationships(self):
        """부모-자식 관계가 올바른 Predicate로 연결되는지 확인"""
        chunk = {
            "content": "Child text",
            "metadata": {"chunk_id": "child_1", "parent_id": "parent_1"},
        }
        output = self.pipeline.run([chunk], strategy="document_chunk")

        node = output.nodes[0]
        rels = node.relationships

        self.assertIn(SayouPredicate.HAS_PARENT, rels)
        self.assertEqual(rels[SayouPredicate.HAS_PARENT][0], "sayou:doc:parent_1")


if __name__ == "__main__":
    unittest.main()
