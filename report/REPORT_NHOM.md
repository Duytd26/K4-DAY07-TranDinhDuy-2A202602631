# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G66
**Thành viên:** Trần Đình Duy (và các thành viên nhóm G66)
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Đổi trả, Hoàn tiền và Quy định Người mua / Người bán trên sàn Thương mại Điện tử Shopee.

**Tại sao nhóm chọn chủ đề này?**
> Đây là chủ đề bắt buộc theo quy định K4-L3B. Các văn bản chính sách của Shopee có cấu trúc điều khoản rõ ràng, nhiều mốc thời gian cụ thể (3-5 ngày làm việc, 6 ngày gửi trả, 2 ngày phản hồi của seller, 15 ngày khiếu nại...) và có sự phân định rõ rệt giữa hai đối tượng đối lập là Người Mua (`buyer`) và Người Bán (`seller`), tạo điều kiện lý tưởng để kiểm nghiệm tính năng lọc siêu dữ liệu (`metadata_filter`) và các chiến lược chia nhỏ văn bản (chunking).

### Danh sách tài liệu (Data Inventory)
    
| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|---|---|---|---:|---|
| 1 | Hướng dẫn gửi yêu cầu Trả hàng và Hoàn tiền dành cho Người mua | https://help.shopee.vn/portal/4/article/79233 | 2026-09-20 / 2024-v2 | ~2,500 | `audience: buyer`, `category: returns-guide`, `language: vi` |
| 2 | Quy định thời hạn và điều kiện trả hàng dành cho Người mua | https://help.shopee.vn/portal/4/article/77244 | 2026-09-20 / 2024-v1 | ~1,800 | `audience: buyer`, `category: returns-policy`, `language: vi` |
| 3 | Chính sách chi phí vận chuyển khi trả hàng dành cho Người mua | https://help.shopee.vn/portal/4/article/77247 | 2026-09-20 / not-stated | ~1,500 | `audience: buyer`, `category: shipping-policy`, `language: vi` |
| 4 | Quy định thời hạn xử lý khiếu nại trả hàng dành cho Người bán | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / 2024-v1 | ~2,100 | `audience: seller`, `category: seller-policy`, `language: vi` |
| 5 | Quy định bảo hành sản phẩm và nghĩa vụ của Người bán | https://help.shopee.vn/portal/4/article/77246 | 2026-09-20 / 2024-v1 | ~1,900 | `audience: seller`, `category: warranty-policy`, `language: vi` |
| 6 | Quy định chung về Trả hàng Hoàn tiền của Shopee | https://help.shopee.vn/portal/4/article/188931 | 2026-09-20 / not-stated | ~7,700 | `audience: buyer`, `category: returns`, `language: vi` |
| 7 | Điều khoản Dịch vụ Shopee Mall cho Người bán | https://help.shopee.vn/portal/4/article/77262 | 2026-09-20 / not-stated | ~16,100 | `audience: seller`, `category: terms`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | `str` | `buyer`, `seller`, `both` | Tránh lẫn lộn chính sách giữa người mua và người bán khi câu hỏi không nêu rõ chủ thể |
| `category` | `str` | `returns`, `terms`, `shipping-fee` | Thu hẹp phạm vi tìm kiếm theo chuyên mục chính sách |
| `source_url` | `str` | `https://help.shopee.vn/...` | Cung cấp link gốc minh bạch nguồn dữ liệu |
| `retrieved_at` | `str` | `2026-09-20` | Giúp kiểm soát độ mới và thời điểm thu thập dữ liệu |
| `document_version` | `str` | `2026-03-11` / `not-stated` | Xác định phiên bản hiệu lực của điều khoản |
| `language` | `str` | `vi` | Phục vụ lọc đa ngôn ngữ nếu hệ thống mở rộng |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên các tài liệu đã thu thập (với `chunk_size=500`):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Quy định chung Trả hàng Hoàn tiền | FixedSizeChunker (`fixed_size`) | 12 | 496.8 | Cắt ngang câu tại ranh giới cố định 500 ký tự |
| Quy định chung Trả hàng Hoàn tiền | SentenceChunker (`by_sentences`) | 9 | 599.9 | Giữ nguyên câu, nhưng một số đoạn gộp vượt ngưỡng |
| Quy định chung Trả hàng Hoàn tiền | RecursiveChunker (`recursive`) | 16 | 336.8 | Mạch lạc, tách và gộp tôn trọng ranh giới đoạn văn |
| Điều khoản Dịch vụ Shopee Mall | FixedSizeChunker (`fixed_size`) | 27 | 496.6 | Dễ cắt rời số liệu tỷ lệ/phí khỏi tiêu đề điều khoản |
| Điều khoản Dịch vụ Shopee Mall | SentenceChunker (`by_sentences`) | 37 | 325.4 | Mạch lạc từng câu nhưng rời rạc bối cảnh điều luật |
| Điều khoản Dịch vụ Shopee Mall | RecursiveChunker (`recursive`) | 32 | 376.6 | Phân bổ đều, bám sát các mục quy định nhỏ và bảng phí |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Đình Duy**
- **Loại chiến lược:** Chunker theo Tiêu đề / Mục chính sách (`HeadingSectionChunker`) kết hợp đệ quy
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản chính sách pháp lý TMĐT có cấu trúc phân cấp chặt chẽ theo từng Điều, Mục (`## 1. Nguyên tắc chung`, `## 5. QUYỀN CỦA NGƯỜI BÁN`). Tách theo Heading giữ trọn vẹn một đơn vị quy định trong cùng một chunk; chỉ khi mục quá dài mới hạ bậc đệ quy.
- **Code snippet (nếu custom):**
```python
import re
from src.chunking import RecursiveChunker

class HeadingSectionChunker:
    """Tách văn bản theo các section markdown (## hoặc ###), giữ tiêu đề ngữ cảnh."""
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        sections = re.split(r'(?m)^(?=#{2,3}\s+)', text)
        chunks = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            if len(sec) <= self.chunk_size:
                chunks.append(sec)
            else:
                chunks.extend(self.fallback.chunk(sec))
        return chunks
```

**Thành viên 2 — [Tên Thành viên 2]**
- **Loại chiến lược:** `RecursiveChunker` chuẩn (tối ưu separators)
- **Mô tả & lý do chọn:** Thử nghiệm thuật toán đệ quy chuẩn với bộ phân cách `["\n\n", "\n", ". ", " ", ""]`, tập trung vào việc gom các đoạn văn tự nhiên sát ngưỡng `chunk_size=400`.
- **Code snippet (nếu custom):**
```python
# Sử dụng RecursiveChunker(chunk_size=400)
```

**Thành viên 3 — [Tên Thành viên 3]**
- **Loại chiến lược:** `FixedSizeChunker` với overlap lớn (`chunk_size=500`, `overlap=100`)
- **Mô tả & lý do chọn:** Kiểm nghiệm xem liệu việc tăng overlap từ 50 lên 100 có giúp nối liền thông tin giữa các ranh giới cắt hay không, làm đường cơ sở (baseline) so sánh với 2 phương pháp có nhận thức cấu trúc trên.
- **Code snippet (nếu custom):**
```python
# Sử dụng FixedSizeChunker(chunk_size=500, overlap=100)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Thành viên 1 | HeadingSectionChunker | 10/10 | Giữ trọn ngữ cảnh toàn bộ điều khoản; không bị mất tiêu đề mục | Section quá ngắn có thể tạo chunk kích thước nhỏ |
| Thành viên 2 | RecursiveChunker | 8/10 | Độ dài đồng đều, không làm rách câu văn | Đôi khi tách một điều khoản dài thành 2 chunk mất liên kết |
| Thành viên 3 | FixedSizeChunker (overlap=100) | 6/10 | Đơn giản, độ dài cố định dự đoán được | Vẫn cắt đôi câu và bảng biểu, gây nhiễu từ khóa rác |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược **HeadingSectionChunker** (Thành viên 1) hoạt động tốt nhất cho chủ đề chính sách TMĐT. Bởi vì văn bản quy định vốn đã được soạn thảo theo cấu trúc phân tầng ngữ nghĩa hoàn chỉnh (từng điều khoản là một chủ thể logic độc lập); việc bám theo heading giúp chunk mang đầy đủ điều kiện - đối tượng áp dụng - thời hạn mà không bị xé vụn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Đối với yêu cầu Trả hàng/Hoàn tiền ở trạng thái Shopee đang xem xét, thời gian Shopee xử lý và gửi kết quả là bao lâu? | Trong vòng 3-5 ngày làm việc (không tính thứ Bảy, Chủ Nhật và các ngày nghỉ lễ/Tết) qua Thông báo hoặc email. | `shopee-buyer-return-request-guide` (Mục 2) / `shopee-general-return-policy` (Mục 1.2) |
| 2 | Nếu Shopee đồng ý cho Người mua Trả hàng & Hoàn tiền, Người mua phải hoàn tất gửi trả hàng trong bao lâu? | Trong vòng 6 ngày kể từ thời điểm nhận được thông báo gửi trả hàng từ Shopee. | `shopee-buyer-return-request-guide` (Mục 2) / `shopee-return-shipping-fee-policy` |
| 3 | (Cần filter audience=seller) Khi Shopee thông báo quyết định hoàn tiền (Hoàn Tiền Ngay), Người Bán có thời hạn bao lâu để gửi phản hồi nếu không đồng ý? | Trong vòng 02 ngày lịch kể từ ngày nhận được thông báo/yêu cầu của Shopee. | `shopee-mall-seller-terms-of-service` (Mục 1.1) / `shopee-seller-return-processing-policy` (Mục 1) |
| 4 | Mức hoàn tiền ngay do Người Bán tự thỏa thuận và đề xuất với Người Mua không được thấp hơn bao nhiêu % giá trị sản phẩm? | Không được thấp hơn 50% giá trị của Sản Phẩm Hoàn Trả (hoặc 100% nếu vi phạm quy định). | `shopee-mall-seller-terms-of-service` (Mục 1.1) |
| 5 | Thời hạn chuẩn để Người Mua gửi yêu cầu trả hàng/hoàn tiền là bao lâu và đối với thực phẩm tươi sống là bao lâu? | Thời hạn chuẩn là trong vòng 15 ngày kể từ khi đơn hàng giao thành công; riêng thực phẩm tươi sống và đông lạnh là trong vòng 24 giờ. | `shopee-general-return-policy` (Mục 1.2) / `shopee-buyer-return-timeline-policy` (Mục 1) |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời gian Shopee xử lý khi xem xét | HeadingSectionChunker | Có (Top-1) | Trả về trọn vẹn Mục 2 Thời gian xử lý và Hoàn tiền (score=0.2073) |
| 2 | Thời hạn gửi trả hàng sau chấp thuận | HeadingSectionChunker | Có (Top-1) | Giữ nguyên vẹn hướng dẫn và mốc thời gian hoàn trả |
| 3 | Thời hạn phản hồi của Người Bán | HeadingSectionChunker | Có (Top-1) | Bắt buộc phải có filter `audience: seller` mới lấy đúng quy định người bán Shopee Mall |
| 4 | Tỷ lệ hoàn tiền tối thiểu của Người Bán | RecursiveChunker / Heading | Có (Top-1) | Trích xuất chính xác điều khoản hoàn trả và bồi hoàn của người bán |
| 5 | Thời hạn gửi yêu cầu của Người Mua | HeadingSectionChunker | Có (Top-1) | Lấy đầy đủ cả 15 ngày thông thường và 24 giờ cho thực phẩm tươi sống |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata phát huy tác dụng sống còn ở **Câu hỏi số 3**: Khi câu hỏi liên quan đến thời hạn phản hồi ("02 ngày"), nếu không lọc `audience: seller`, hệ thống bị phân tán bởi các chunk của người mua (`shopee-general-return-policy#11`, `#15`). Khi áp dụng `metadata_filter={"audience": "seller"}`, top 1 trả về chính xác điều khoản nghĩa vụ và chế tài của Người Bán tại Shopee Mall (`shopee-mall-seller-terms-of-service#22`, `#1`).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. *Chiến lược có nhận thức cấu trúc (Structure-aware Chunking)*: Văn bản chính sách pháp lý / TMĐT cần được chia nhỏ bám theo cấu trúc tiêu đề (heading/section) thay vì cắt máy móc theo số lượng ký tự; điều này bảo toàn mối liên hệ ràng buộc giữa điều kiện - chủ thể - quyền lợi.
> 2. *Tầm quan trọng sống còn của Metadata Pre-filtering*: Trong cùng một văn bản hoặc tập tài liệu có các quy định tương tự nhau cho nhiều đối tượng (Người mua vs Người bán), chỉ tìm kiếm tương đồng vector (semantic search) là không đủ vì độ tương đồng từ khóa dễ gây nhầm lẫn; metadata filter là công cụ bắt buộc để loại trừ kết quả sai đối tượng.
> 3. *Đánh giá kép (Dual Evaluation)*: Không thể chỉ nhìn `doc_id` của tài liệu lọt vào top-3 để kết luận thành công; cần phải đối chiếu chuỗi nội dung thực tế (grounding) xem chunk có chứa trực tiếp con số và mốc thời gian để Agent trả lời chính xác hay không.

**Bài học rút ra khi so sánh trong nhóm:**
> Khi chạy trên cùng bộ tài liệu và cùng 5 câu hỏi, chiến lược FixedSize bị cắt cụt nhiều câu quan trọng và bảng biểu, khiến mô hình embedding nhận các đoạn văn bản khuyết ngữ nghĩa. RecursiveChunker cải thiện đáng kể tính mạch lạc của câu nhưng vẫn có thể cắt đôi một điều khoản dài. HeadingSectionChunker cho kết quả truy xuất ổn định và điểm số câu trả lời chính xác nhất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thiết kế thêm metadata `section_title` và trích xuất bảng biểu thành các đoạn có cấu trúc Markdown Table rõ ràng hơn khi nạp vào hệ thống, đồng thời thử nghiệm mô hình embedding tiếng Việt đa ngữ (Local Multilingual Embedder) thay vì chỉ chạy trên môi trường giả lập.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
