import logging

from sayou.wrapper.pipeline import WrapperPipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_demo():
    print(">>> Initializing Sayou Wrapper...")

    pipeline = WrapperPipeline()
    pipeline.initialize()

    chunks_data = [
        {
            "content": "# Introduction to AI",
            "metadata": {
                "chunk_id": "doc1_h_0",
                "semantic_type": "h1",
                "is_header": True,
                "source": "ai_intro.md",
                "page_num": 1,
            },
        },
        {
            "content": "AI stands for Artificial Intelligence.",
            "metadata": {
                "chunk_id": "doc1_p_0",
                "semantic_type": "text",
                "parent_id": "doc1_h_0",
                "source": "ai_intro.md",
                "page_num": 1,
            },
        },
        {
            "content": "| Model | Type |",
            "metadata": {
                "chunk_id": "doc1_t_0",
                "semantic_type": "table",
                "parent_id": "doc1_h_0",
                "source": "ai_intro.md",
            },
        },
    ]

    # (옵션) 실제 파일에서 로드하는 경우
    # import json
    # import os
    # input_file = "./chunks_demo.json"
    # if os.path.exists(input_file):
    #     with open(input_file, "r", encoding="utf-8") as f:
    #         chunks_data = json.load(f)

    print(f"Ready to process {len(chunks_data)} chunks.")

    try:
        output = pipeline.run(chunks_data, strategy="document_chunk")

        print(f"✅ Generated {len(output.nodes)} SayouNodes.\n")

        for node in output.nodes:
            print(f"🔹 [{node.node_class}] {node.node_id}")
            print(f"   Name: {node.friendly_name}")

            if "schema:text" in node.attributes:
                print(f"   Text: {node.attributes['schema:text'][:30]}...")

            if node.relationships:
                print(f"   Rels: {node.relationships}")
            print("-" * 40)

    except Exception as e:
        print(f"❌ Error: {e}")

    final_json = output.model_dump_json(indent=2)

    with open("examples/wrapper_output_demo.json", "w", encoding="utf-8") as f:
        f.write(final_json)

    print("Saved to wrapper_output_demo.json")


if __name__ == "__main__":
    run_demo()
