# INVESTIGATE_PART3.md

Điều tra bổ sung (chỉ-đọc, không chạy mining) — tiếp nối `INVESTIGATE_REPO.md`.
Trả lời 2 câu hỏi quyết định trước khi refactor. File tham chiếu: `fwi_hiding_system_v38 (3).py`.

---

## CÂU 1 — QUANTITY CÓ THAM GIA TÍNH TOÁN KHÔNG?

### TRẢ LỜI DỨT KHOÁT
**CÓ — nhưng chỉ ở PHA MINING, KHÔNG ở pha sanitization.** Đây là một **bất nhất (inconsistency)** giữa hai pha, không phải "engine bỏ qua qty" đơn thuần. Cụ thể:

- **Pha MINING (`compute_tw_optimized`, PART 3): DÙNG qty.** Trọng số giao dịch tính bằng `tw = Σ(wᵢ × qtyᵢ) / |T|`.
- **Pha SANITIZATION (`HFPriorityManager` / `MCPriorityManager`, PART 4): BỎ qty.** Giao dịch bị chuyển thành **set item** (mất qty), nên `tw = Σwᵢ / |T|`.

### Truy vết biến `qty` từ đầu tới cuối

**(1) Load — qty được đọc thành int** (`load_transactions_from_file`, dòng 589–590):
```python
item, qty = part.split(':')
items[item] = int(qty)        # {tid: {item: qty}}, qty là số nguyên
```

**(2) MINING — qty ĐI VÀO công thức tw** (`compute_tw_optimized`, dòng 213–217):
```python
s_tk = len(t)
if s_tk > 0:
    utility = sum(weights.get(item, 0.0) * qty for item, qty in t.items())  # ← Σ(w × qty)
    tw_t = utility / s_tk        # ← chia cho |T|  ⇒  tw = Σ(w×qty) / |T|
    sumtw += tw_t
    transaction_tw_map[tid] = tw_t
```
⇒ **qty XUẤT HIỆN đúng một chỗ trong toàn engine: dòng 214.** Đây là điểm duy nhất qty tác động tới tw/ws.

**(3) Vào cây WUN — qty KHÔNG còn được dùng riêng** (`insert_transaction`, dòng 150–158): cây chỉ duyệt `transaction.keys()` (sự hiện diện item) và cộng **scalar `tw_t`** (đã tính sẵn ở bước 2) vào `node.weight`. Không có phép nhân qty nào trong cây. `processed_transactions_map` (dòng 329) vẫn giữ qty trong dict nhưng giá trị đưa vào cây là `tw_list` (các `tw_t`), nên qty ở đây **không được dùng lại**.

**(4) ws của item / itemset:** `ws = tw(item)/sumtw`, với `tw(item) = Σ_{T∋item} tw_T`. Vì `tw_T` đã "nuốt" qty ở bước 2, nên **ws thừa hưởng ảnh hưởng của qty gián tiếp** — nhưng chỉ ở mức trung bình per-transaction, không phải per-item-occurrence.

**(5) SANITIZATION — qty BỊ LOẠI HẲN.** Coordinator tạo bản làm việc dạng **set** (dòng 752):
```python
trans_set_template = {k: set(v.keys()) for k, v in trans_D.items()}   # ← chỉ giữ tên item, mất qty
```
Các manager tính lại tw trên set này, KHÔNG có qty (dòng 468 / 543 / 557):
```python
new_tw = sum(self.item_weights.get(i, 0) for i in t) / len(t) if t else 0.0   # ← Σw / |t|, KHÔNG có qty
```
`_calc_ws` (dòng 462, 537) cũng cộng `tw_ref[tid]` (các tw không-qty này) ⇒ điều kiện "đã ẩn xong" (`_calc_ws < min_ws`) được quyết định trên **mô hình trọng số KHÔNG qty**.

**(6) RE-MINE (đo metric):** coordinator dựng lại qty từ `trans_D` cho các item còn sống (dòng 781) rồi gọi lại `run_fwi_mining_core` ⇒ **re-mine DÙNG qty trở lại** (qua bước 2).

### Xác nhận TRUNG BÌNH (FWI) chứ không phải TỔNG utility (HUIM)
Phép chia `/ s_tk` (= `/|T|`) ở **dòng 215** xác nhận đây là mô hình **trung bình** (đặc trưng Frequent Weighted Itemset), **không phải** tổng utility `Σ(w×qty)` của HUIM (HUIM không chia cho độ dài giao dịch). 

> ⚠️ **Đính chính quan trọng so với hình dung ban đầu:** công thức mining **KHÔNG phải** `Σw/|T|` thuần — mà là **`Σ(w×qty)/|T|`**. Nó là *trung bình* (nên là FWI, không phải HUIM) **nhưng tử số vẫn nhân qty**. Chỉ khi mọi `qty = 1` thì `Σ(w×qty)/|T|` mới trùng `Σw/|T|`.

### Kết luận: nạp file có qty>1 thì FWI có sai không?

| Trường hợp | Hệ quả |
|---|---|
| **qty = 1 cho MỌI item** (điển hình các dataset FIMI: mushroom, chess, retail, accidents… ở dạng presence) | `Σ(w×qty)=Σw` ⇒ mining và sanitization **trùng khớp**, **không sai**. Hai pha nhất quán. |
| **qty > 1 tồn tại** (dữ liệu có số lượng thật, ví dụ dữ liệu IoT đếm sự kiện) | **CÓ RỦI RO SAI / BẤT NHẤT.** Mining và re-mine dùng `Σ(w×qty)/|T|`; nhưng vòng lặp xóa của manager dùng `Σw/|T|` để quyết định khi nào pattern "đã ẩn". Hai mô hình lệch nhau ⇒ manager có thể tưởng đã ẩn (theo Σw/|T|) trong khi re-mine (theo Σ(w×qty)/|T|) vẫn thấy frequent ⇒ **HF bị thổi phồng**; hoặc ngược lại xóa dư ⇒ **MC/AC/DDI sai lệch**. Ngoài ra `_is_safe` của MC cũng đánh giá NSFWI trên tw không-qty, nên "safety net" không phản ánh đúng ws thật (có qty). |

**Khuyến nghị trước refactor:**
1. **Kiểm tra dữ liệu thật:** mở các `*_quantities.txt` (trên Drive, không có trong repo) xem có token `item:qty` với `qty>1` không. Nếu tất cả `qty=1` → an toàn, bất nhất chỉ trên lý thuyết.
2. Nếu muốn hỗ trợ qty>1 một cách đúng: phải **thống nhất mô hình tw** giữa mining và sanitization — hoặc cả hai dùng `Σ(w×qty)/|T|` (giữ qty trong `trans_set_template`, đổi `set` → `dict`/`Counter` và sửa 3 công thức `new_tw` ở dòng 468/543/557), hoặc cả hai bỏ qty (đổi dòng 214 thành `sum(weights.get(item,0.0) for item in t)`). **Không được để lệch như hiện tại.**
3. Đối chiếu định nghĩa tw trong bản thảo: nếu bài mô tả `tw = Σw/|T|` (FWI chuẩn, không qty) thì **dòng 214 đã lệch bản thảo** — code đang nhân thêm qty.

---

## CÂU 2 — PHỤ THUỘC COLAB & ĐIỂM CẦN SỬA ĐỂ CHẠY GCP

### Liệt kê MỌI phụ thuộc Colab (chỉ 5 vị trí, tất cả là I/O path)

| # | Dòng | Nội dung | Mức độ |
|---|---|---|---|
| 1 | **10** | `from google.colab import drive` | **Blocker cứng** — chạy khi import module, môi trường không-Colab sẽ `ModuleNotFoundError`. |
| 2 | **11** | `drive.mount('/content/drive')` | **Blocker cứng** — mount Drive, ngoài Colab sẽ lỗi. |
| 3 | **71–73** | `is_colab = 'google.colab' in sys.modules` → nếu Colab đặt `DRIVE_ROOT='/content/drive/MyDrive/HUTECH/...'`, ngược lại `'./'` | Mềm — đã có nhánh fallback local (`'./'`), **không cần sửa**; sẽ tự dùng `./` khi không phải Colab. |
| 4 | **840** | `file_path = '/content/drive/MyDrive/.../fwi_v38_dual_results.json'` (cell visualization) | Trung bình — hardcode path Drive; chỉ ảnh hưởng bước vẽ hình, không ảnh hưởng mining. |

> Ghi chú: dòng 73 nhắc path Colab nhưng nằm trong nhánh `if self.is_colab:` nên **vô hại** khi chạy ngoài Colab.

### Cách gỡ AN TOÀN (không đụng logic mining)

**Dòng 10–11 (bắt buộc sửa):** bọc try/except để no-op khi không có Colab:
```python
try:
    from google.colab import drive
    drive.mount('/content/drive')
except (ImportError, ModuleNotFoundError):
    pass   # Không phải Colab (GCP/local): bỏ qua, PathManager sẽ tự dùng './'
```
→ `PathManager.is_colab` đã tự phát hiện qua `sys.modules` nên `DRIVE_ROOT` sẽ rơi về `'./'` một cách chính xác; **không cần sửa PART 3**.

**Dòng 73 (khuyến nghị, không bắt buộc):** cho phép cấu hình gốc dữ liệu qua biến môi trường để trỏ tới bucket/disk GCP mà không sửa code:
```python
self.DRIVE_ROOT = os.environ.get("FWI_DATA_ROOT", "./")
```
(giữ nguyên nhánh Colab; chỉ đổi default local). An toàn tuyệt đối với mining vì chỉ đổi đường dẫn.

**Dòng 840 (chỉ khi cần vẽ hình):** thay hardcode bằng đường dẫn tương đối / env:
```python
file_path = os.environ.get("FWI_RESULTS_JSON",
    os.path.join(os.environ.get("FWI_DATA_ROOT","./"),
                 "MyResults/fwi_processed_results/fwi_v38_dual_results.json"))
```

Tất cả các sửa trên **chỉ chạm I/O path**, không chạm bất kỳ hàm nào trong PART 3 (mining) hay PART 4 (hiding).

### Ngoài I/O path, PART 3 có phụ thuộc Colab nào khác không?
**KHÔNG.** Rà toàn file: **không có** `tqdm` / `tqdm.notebook`, **không có** `IPython.display` / `display(...)`, **không có** `get_ipython()`, **không có** `%matplotlib` hay bất kỳ `%magic`/`!shell` nào. PART 3 chỉ dùng thư viện chuẩn + `psutil`, `pandas`, `matplotlib` (import ở đầu), `gc`, `logging`, `multiprocessing` — đều chạy được trên GCP.
- Phụ thuộc pip cần cài trên GCP (không phải Colab-specific): `pandas`, `matplotlib`, `psutil`, và cho cell visualization thêm `seaborn`, `numpy`. (Không có `requirements.txt` trong repo — cần tạo hoặc cài thủ công.)

### Multiprocessing & khả năng chạy trên GCP c2-standard-16

**Có dùng multiprocessing** (khớp báo cáo cũ):
```python
NUM_WORKERS: int = min(4, max(1, mp.cpu_count() - 2))   # dòng 59  → luôn tối đa 4
USE_MULTIPROCESSING: bool = True                         # dòng 57
# dòng 358:
with ProcessPoolExecutor(max_workers=config.NUM_WORKERS,
                         initializer=init_worker, initargs=init_args) as executor:
```

**Trên c2-standard-16 (16 vCPU, 64 GB RAM):**
- **Chạy được như hiện tại, KHÔNG cần chỉnh để hoạt động.** `mp.cpu_count()-2 = 14`, nhưng `min(4, …)` **chốt cứng 4 worker** ⇒ chỉ dùng 4/16 vCPU. Hoạt động bình thường.
- Start method: GCP là Linux ⇒ mặc định **fork**, tương thích `ProcessPoolExecutor` + `initializer` truyền object lớn (`tree`, `swunl_dict`) — như đang chạy trên Colab (cũng Linux). Không cần `set_start_method`.
- **Chưa tối ưu (tùy chọn, không bắt buộc):**
  - Trần 4 worker lãng phí 12 vCPU. Muốn tận dụng: nới `NUM_WORKERS = min(14, max(1, mp.cpu_count()-2))` — nhưng lưu ý mỗi worker được truyền bản `tree`/`swunl_dict` qua `initargs` (pickle/copy), nên **nhiều worker ⇒ nhiều RAM**. Với 64 GB, 8–12 worker thường ổn cho dataset vừa; dataset lớn (Kosarak/Accidents) nên giữ thấp.
  - `MAX_MEMORY_USAGE_MB = 45000` (dòng 53) đặt cho "Runtime 51GB". c2-standard-16 có 64 GB ⇒ có thể nâng lên ~55000 nếu cần, hoặc giữ nguyên cho an toàn.
- **Rủi ro cần biết:** `initargs` pickle cả cây WUN sang từng worker; với dataset rất lớn, chi phí pickle + bộ nhớ nhân theo số worker là điểm nghẽn chính. Đây là lý do trần 4 worker được đặt ngay từ đầu — **giữ nguyên trần khi mới port sang GCP**, chỉ nới sau khi đo RAM thực tế.

### Tóm tắt Câu 2
- **Chỉ 2 dòng bắt buộc sửa** (10–11) để chạy ngoài Colab; bọc `try/except ImportError`.
- PART 3 **không có** phụ thuộc Colab nào khác ngoài path; **không** magic/tqdm/display.
- Multiprocessing **chạy nguyên trạng trên c2-standard-16** (fork Linux, chốt 4 worker). Không bắt buộc chỉnh; muốn nhanh hơn thì nới `NUM_WORKERS` có kiểm soát RAM.

---

## Phụ lục — bảng vị trí công thức tw (đối chiếu nhanh)

| Pha | Hàm | Dòng | Công thức tw | Dùng qty? |
|---|---|---|---|---|
| Mining | `compute_tw_optimized` | 214–215 | `Σ(w×qty) / |T|` | **CÓ** |
| Sanitization (HF) | `_delete_item` | 468 | `Σw / |t|` | Không |
| Sanitization (MC) | `_is_safe` / `_delete_item` | 543 / 557 | `Σw / |rem|` (hoặc `/|t|`) | Không |
| Re-mine (metric) | `compute_tw_optimized` | 214–215 | `Σ(w×qty) / |T|` | **CÓ** |

⇒ Bất nhất tập trung ở việc mining/re-mine có qty còn deletion loop thì không — vô hại khi qty≡1, sai lệch khi qty>1.
