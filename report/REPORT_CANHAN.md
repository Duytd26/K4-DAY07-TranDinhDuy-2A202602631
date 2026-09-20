# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Đình Duy
**Nhóm:** G66
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự Cosine cao (tiến dần về 1.0) thể hiện hai vector embedding cùng hướng trong không gian ngữ nghĩa nhiều chiều. Điều này có nghĩa là hai đoạn văn bản có sự tương đồng lớn về mặt ý nghĩa, chủ đề và ngữ cảnh, bất kể độ dài hay câu từ chính xác có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Khách hàng có thể gửi yêu cầu trả hàng và hoàn tiền trong thời hạn 15 ngày kể từ ngày nhận hàng."
- Câu B: "Thời gian cho phép người mua khiếu nại đổi trả sản phẩm là nửa tháng sau khi giao dịch thành công."
- Tại sao tương đồng: Hai câu sử dụng các từ vựng đồng nghĩa và cấu trúc câu khác nhau ("15 ngày" vs "nửa tháng", "khách hàng" vs "người mua", "hoàn trả sản phẩm" vs "trả hàng và hoàn tiền"), nhưng đều truyền tải cùng một nội dung chính sách về thời hạn đổi trả hàng thương mại điện tử.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sản phẩm điện tử chính hãng được bảo hành 12 tháng tại các trung tâm bảo hành ủy quyền trên toàn quốc."
- Câu B: "Công thức nấu món phở bò truyền thống chuẩn vị Hà Nội cần chuẩn bị hoa hồi, quế và thảo quả nướng thơm."
- Tại sao khác: Hai câu thuộc hai lĩnh vực ngữ nghĩa hoàn toàn tách biệt (chính sách kỹ thuật - thương mại điện tử đối lập với ẩm thực), các đặc trưng vector không có sự giao thoa ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị phụ thuộc vào độ dài (magnitude) của vector, do đó hai văn bản cùng một ý nghĩa nhưng một đoạn viết ngắn gọn và một đoạn dài lặp lại từ vựng sẽ bị đẩy ra xa nhau. Ngược lại, Cosine Similarity chuẩn hóa độ dài của vector và chỉ tập trung đo góc định hướng giữa chúng, giúp phản ánh chính xác sự tương đồng ngữ nghĩa mà không bị sai lệch bởi độ dài đoạn văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Áp dụng công thức: $\text{số chunk} = \left\lceil \frac{\text{độ\_dài} - \text{độ\_chồng\_chéo}}{\text{kích\_thước\_chunk} - \text{độ\_chồng\_chéo}} \right\rceil$
> - $\text{số chunk} = \left\lceil \frac{10000 - 50}{500 - 50} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \lceil 22.111... \rceil = 23$
> *Đáp án:* **23 chunks** (đã xác thực bằng code `FixedSizeChunker(chunk_size=500, overlap=50)`).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Khi overlap tăng lên 100, số lượng chunk tăng lên thành: $\left\lceil \frac{10000 - 100}{500 - 100} \right\rceil = \left\lceil \frac{9900}{400} \right\rceil = \lceil 24.75 \rceil = 25$ chunks (tăng thêm 2 chunks).
> - Chúng ta muốn tăng độ chồng chéo để bảo toàn mạch ngữ cảnh liên tục giữa các chunk kề nhau, ngăn ngừa việc các câu văn hoặc ý niệm quan trọng bị cắt đôi ngay ranh giới chunk khiến embedding mất thông tin hoặc RAG truy xuất thiếu ngữ cảnh.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy Positive Lookbehind `r"(?<=[.!?])\s+"` để phân tách tại vị trí sau các dấu chấm, chấm than, chấm hỏi kèm khoảng trắng hoặc xuống dòng mà không làm mất dấu câu ở cuối câu. Sau khi tách câu, lọc bỏ các chuỗi rỗng và gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk, đồng thời xử lý an toàn văn bản rỗng trả về `[]`. Một edge case chưa xử lý triệt để là các từ viết tắt (`TS.`, `v.v.`) hoặc số thập phân (`3.14`) có thể bị nhận nhầm thành kết thúc câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo nguyên lý đệ quy 2 chiều: đi từ phân cách lớn nhất xuống phân cách nhỏ hơn theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]` khi đoạn văn bản dài hơn `chunk_size`, sau đó thực hiện gom (merge) các mảnh nhỏ liên tiếp sát ngưỡng `chunk_size` để tránh sinh ra các chunk vụn. Base cases gồm: văn bản rỗng trả `[]`, độ dài văn bản $\le$ `chunk_size` trả `[current_text]`, và khi hết separator (`separators == []`) hoặc separator rỗng `""` thì cắt lát trực tiếp theo kích thước `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ các tài liệu dạng in-memory trong danh sách dict `self._store`. Hàm `_make_record` chuẩn hóa dữ liệu, sao chép metadata độc lập và đảm bảo luôn có khóa `doc_id`, sau đó lưu cùng vector embedding. Hàm `search` (thông qua `_search_records`) tính tích vô hướng (dot product) giữa query vector đã nhúng và từng record trong store, sắp xếp điểm tương đồng giảm dần và trích xuất `top_k` kết quả (loại bỏ vector embedding thô để output sạch).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Áp dụng cơ chế **pre-filtering** (lọc trước khi tìm kiếm): lọc tập ứng viên trong `self._store` thỏa mãn toàn bộ các cặp key-value của `metadata_filter`, sau đó mới chuyển sang hàm tìm kiếm tương đồng; việc này đảm bảo các slot trong `top_k` không bị chiếm bởi tài liệu sai điều kiện lọc. Hàm `delete_document` lọc bỏ mọi bản ghi có `metadata['doc_id'] == doc_id` hoặc `id == doc_id` và trả về `True` nếu kích thước store giảm đi, ngược lại `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `self.store.search(question, top_k)` để truy xuất các đoạn văn bản liên quan nhất. Định dạng ngữ cảnh có đánh số thứ tự `[1]`, `[2]` kèm nguồn gốc (`metadata['source']`) nhằm phục vụ tiêu chí truy vết nguồn (Source Traceability). Dựng prompt RAG yêu cầu LLM đóng vai trò trợ lý chuyên môn, chỉ trả lời dựa vào ngữ cảnh và nêu rõ nếu không tìm thấy thông tin, đồng thời xử lý an toàn trường hợp store rỗng mà không gây crash hay gọi LLM vô ích.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- D:\vin20k\LAB7\K4-L3B-Data-Foundations\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\vin20k\LAB7\K4-L3B-Data-Foundations
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.19s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng hóa áp dụng trong vòng 15 ngày. | Thời gian cho phép hoàn trả sản phẩm là 15 ngày. | cao | 0.1619 | Đúng |
| 2 | Shopee hỗ trợ phí vận chuyển cho đơn hàng đạt giá trị tối thiểu. | Người mua được miễn phí giao hàng nếu giá trị đơn đủ điều kiện. | cao | 0.1049 | Đúng |
| 3 | Thời gian bảo hành máy tính xách tay là hai mươi bốn tháng. | Cách làm món phở bò truyền thống thơm ngon tại nhà. | thấp | 0.0307 | Đúng |
| 4 | Người bán cần xác nhận đơn hàng trong vòng 24 giờ kể từ khi phát sinh. | Quy định thời hạn người bán chuẩn bị và giao hàng cho bưu tá. | cao | -0.0776 | Sai (do Mock) |
| 5 | Tài khoản người dùng bị khóa do vi phạm chính sách cộng đồng. | Giá vàng hôm nay tiếp tục tăng mạnh trên thị trường quốc tế. | thấp | -0.2297 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là ở cặp số 4: hai câu đều nói về nghĩa vụ chuẩn bị và giao hàng của Người bán trên sàn TMĐT nhưng lại nhận điểm số âm (-0.0776) trên `MockEmbedder`. Điều này phản ánh rõ ràng bản chất của `MockEmbedder` chỉ băm chuỗi ký tự ngẫu nhiên bằng MD5 chứ không hiểu ngữ nghĩa thực sự, khẳng định vai trò tối quan trọng của mô hình embedding nơ-ron thật (như Local Multilingual hoặc OpenAI/Gemini) trong việc nắm bắt bản chất ngữ nghĩa của văn bản trong hệ thống RAG.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

*(Phần này được cập nhật đồng bộ sau khi nhóm thống nhất bộ 5 Benchmark Queries ở Giai đoạn 2)*

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Đối với yêu cầu Trả hàng/Hoàn tiền ở trạng thái Shopee đang xem xét, thời gian Shopee xử lý và gửi kết quả là bao lâu? | `shopee-buyer-return-request-guide#5`: Mục 2 Thời gian xử lý... | 0.2073 | Có (Relevant) | Shopee xử lý và gửi kết quả trong vòng 3-5 ngày làm việc qua Thông báo hoặc email. |
| 2 | Nếu Shopee đồng ý cho Người mua Trả hàng & Hoàn tiền, Người mua phải hoàn tất gửi trả hàng trong bao lâu? | `shopee-buyer-return-request-guide#5`: Mục 2 Thời gian xử lý... | 0.1903 | Có (Relevant) | Người mua cần hoàn tất gửi trả hàng trong vòng 6 ngày kể từ thông báo chấp thuận. |
| 3 | (Filter audience=seller) Khi Shopee thông báo quyết định hoàn tiền, Người Bán có thời hạn bao lâu để gửi phản hồi nếu không đồng ý? | `shopee-mall-seller-terms-of-service#22`: Mục 1.1 Nghĩa vụ phản hồi... | 0.3077 | Có (Relevant) | Người Bán cần gửi phản hồi/khiếu nại trong vòng 02 ngày lịch kể từ ngày nhận được thông báo. |
| 4 | Mức hoàn tiền ngay do Người Bán tự thỏa thuận và đề xuất với Người Mua không được thấp hơn bao nhiêu % giá trị sản phẩm? | `shopee-mall-seller-terms-of-service#15`: Mục 1.1 Thỏa thuận hoàn tiền... | 0.2913 | Có (Relevant) | Số tiền hoàn trả tự thỏa thuận không được thấp hơn 50% giá trị sản phẩm hoàn trả. |
| 5 | Thời hạn chuẩn để Người Mua gửi yêu cầu trả hàng/hoàn tiền là bao lâu và đối với thực phẩm tươi sống là bao lâu? | `shopee-return-shipping-fee-policy#0` / `timeline#3`: Mục 1 Thời hạn... | 0.2082 | Có (Relevant) | Thời hạn chuẩn là 15 ngày kể từ khi giao thành công, thực phẩm tươi sống là trong 24 giờ. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chiến lược chunking theo tiêu đề (heading-based) đặc biệt hiệu quả đối với các văn bản chính sách và điều khoản pháp lý TMĐT có cấu trúc rõ ràng, vì mỗi section tự nó đã là một đơn vị ngữ nghĩa trọn vẹn. Tuy nhiên, việc kết hợp metadata pre-filtering mới là yếu tố quyết định để phân định chính sách giữa Người mua và Người bán một cách chính xác.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
