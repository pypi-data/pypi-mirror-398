import logging
import os

from sayou.loader.pipeline import LoaderPipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_demo():
    print(">>> Initializing Sayou Loader Pipeline...")

    pipeline = LoaderPipeline()
    pipeline.initialize()

    OUTPUT_DIR = "examples"
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    graph_payload = {
        "nodes": [
            {"id": "n1", "label": "Person", "props": {"name": "Alice"}},
            {"id": "n2", "label": "Person", "props": {"name": "Bob"}},
        ],
        "edges": [{"source": "n1", "target": "n2", "type": "KNOWS"}],
        "metadata": {"generated_at": "2023-10-27"},
    }

    # 전략: file
    dest_path = os.path.join(OUTPUT_DIR, "knowledge_graph_demo.json")

    pipeline.run(graph_payload, destination=dest_path, strategy="file")

    print(f"✅ Check file: {dest_path}")

    # 더미 벡터 데이터 (리스트)
    vector_payloads = [
        {"id": f"vec_{i}", "vector": [0.1, 0.2, float(i)], "text": f"Chunk {i}"}
        for i in range(5)
    ]

    # 전략: jsonl (또는 stream)
    dest_path_l = os.path.join(OUTPUT_DIR, "vectors_demo.jsonl")

    pipeline.run(vector_payloads, destination=dest_path_l, strategy="jsonl")

    print(f"✅ Check file: {dest_path_l}")

    # 내용 확인
    with open(dest_path_l, "r") as f:
        print("\n[File Content Preview]")
        print(f.read())

    # 콘솔 출력 테스트
    pipeline.run("System ready.", destination="STDOUT", strategy="console")


if __name__ == "__main__":
    run_demo()
