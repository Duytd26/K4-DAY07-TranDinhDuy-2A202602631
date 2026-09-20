from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức để trả lời câu hỏi."

        context_entries = []
        for i, r in enumerate(results, start=1):
            source = r.get("metadata", {}).get("source", r.get("id", f"doc_{i}"))
            context_entries.append(f"[{i}] (Nguồn: {source}):\n{r['content']}")
        context_str = "\n\n".join(context_entries)

        prompt = (
            f"Bạn là trợ lý AI trả lời câu hỏi dựa trên cơ sở tri thức.\n"
            f"Chỉ sử dụng thông tin trong ngữ cảnh được cung cấp dưới đây để trả lời. "
            f"Hãy trích dẫn nguồn bằng số thứ tự [1], [2] tương ứng. "
            f"Nếu thông tin không có trong ngữ cảnh, hãy nêu rõ là không tìm thấy thông tin.\n\n"
            f"Ngữ cảnh:\n{context_str}\n\n"
            f"Câu hỏi: {question}\n\n"
            f"Câu trả lời:"
        )
        return self.llm_fn(prompt)
