# INVESTIGATE_REPO.md

Điều tra chỉ-đọc codebase cho bài báo *"Efficient Methods for Hiding Frequent Weighted Itemsets"* (HFPriority & MCPriority, hướng item-deletion).
Ngày điều tra: 2026-08-20. Không sửa/chạy code; toàn bộ phân tích bằng đọc tĩnh.

> **TÓM TẮT NHANH (đọc trước khi làm gì)**
> - Repo chỉ có **2 file**: `fwi_hiding_system_v38 (3).py` (966 dòng) và bản notebook tương đương `FWI_hiding_system_v38.ipynb`. **Không có dataset, không có file kết quả, không có baseline** trong repo.
> - **KHÔNG CÓ BASELINE** — chỉ so sánh HFPriority vs MCPriority với nhau (xem Mục 3).
> - **KHÔNG có multi-run / std / confidence interval** — mỗi (dataset, thuật toán) chạy đúng 1 lần (xem Mục 4).
> - **Công thức scoring trong code KHÔNG khớp mô tả bài báo** (`|SCov|·w` và `1/(NSCov+1)`). Code dùng cách chọn nạn nhân khác — xem Mục 2. **Đây là điểm cần đối chiếu kỹ với bản thảo.**
> - File kết quả `fwi_v38_dual_results.json` **nằm trên Google Drive, không có trong repo** → không thể xác minh số HF/AC/MC của Mushroom/Retail từ repo (xem Mục 7).

---

## 1. CẤU TRÚC TỔNG THỂ

### Cây thư mục (đã bỏ .git/__pycache__/.venv)
```
FWI_hiding_system/
├── FWI_hiding_system_v38.ipynb      # Notebook Colab (11 cells) — bản gốc
└── fwi_hiding_system_v38 (3).py     # Bản export .py của notebook (966 dòng) — dùng để đọc
```
Đó là **toàn bộ** repo. Không có thư mục `Datasets/`, `MyResults/`, `MyLogs/`, không có `requirements.txt`, không có `.gitignore`, không có README, không có test.

### Vai trò file
| File | Vai trò |
|---|---|
| `fwi_hiding_system_v38 (3).py` | Toàn bộ hệ thống trong 1 file: mining engine + 2 thuật toán ẩn + coordinator + metric + visualization. |
| `FWI_hiding_system_v38.ipynb` | Cùng nội dung, chia 11 cell (Part 1–2, Part 3, Part 4, Part 6, Visualization). Code cell trùng khớp với file .py. |

### Bố cục logic bên trong file (theo comment PART)
- **PART 1–2** (dòng 15–111): imports, `OptimizedConfig`, `HidingConfig`, `PathManager`, `setup_logging`.
- **PART 3** (dòng 113–378): *Core FWI Mining Engine* — cây WUN, khai phá Frequent Weighted Itemsets. Comment ghi "DO NOT MODIFY".
- **PART 4** (dòng 380–559): *Hiding Algorithms* — `HFPriorityManager` và `MCPriorityManager`.
- **PART 6** (dòng 561–827): *Main Execution* — helper load dữ liệu, `SimpleSFWISelector`, `evaluate_comprehensive`, coordinator `run_dual_experiment_with_cache`, và `if __name__=="__main__"`.
- **Visualization** (dòng 829–967): đọc JSON kết quả → vẽ 8 hình PNG (seaborn/matplotlib).

### Entry point / `if __name__=="__main__"`
- **Chỉ một** entry point: dòng **826–827**:
  ```python
  if __name__ == "__main__":
      run_dual_experiment_with_cache()
  ```
- Trong notebook, entry point này nằm ở cell 8 (cell chạy chính); cell 10 là code visualization chạy độc lập.

### Coordinator/script điều phối
- **CÓ.** Coordinator là `run_dual_experiment_with_cache()` (dòng 670–824). Cơ chế:
  1. Định nghĩa 7 dataset + ngưỡng min_ws (dict `datasets`, dòng 676–684).
  2. **Resume/cache 2 tầng:**
     - *Tầng kết quả:* nạp `fwi_v38_dual_results.json`; nếu 1 dataset đã có cả 2 thuật toán → **skip** (dòng 705–707).
     - *Tầng mining:* cache kết quả khai phá gốc vào `{dataset}_mining_cache.pkl` (pickle), lần sau nạp lại thay vì mining lại (dòng 718–740).
  3. **Dual-track:** với mỗi dataset, chạy lần lượt `HFPriorityManager` rồi `MCPriorityManager` trên bản deepcopy riêng của giao dịch (dòng 755–809).
  4. Sau sanitize → **re-mine** dataset đã làm sạch để đo metric (dòng 780–782).
  5. Ghi metric vào JSON sau mỗi thuật toán (checkpoint tăng dần), dọn RAM bằng `gc.collect()` + `del`.
  6. Bọc try/except quanh từng thuật toán và từng dataset để không sập cả run; lỗi ghi `{"Error": ...}` vào JSON.

---

## 2. THUẬT TOÁN ĐỀ XUẤT

### Định vị code
| Thuật toán | Class | Dòng | Hàm chính |
|---|---|---|---|
| HFPriority | `HFPriorityManager` ("The Hunter") | 393–470 | `sanitize` (404–459), `_calc_ws` (461–463), `_delete_item` (465–470) |
| MCPriority | `MCPriorityManager` ("The Guardian") | 473–559 | `sanitize` (485–534), `_calc_ws` (536–537), `_is_safe` (539–552), `_delete_item` (554–559) |

Lưu ý tên: bài báo gọi HFPriority/MCPriority; code đặt tên class `...Manager`. Tương ứng nhau.

### ⚠️ Xác nhận công thức scoring — KHÔNG khớp mô tả trong đề bài/bài báo

**Kỳ vọng (đề bài):** `HFPriority = |SCov(v)| · w(v)`, `MCPriority = 1/(NSCov(v)+1)`.
**Thực tế trong code:** không có biểu thức scoring nào dạng đó. Cách chọn giao dịch/nạn nhân như sau:

**HFPriority (`HFPriorityManager.sanitize`, dòng 425–457):**
- Duyệt pattern nhạy cảm theo `ws` **giảm dần** (ẩn cái mạnh trước — dòng 406).
- Vòng lặp xóa `while True` cho tới khi `_calc_ws(s_node) < min_ws`:
  - `candidates` = các tid chứa itemset (dòng 433).
  - **Chọn giao dịch:** sort candidates theo `tw_ref[tid]` **giảm dần** → chọn giao dịch có trọng số giao dịch (tw) lớn nhất (dòng 439).
  - **Chọn item nạn nhân:** trong các item của itemset nhạy cảm có trong giao dịch đó, chọn `victim = max(..., key=item_weights[i])` — **item có trọng số lớn nhất** (dòng 443–445).
  - Xóa đúng **1 item** rồi `break` (chỉ tác động giao dịch đầu tiên mỗi vòng — dòng 447–455).
- ⇒ Tiêu chí thực tế: **max tw giao dịch → max item-weight**. **Không hề tính `|SCov(v)|`** (số giao dịch phủ). ⇒ **LỆCH so với `|SCov(v)|·w(v)`** — cần đối chiếu bản thảo.

**MCPriority (`MCPriorityManager.sanitize`, dòng 485–532):**
- Xây "Safety Net": `nsfwi_map[tid] = [các NSFWI node]` (dòng 489–490).
- Duyệt pattern nhạy cảm theo `ws` **tăng dần** (ẩn cái yếu trước — dòng 492).
- Vòng lặp xóa: `candidates` sort theo `tw_ref[tid]` **tăng dần** (chọn giao dịch tw nhỏ nhất — dòng 515); trong giao dịch, `pool` các item của itemset sort theo `item_weights` **tăng dần** (ưu tiên item weight nhỏ — dòng 519–520).
  - Với mỗi item: **chỉ xóa nếu `_is_safe(...)`** (dòng 522–529); nếu không an toàn → `vetoed += 1` (dòng 530).
- `_is_safe` (dòng 539–552): mô phỏng việc xóa, dự đoán `tsw` mới; với **mọi NSFWI trong giao dịch đó**, nếu ws dự đoán tụt < `min_ws` → **veto (False)**. Đây là **ràng buộc cứng dạng boolean**, **không phải điểm số `1/(NSCov+1)`**.
- ⇒ Tiêu chí thực tế: **min tw → min item-weight, có kiểm tra an toàn NSFWI (veto)**. **LỆCH so với `1/(NSCov(v)+1)`** — code dùng cơ chế veto nhị phân dựa trên NSFWI thay vì hàm ưu tiên nghịch đảo. Cần đối chiếu bản thảo.

> **KẾT LUẬN MỤC 2:** Cả hai công thức scoring nêu trong đề bài **đều không xuất hiện dưới dạng biểu thức** trong code. Code hiện thực bằng heuristic sort + (với MC) veto an toàn. Đây là **khác biệt lớn giữa mô tả và implement**, cần xác minh xem bản thảo mô tả đúng code hay code đã đổi so với công thức bài báo.

### Cơ chế đảm bảo hội tụ (quan trọng cho ablation)
- **Không có counter cap, không có "van escalation".** Có biến `loop_count` trong HFPriority (dòng 424, 450) nhưng **chỉ tăng, không bao giờ dùng làm điều kiện dừng → biến chết**.
- Hội tụ dựa trên: mỗi vòng `while` hoặc **xóa đúng 1 item** (đơn điệu giảm kích thước DB, hữu hạn) hoặc `break`. Điều kiện break:
  - HFPriority: `_calc_ws < min_ws` (đã ẩn) | `not candidates` (kẹt, log "stuck", bỏ pattern — dòng 435–437) | `not hit`.
  - MCPriority: `_calc_ws < min_ws` | `not candidates` | **`not move`** — tức **tất cả item đều bị veto** ⇒ **bỏ pattern mà CHƯA ẩn được** (dòng 532). MC **không có cơ chế escalation** để cưỡng bức xóa khi bị kẹt ⇒ đây chính là nguồn Hiding Failure của MC và là điểm mấu chốt cho ablation dự kiến.
- **Van an toàn duy nhất ở mức toàn cục:** `TIMEOUT = 3600s`, kiểm tra ở cả cấp pattern (dòng 413/496) lẫn cấp vi mô trong vòng while (dòng 427/506); vượt → `status="Timeout"` và dừng.

---

## 3. BASELINE

**KHÔNG CÓ BASELINE.**

- Trong coordinator, danh sách thuật toán chỉ gồm **hai thuật toán đề xuất** (dòng 693–696):
  ```python
  algorithms = [("HFPriorityManager", HFPriorityManager),
                ("MCPriorityManager", MCPriorityManager)]
  ```
- Không có class/hàm nào hiện thực thuật toán ẩn của công trình trước (không có port từ HUIM-hiding, không có FHSAR/HHUIF/MSICF… hay bất kỳ baseline nào).
- Toàn bộ so sánh trong repo là **HFPriority vs MCPriority với nhau** (chính visualization cũng chỉ vẽ 2 series này — dòng 843–846, 859).

> ⚠️ **Thông tin quan trọng cho resubmit:** thiếu baseline độc lập là điểm yếu học thuật rõ rệt (rất có thể liên quan tới lý do reject ở IEEE IoT Journal). Nếu cần so sánh với state-of-the-art, phải **tự bổ sung baseline** — hiện chưa có gì để tái dùng.

---

## 4. METRIC & ĐO ĐẠC

Tất cả metric tính trong `evaluate_comprehensive` (dòng 622–666), so sánh tập itemset (dưới dạng `set of tuple(itemset)`) giữa FWI gốc và FWI re-mine sau khi làm sạch.

| Metric | Dòng | Công thức trong code | Ý nghĩa |
|---|---|---|---|
| **HF** (Hiding Failure) | 632–633 | `len(set_sfwi ∩ set_new) / len(set_sfwi) * 100` | % SFWI **còn sót lại** (vẫn khai phá được) sau sanitize. Thấp = ẩn tốt. |
| **MC** (Misses Cost) | 636–637 | `len(set_nsfwi − set_new) / len(set_nsfwi) * 100` | % NSFWI **bị mất** (tác dụng phụ). |
| **AC** (Artificial Cost) | 640–641 | `len(set_new − set_orig) / len(set_new) * 100` | % itemset mới **là giả** (ghost, không có trong gốc). |
| IUS/IWS | 644–648 | `Σws_new / Σws_orig * 100` | Bảo toàn tổng weighted-support. |
| DUS | 651 | `Σtw_sanitized / Σtw_orig * 100` | Bảo toàn tổng transaction-weight. |
| TMR | 654–655 | `#giao dịch đổi độ dài / #giao dịch * 100` | Tỷ lệ giao dịch bị sửa. |
| DDI | 658–660 | `(items_gốc − items_mới) / items_gốc * 100` | Tỷ lệ item bị xóa. |
| **Runtime** | 665 (= 459/534) | `time.time() - start_time` | Xem dưới. |

### ⚠️ Xác nhận công thức HF (theo yêu cầu)
- Đề bài kỳ vọng: `HF = |SFWI còn lại| / |SFWI ban đầu| * 100`.
- Code (dòng 632–633):
  ```python
  rem_sfwi = set_sfwi.intersection(set_new)          # SFWI còn khai phá được trên D'
  hf = (len(rem_sfwi) / len(set_sfwi)) * 100 if set_sfwi else 0
  ```
- ⇒ **KHỚP.** `set_sfwi` = tập itemset nhạy cảm ban đầu (top-50), `set_new` = tập FWI re-mine trên dataset đã làm sạch. HF = % top-50 nhạy cảm **vẫn còn là FWI** sau khi ẩn. HF=0 nghĩa là ẩn hoàn hảo. (Lưu ý: mẫu số là **50** cố định — số SFWI ban đầu, xem Mục 6.)

### Runtime đo bằng gì / bao trùm pha nào
- Dùng **`time.time()`** (KHÔNG dùng `time.perf_counter()`), đo trong `sanitize()`: `start_time` ở đầu, trả `time.time() - start_time`.
- **Chỉ bao trùm pha sanitize (xóa item)**. **KHÔNG bao gồm:** thời gian mining gốc, re-mine sau làm sạch, load dữ liệu, hay tính metric. Runtime báo cáo = thuần thời gian thuật toán ẩn.

### Std deviation / multi-run / confidence interval
- **KHÔNG CÓ — xác nhận đúng nghi ngờ.**
- Mỗi (dataset, thuật toán) chạy **đúng 1 lần**; không lặp seed, không tính trung bình/độ lệch chuẩn, không khoảng tin cậy. Kết quả lưu là **giá trị đơn** cho mỗi metric. Không có vòng lặp `for run in range(N)` ở bất kỳ đâu.

---

## 5. DATASET & PIPELINE INPUT

### Định dạng đọc dữ liệu
**Giao dịch** — `load_transactions_from_file` (dòng 576–596):
- Đọc theo dòng; mỗi dòng = 1 giao dịch; token cách nhau bằng khoảng trắng.
- Mỗi token: nếu có `:` → `item:qty` (qty ép về `int`); nếu không có `:` → item với **qty mặc định = 1** (dòng 587–592).
- **TID sinh tự động** theo thứ tự dòng: `f"T{i+1}"` (T1, T2, …) — file **không** chứa TID.
- Trả `{tid: {item: qty}}`. → Đây là **định dạng SPMF-style "quantity/utility" dạng text**, item là **chuỗi**.

**Trọng số** — `load_weights_from_file` (dòng 598–612):
- Mỗi dòng: thay `,`→`:` rồi split theo `:`; lấy `weights[parts[0]] = float(parts[1])`.
- ⇒ Chấp nhận cả `item:weight` lẫn `item,weight`. Trả `{item: weight_float}`.

### Weight/profit được sinh thế nào
- **KHÔNG có code sinh weight trong repo.** Weight được **nạp từ file có sẵn** (`{dataset}_weights.txt`), tức đã sinh ở bước tiền xử lý **bên ngoài** repo (không có normal-distribution generator, không có seed sinh weight ở đây).
- `HidingConfig.seed = 42` tồn tại (dòng 66) nhưng **không được dùng** ở bất kỳ đâu trong luồng thực thi → **dead code**. Không thể xác nhận phân phối/seed sinh weight từ repo này.

### Dataset đang dùng + đường dẫn
Định nghĩa trong `run_dual_experiment_with_cache` (dòng 676–684). Thư mục gốc: `PathManager.DATA_PATH` =
`/content/drive/MyDrive/HUTECH/Master/Master_Thesis/Sourcecode/Datasets/fwi_processed_datasets/` (Colab) hoặc `./Datasets/fwi_processed_datasets/` (local).

| Dataset | File giao dịch | File weight | min_ws (ξ) |
|---|---|---|---|
| Retail | `retail_quantities.txt` | `retail_weights.txt` | 0.01 |
| BMS-POS | `bms-pos_quantities.txt` | `bms-pos_weights.txt` | 0.001 |
| Chainstore | `chainstore_quantities.txt` | `chainstore_weights.txt` | 0.007 |
| Kosarak | `kosarak_quantities.txt` | `kosarak_weights.txt` | 0.015 |
| Mushroom | `mushroom_quantities.txt` | `mushroom_weights.txt` | 0.07 |
| Accidents | `accident_quantities.txt` | `accident_weights.txt` | 0.6 |
| Chess | `chess_fimi_quantities.txt` | `chess_fimi_weights.txt` | 0.5 |

> ⚠️ **Không file dataset nào có trong repo** — tất cả nằm trên Google Drive.

### Schema tối thiểu để thêm 1 dataset MỚI (vd dữ liệu IoT tĩnh)
Cần **2 file text** trong `DATA_PATH`, theo đúng convention đặt tên `{tên}_quantities.txt` + `{tên}_weights.txt`:
1. **File giao dịch** — mỗi dòng một giao dịch, các item cách nhau bởi khoảng trắng, mỗi item dạng `item:qty` (qty là số nguyên) hoặc chỉ `item` (mặc định qty=1). Không có header, không có TID (tự sinh T1..Tn). Item là token chuỗi (nên map về mã số nguyên dạng chuỗi để nhất quán).
   Ví dụ một dòng: `12:3 45:1 78:2`
2. **File weight** — mỗi dòng `item:weight` (hoặc `item,weight`), weight là số thực. Phải phủ **mọi item** xuất hiện trong file giao dịch (item thiếu weight sẽ bị coi weight = 0.0 qua `weights.get(item, 0.0)`).
   Ví dụ: `12:0.85`
3. Thêm 1 dòng vào dict `datasets` (dòng 676–684): `"MyIoT": ("myiot_quantities.txt", "myiot_weights.txt", <min_ws>)`.
- (Tùy chọn) Nếu muốn ép mining lại: đừng để file cache `MyIoT_mining_cache.pkl`.

---

## 6. THAM SỐ THỰC NGHIỆM

- **ξ (min_ws / threshold):** **hardcode**, mỗi dataset một giá trị, ngay trong dict `datasets` (dòng 676–684) — xem bảng Mục 5 (0.001 → 0.6). Không đọc từ config/CLI/env. Cùng min_ws được dùng cho: mining gốc, sanitize (`min_ws` trong `_calc_ws`), và re-mine.
- **Số tập nhạy cảm |S| = 50:** `SimpleSFWISelector.select_top_k(fwi_orig, k=50)` (dòng 617, gọi ở 747). Chọn **top-50 FWI theo `ws` giảm dần** làm SFWI; phần còn lại là NSFWI (dòng 749). `k=50` hardcode. ⇒ Mẫu số của HF luôn = 50 (nếu tổng FWI ≥ 50).
- **Timeout 3600s:** `TIMEOUT = 3600` (dòng 698), truyền vào constructor manager (dòng 772), áp dụng **trong pha sanitize** ở cả cấp pattern lẫn cấp vòng-xóa vi mô (dòng 413/427 và 496/506). **Không** áp cho pha mining/re-mine.
- Tham số khác (`OptimizedConfig`, dòng 50–62): `MAX_PATTERN_LENGTH = 7` (giới hạn độ dài itemset khi khai phá), `MAX_MEMORY_USAGE_MB = 45000`, `NUM_WORKERS = min(4, cpu-2)`, `USE_MULTIPROCESSING = True` (mining đa tiến trình; pha sanitize là đơn luồng).

---

## 7. KẾT QUẢ ĐÃ CHẠY

### File kết quả có trong repo?
- **KHÔNG.** Không có JSON/CSV/XLSX/PNG kết quả nào trong repo (repo chỉ có .py + .ipynb).
- Code ghi kết quả ra `fwi_v38_dual_results.json` tại `RESULTS_PATH` =
  `/content/drive/MyDrive/HUTECH/Master/Master_Thesis/Sourcecode/MyResults/fwi_processed_results/` — **trên Google Drive, ngoài repo**.
- Cache mining (`{dataset}_mining_cache.pkl`) cũng nằm trên Drive, không có trong repo.

### Bằng chứng đã chạy (từ output notebook)
Output đã lưu trong `.ipynb`:
- Cell 8 (main): in **"Skipping <dataset> (Both algorithms completed)"** cho **cả 7 dataset** (Retail, BMS-POS, Chainstore, Kosarak, Mushroom, Accidents, Chess) ⇒ **cả 7 dataset đã chạy xong cả 2 thuật toán** trong lần chạy trước (JSON kết quả đã tồn tại trên Drive).
- Cell 10 (visualization): in đã lưu 8 hình `Fig_1..Fig_8` (HF, MC, Chess/Retail/BMS-POS trade-off, AC, IWS, Runtime).
- **Nhưng các output này KHÔNG chứa con số HF/AC/MC nào** — chỉ có dòng "Skipping…" và "Đã lưu: Fig…".

### Đối chiếu số HF/AC/MC (Mushroom, Retail) với bài báo
- **KHÔNG THỂ xác minh từ repo.** File `fwi_v38_dual_results.json` chứa các con số thật **không có trong repo** (nằm trên Drive), và output notebook không in ra giá trị metric.
- Các mốc cần kiểm (HF của Mushroom/Retail; AC Mushroom ~99.9%, AC Retail ~81.8%): **không có nguồn dữ liệu trong repo để đối chiếu.**
- **Hành động đề xuất:** lấy `fwi_v38_dual_results.json` từ Google Drive rồi đối chiếu với bảng số trong bản thảo. Không thể làm bước này chỉ với repo hiện tại.

---

## 8. GIT

- **Branch hiện tại:** `claude/investigate-itemsets-repo-wd1hz4` (branch điều tra). Ngoài ra có `main` (local + `origin/main`).
- **Remote:** `origin` → `https://github.com/TrungDuong83/FWI_hiding_system`.
- **git status:** *sạch* (working tree clean) tại thời điểm bắt đầu điều tra (chỉ file `INVESTIGATE_REPO.md` này là mới được tạo).
- **Log commit (toàn bộ lịch sử — chỉ có 1 commit):**
  ```
  4852a50  Add files via upload   — TrungDuong83 <131349815+TrungDuong83@users.noreply.github.com>, Thu Aug 20 10:16:35 2026 +0700
  ```
  Repo mới chỉ có **1 commit** (upload thủ công 2 file). Không có lịch sử phát triển.
- **.gitignore:** **KHÔNG CÓ** file `.gitignore` (nên nếu về sau thêm `Datasets/`, `MyResults/`, `.pkl`, `__pycache__/`, `.venv/` thì cần tạo mới để tránh commit nhầm dữ liệu/cache lớn).

---

## PHỤ LỤC — Các điểm cần lưu ý khi sửa/chạy lại (không nằm trong 8 mục, nhưng liên quan resubmit)

1. **Phụ thuộc Colab cứng:** dòng 10–11 `from google.colab import drive; drive.mount(...)` chạy ngay khi import ⇒ file .py **không chạy được ngoài Colab** nếu không sửa. `PathManager` có nhánh local (`./`) nhưng `drive.mount` ở đầu file sẽ lỗi trước đó.
2. **HF dùng mẫu số cố định = |S| = 50** — nếu bản thảo định nghĩa HF theo tổng SFWI khác 50 thì cần rà lại.
3. **Runtime chỉ đo pha sanitize**, không gồm mining/re-mine — cần nêu rõ trong bài để tránh hiểu nhầm.
4. **MC có thể bỏ pattern khi bị veto toàn bộ** (không escalation) ⇒ HF của MC > 0 là hành vi thiết kế, không phải bug — chính là mục tiêu ablation.
5. **Không multi-run/std/CI** và **không baseline** là hai thiếu sót phương pháp luận lớn nhất cho một submission tạp chí.
