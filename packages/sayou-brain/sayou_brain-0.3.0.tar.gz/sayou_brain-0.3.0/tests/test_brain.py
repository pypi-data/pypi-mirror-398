import json
import os
import shutil
import unittest

from sayou.brain.pipelines.standard import StandardPipeline


class TestStandardPipeline(unittest.TestCase):
    """
    StandardPipeline(Brain) 통합 테스트 (v0.3.0 Final)
    """

    def setUp(self):
        # 1. 테스트 환경 초기화
        self.test_base_dir = "tests_sayou_brain_final"
        if os.path.exists(self.test_base_dir):
            shutil.rmtree(self.test_base_dir)
        os.makedirs(self.test_base_dir, exist_ok=True)

        # 2. 소스 파일 생성
        self.source_file = os.path.join(self.test_base_dir, "test_doc.md")
        content = (
            "# Main Title\n\n"
            "This is the introduction.\n\n"
            "## Section 1\n"
            "This is the content of section 1."
        )
        with open(self.source_file, "w", encoding="utf-8") as f:
            f.write(content)

        self.dest_file = os.path.join(self.test_base_dir, "result_output.json")

        self.pipeline = StandardPipeline()

    def tearDown(self):
        if os.path.exists(self.test_base_dir):
            shutil.rmtree(self.test_base_dir)

    def test_full_ingestion_flow(self):
        """
        [Scenario] .md 파일 -> Auto Routing -> JSON 파일 생성 검증
        """
        print(f"\n[Test] Ingesting {self.source_file} -> {self.dest_file} ...")

        stats = self.pipeline.ingest(
            source=self.source_file,
            destination=self.dest_file,
            chunk_size=100,
        )

        print(f"[Test Stats] {stats}")

        # 1. 통계 검증
        self.assertEqual(stats["processed"], 1, "Processing count should be 1")

        # 2. 파일 생성 확인
        if not os.path.exists(self.dest_file):
            print(f"Directory listing: {os.listdir(self.test_base_dir)}")

        self.assertTrue(
            os.path.exists(self.dest_file),
            f"Output file not found at: {self.dest_file}",
        )

        # 3. 데이터 구조 검증
        with open(self.dest_file, "r", encoding="utf-8") as f:
            result_data = json.load(f)

        self.assertIn("nodes", result_data)
        nodes = result_data["nodes"]
        self.assertTrue(len(nodes) > 0, "Nodes list is empty")

        # 4. 내용 검증
        first_node = nodes[0]
        print(json.dumps(first_node, indent=2, ensure_ascii=False))

        attributes = first_node.get("attributes", {})
        has_text = len(attributes.get("schema:text", "")) > 0
        has_title = len(first_node.get("friendly_name", "")) > 0

        self.assertTrue(has_text or has_title, "Node has no content.")


if __name__ == "__main__":
    unittest.main()
