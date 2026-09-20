#!/usr/bin/env python3
"""Benchmark runner for Lab 07 (K4-L3B).

Evaluates 5 benchmark queries across the ingested corpus.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore


class HeadingSectionChunker:
    """Structure-aware chunker that splits text by Markdown sections (headings)."""

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        sections = re.split(r"(?m)^(?=#{2,3}\s+)", text)
        chunks: list[str] = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            if len(sec) <= self.chunk_size:
                chunks.append(sec)
            else:
                chunks.extend(self.fallback.chunk(sec))
        return chunks


BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Đối với yêu cầu Trả hàng/Hoàn tiền ở trạng thái Shopee đang xem xét, thời gian Shopee xử lý và gửi kết quả là bao lâu?",
        "filter": {"audience": "buyer"},
        "gold_answer": "Trong vòng 3-5 ngày làm việc (không tính chủ nhật và các ngày lễ, Tết) qua Thông báo hoặc email.",
    },
    {
        "id": 2,
        "query": "Nếu Shopee đồng ý cho Người mua Trả hàng & Hoàn tiền, Người mua phải hoàn tất gửi trả hàng trong bao lâu?",
        "filter": {"audience": "buyer"},
        "gold_answer": "Trong vòng 6 ngày kể từ thời điểm nhận được thông báo gửi trả hàng từ Shopee.",
    },
    {
        "id": 3,
        "query": "Khi Shopee thông báo quyết định hoàn tiền, Người Bán có thời hạn bao lâu để gửi phản hồi nếu không đồng ý?",
        "filter": {"audience": "seller"},
        "gold_answer": "Trong vòng 02 ngày lịch kể từ ngày nhận được thông báo của Shopee.",
    },
    {
        "id": 4,
        "query": "Mức hoàn tiền ngay do Người Bán tự thỏa thuận và đề xuất với Người Mua không được thấp hơn bao nhiêu % giá trị sản phẩm?",
        "filter": {"audience": "seller"},
        "gold_answer": "Không được thấp hơn 50% giá trị của Sản Phẩm Hoàn Trả.",
    },
    {
        "id": 5,
        "query": "Thời hạn chuẩn để Người Mua gửi yêu cầu trả hàng/hoàn tiền là bao lâu và đối với thực phẩm tươi sống là bao lâu?",
        "filter": {"audience": "buyer"},
        "gold_answer": "Thời hạn chuẩn là trong vòng 15 ngày kể từ khi đơn hàng giao thành công; riêng thực phẩm tươi sống và đông lạnh là trong vòng 24 giờ.",
    },
]


def parse_markdown_file(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw_fm = parts[1]
            content = parts[2].strip()
            fm = dict(re.findall(r"^(\w+):\s*(.+)$", raw_fm, re.M))
            fm = {k: v.split("#")[0].strip().strip('"\'') for k, v in fm.items()}
            return fm, content
    return {}, text.strip()


def run_benchmark(data_dir: Path | None = None) -> None:
    if data_dir is None:
        if Path("data/exchange_policy").exists():
            data_dir = Path("data/exchange_policy")
        elif Path("exchange_policy").exists():
            data_dir = Path("exchange_policy")
        else:
            data_dir = Path("data/ecommerce")
    output_lines: list[str] = []

    def log(msg: str = "") -> None:
        print(msg)
        output_lines.append(msg)

    log("=" * 60)
    log("K4-L3B BENCHMARK RUNNER")
    log(f"Data directory: {data_dir}")
    log("=" * 60)

    chunker = HeadingSectionChunker(chunk_size=500)
    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=_mock_embed)

    md_files = sorted(data_dir.glob("*.md"))
    all_chunks: list[Document] = []

    for path in md_files:
        metadata, content = parse_markdown_file(path)
        base_doc_id = metadata.get("doc_id", path.stem)
        chunks = chunker.chunk(content)
        for i, c in enumerate(chunks):
            doc = Document(
                id=f"{base_doc_id}#{i}",
                content=c,
                metadata={**metadata, "doc_id": base_doc_id, "chunk_index": i},
            )
            all_chunks.append(doc)

    store.add_documents(all_chunks)
    log(f"Loaded {len(md_files)} files -> {store.get_collection_size()} chunks indexed.\n")

    agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: "Tra cứu thành công từ ngữ cảnh.")

    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        query = item["query"]
        qfilter = item["filter"]
        gold = item["gold_answer"]

        log(f"--- Query {qid} ---")
        log(f"Query:  {query}")
        log(f"Filter: {qfilter}")
        log(f"Gold:   {gold}")

        # Search with filter
        results = store.search_with_filter(query, top_k=3, metadata_filter=qfilter)
        log("Top-3 Retrieved Chunks (with filter):")
        for rank, r in enumerate(results, start=1):
            snippet = r["content"][:100].replace("\n", " ")
            log(f"  {rank}. [{r['id']}] score={r['score']:.4f} doc_id={r['metadata'].get('doc_id')}")
            log(f"     Preview: {snippet}...")

        # Also demo A/B comparison without filter for Query 3
        if qid == 3:
            unfiltered = store.search(query, top_k=3)
            log("\n  [A/B Compare - Without Filter]:")
            for rank, r in enumerate(unfiltered, start=1):
                snippet = r["content"][:100].replace("\n", " ")
                log(f"    {rank}. [{r['id']}] score={r['score']:.4f} audience={r['metadata'].get('audience')}")
                log(f"       Preview: {snippet}...")

        log()

    Path("ket_qua_benchmark.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print("\nSaved benchmark results to ket_qua_benchmark.txt (UTF-8).")


if __name__ == "__main__":
    run_benchmark()
