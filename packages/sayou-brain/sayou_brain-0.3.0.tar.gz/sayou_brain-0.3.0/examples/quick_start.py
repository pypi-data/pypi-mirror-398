import json
import logging
import os
import sys
from pathlib import Path

import yaml

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = CURRENT_DIR
while not os.path.exists(os.path.join(ROOT_DIR, "packages")):
    parent = os.path.dirname(ROOT_DIR)
    if parent == ROOT_DIR:
        raise FileNotFoundError("'packages' folder not found.")
    ROOT_DIR = parent

PACKAGES_ROOT = os.path.join(ROOT_DIR, "packages")
sys.path.insert(0, os.path.join(PACKAGES_ROOT, "sayou-brain", "."))
sys.path.insert(0, os.path.join(PACKAGES_ROOT, "sayou-chunking", "."))

print(f"[DEBUG] ROOT_DIR: {ROOT_DIR}")
print(f"[DEBUG] Added paths to sys.path for: sayou-core, sayou-document")

from sayou.chunking.plugins.markdown_splitter import MarkdownSplitter

from src.sayou.brain.pipelines.standard import StandardPipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)


def create_input_folder(folder_path="examples/input"):
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    print(f"폴더 '{folder_path}'가 생성되었거나 이미 존재합니다.")


def load_config(path="config.yaml"):
    """YAML 설정 파일 로드"""
    if not os.path.exists(path):
        print(f"⚠️ Config file '{path}' not found. Using empty config.")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"❌ Error parsing YAML: {e}")
            return {}


def prepare_test_data(input_dir):
    """테스트용 더미 데이터를 생성합니다."""

    md_content = """
# Sayou Fabric Guide
Sayou is a modular data pipeline.

## Module 1: Connector
Connectors fetch data from various sources.

## Module 2: Brain
Brain orchestrates the whole process.
    """.strip()

    with open(f"{input_dir}/guide_demo.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    json_data = [
        {"id": 1, "name": "Alice", "email": "alice@test.com", "score": 95},
        {"id": 2, "name": "Bob", "email": "bob@test.com", "score": 15000},
    ]
    with open(f"{input_dir}/users_demo.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f)

    print(f"✅ Created test data in '{input_dir}'")


def run_demo():
    print(">>> [Sayou Fabric] Initializing Brain...")

    INPUT_DIR = "examples/input"
    OUTPUT_FILE = "examples/kg_demo.json"

    # 1. 환경 설정
    config = load_config("config.yaml")
    create_input_folder(INPUT_DIR)

    # 2. Brain 초기화
    brain = StandardPipeline(extra_splitters=[MarkdownSplitter])

    # 3. 데이터 준비
    prepare_test_data(INPUT_DIR)

    # 4. Ingest 실행
    print(f">>> Starting Ingestion from '{INPUT_DIR}'...")

    result = brain.process(
        source=INPUT_DIR,
        destination=OUTPUT_FILE,
    )

    print("\n=== Ingestion Result ===")
    print(json.dumps(result, indent=2))

    # 5. 결과 파일 검증
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            kg = json.load(f)

        node_count = len(kg.get("nodes", []))
        edge_count = len(kg.get("edges", []))
        print(f"\n✅ Validated Output: {OUTPUT_FILE}")
        print(f"   - Nodes: {node_count}")
        print(f"   - Edges: {edge_count}")

        # PII 마스킹 확인 (email이 가려졌는지)
        print("   - Sample Node Content:")
        for node in kg["nodes"][:3]:
            # JSON Record의 경우 content가 dict로 들어감
            content = node["attributes"].get("schema:text")
            # (RecordNormalizer 등은 schema:text 대신 다른 키를 쓸 수 있으나,
            #  여기서는 간단히 출력)
            print(f"     * {node['node_id']}: {str(content)[:50]}...")


if __name__ == "__main__":
    run_demo()
