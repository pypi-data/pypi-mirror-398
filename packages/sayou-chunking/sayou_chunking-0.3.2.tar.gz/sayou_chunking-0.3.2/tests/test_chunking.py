import unittest

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.markdown_splitter import MarkdownSplitter


class TestChunkingPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = ChunkingPipeline(extra_splitters=[MarkdownSplitter])
        self.pipeline.initialize()

    def test_recursive_splitter(self):
        """기본 재귀 분할 테스트"""
        text = "Hello.\n\nWorld.\nThis is a test."
        chunks = self.pipeline.run(
            {"content": text, "config": {"chunk_size": 10}}, strategy="recursive"
        )
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].content, "Hello.")

    def test_markdown_splitter(self):
        """마크다운 헤더 분할 테스트"""
        text = "# Header 1\nContent 1\n## Header 2\nContent 2"
        chunks = self.pipeline.run({"content": text}, strategy="markdown")

        # H1, H2 헤더가 각각 별도 청크로 잡혀야 함
        headers = [c for c in chunks if c.metadata.get("is_header")]
        self.assertEqual(len(headers), 2)
        self.assertEqual(headers[0].metadata["semantic_type"], "h1")

    def test_fixed_length_splitter(self):
        """고정 길이 분할 테스트"""
        text = "1234567890"
        chunks = self.pipeline.run(
            {"content": text, "config": {"chunk_size": 5, "chunk_overlap": 0}},
            strategy="fixed_length",
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].content, "12345")
        self.assertEqual(chunks[1].content, "67890")

    def test_parent_document_splitter(self):
        """부모-자식 관계 생성 테스트"""
        text = "Parent Content " * 100
        chunks = self.pipeline.run(
            {"content": text, "config": {"parent_chunk_size": 500, "chunk_size": 50}},
            strategy="parent_document",
        )

        parents = [c for c in chunks if c.metadata.get("doc_level") == "parent"]
        children = [c for c in chunks if c.metadata.get("doc_level") == "child"]

        self.assertTrue(len(parents) > 0)
        self.assertTrue(len(children) > 0)
        # 자식이 부모 ID를 가지고 있는지 확인
        self.assertEqual(
            children[0].metadata["parent_id"], parents[0].metadata["chunk_id"]
        )


if __name__ == "__main__":
    unittest.main()
