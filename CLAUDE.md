# CLAUDE.md

> File này đặt ở GỐC repo. Claude Code tự đọc khi làm việc trong repo.
> PHẦN A = 4 nguyên tắc hành xử khi code (theo Karpathy — giảm sai lầm phổ biến của LLM).
> PHẦN B = quy ước riêng của repo này (dataset + hạ tầng kế thừa, ranh giới bài cũ). Điền `<...>`.
>
> **Tradeoff:** các nguyên tắc này thiên về CẨN TRỌNG hơn tốc độ. Task tầm thường (sửa typo, one-liner
> hiển nhiên) → dùng phán đoán, không cần full rigor.

---

# PHẦN A — 4 NGUYÊN TẮC HÀNH XỬ KHI CODE

## A1. Think Before Coding — Nghĩ trước khi code
**Đừng giả định. Đừng giấu chỗ khó hiểu. Nêu tradeoff.**

Trước khi implement:
- Nêu RÕ giả định của mình. Nếu không chắc → HỎI, đừng đoán.
- Nếu có nhiều cách hiểu → trình bày ra, ĐỪNG tự chọn thầm.
- Nếu có cách đơn giản hơn → nói ra. Push back khi có cơ sở.
- Nếu có gì chưa rõ → DỪNG. Gọi tên cái đang mập mờ. Hỏi.

## A2. Simplicity First — Đơn giản trước
**Code tối thiểu giải quyết đúng vấn đề. Không gì đầu cơ/phòng xa.**

- Không thêm tính năng ngoài cái được yêu cầu.
- Không abstraction cho code chỉ dùng 1 lần.
- Không "linh hoạt"/"cấu hình được" mà không ai xin.
- Không error-handling cho tình huống bất khả.
- Viết 200 dòng mà 50 dòng đủ → viết lại.

Tự hỏi: "Một senior engineer có nói cái này rối rắm quá không?" Nếu có → đơn giản hóa.

## A3. Surgical Changes — Sửa đúng phần cần
**Chỉ chạm cái BẮT BUỘC phải chạm. Dọn đúng phần mình bày ra.**

Khi sửa code có sẵn:
- Đừng "cải thiện" code/comment/format lân cận.
- Đừng refactor thứ không hỏng.
- Khớp style hiện có, kể cả khi mình thích làm khác.
- Thấy dead code không liên quan → NÊU ra, ĐỪNG xóa.

Khi thay đổi của mình tạo orphan:
- Xóa import/biến/hàm mà THAY ĐỔI CỦA MÌNH làm thừa.
- KHÔNG xóa dead code có sẵn từ trước trừ khi được yêu cầu.

Kiểm: mỗi dòng thay đổi phải truy thẳng về yêu cầu của người dùng.

## A4. Goal-Driven Execution — Chạy theo mục tiêu verify được
**Chốt tiêu chí thành công. Lặp tới khi verify đạt.**

Chuyển task mệnh lệnh thành mục tiêu verify được:
- "Thêm validation" → "Viết test cho input sai, rồi làm nó pass"
- "Sửa bug" → "Viết test tái hiện bug, rồi làm nó pass"
- "Refactor X" → "Đảm bảo test pass trước VÀ sau"

Task nhiều bước → nêu plan ngắn:
```
1. [Bước] → verify: [kiểm gì]
2. [Bước] → verify: [kiểm gì]
3. [Bước] → verify: [kiểm gì]
```
Tiêu chí mạnh cho phép loop độc lập. Tiêu chí yếu ("làm cho chạy") gây hỏi tới hỏi lui.

**Các nguyên tắc này ĐANG hiệu quả nếu:** diff ít thay đổi thừa, ít phải viết lại do rối rắm, câu
hỏi làm rõ đến TRƯỚC khi implement (không phải sau khi đã sai).

> Ví dụ chi tiết ❌ sai vs ✅ đúng cho từng nguyên tắc: xem `docs/EXAMPLES.md` (bản gốc Karpathy —
> ví dụ code minh họa; nguyên tắc phổ quát, dù ví dụ là code web).

---

# PHẦN B — QUY ƯỚC RIÊNG CỦA REPO NÀY

## 1. REPO NÀY LÀ GÌ

- Bài báo: **<tên bài mới>** — lĩnh vực <data mining / ...>. Đóng góp mới: <mô tả 1 dòng>.
- Kế thừa từ dự án cũ: 7 dataset (đã làm sạch) + khung hạ tầng chạy thực nghiệm (coordinator,
  metric utility tổng quát, scheme kết quả). KHÔNG kế thừa thuật toán/kết quả bài cũ.
- Trạng thái sự thật nằm trong FILE (không dựa trí nhớ phiên): master plan `<PLAN_*.md>`,
  `results/progress_*.json`, `results/summary.csv`. Mở phiên mới → đọc các file này trước.

## 2. CẤU TRÚC & VỊ TRÍ

```
datasets/           # 7 dataset FIMI (*_quantities.txt, *_weights.txt) — DÙNG LẠI, bản sạch
src/                # code bài mới: data_loader.py, metrics.py, miner.py, <thuat_toan_moi>.py
calibration/        # calibrate.py + calib_<ds>_<mult>.json (ξ per-dataset)
experiments/        # config.py, run_coordinator.py, watchdog.sh
results/            # kết quả MỚI: result_<ds>_<method>.json, progress_<ds>.json, summary.csv
docs/REUSE_KIT/     # tài liệu gốc dữ liệu/hạ tầng kế thừa (tham chiếu)
```

## 3. LỆNH THƯỜNG DÙNG

```bash
# Môi trường
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Calibrate ξ per-dataset (chạy lại cho ĐỊNH NGHĨA MỚI — không tái dùng pattern đóng băng cũ)
python calibration/calibrate.py

# Chạy thực nghiệm QUA coordinator (KHÔNG chạy script thuật toán trần)
python experiments/run_coordinator.py

# Xem tiến độ (pgrep là sự thật, không dựa log mtime)
pgrep -f run_coordinator && tail -4 results/progress_*.json
```

## 4. QUY ƯỚC BẮT BUỘC (chắt từ bài học dự án cũ)

- **Chạy ô TUẦN TỰ** (song song chỉ trong 1 ô) → runtime defensible, không tranh tài nguyên.
- **Checkpoint + commit/push mỗi ô.** Resume tự SKIP ô đã xong (idempotent). MỘT git writer =
  coordinator.
- **CHẠY THẬT, không suy luận.** Không "ghi-theo-verify" baseline (baseline có thể đổi theo tham số).
- **RT = wall-clock chỉ pha xử lý chính**, chốt TRƯỚC khi eval/re-mine. Eval không có deadline.
- **Metric utility tổng quát tái dùng:** MC/AC/DUS/IUS/TMR/DDI (đo tác động biến đổi DB). HF là
  ĐẶC THÙ bài ẩn cũ → BỎ hoặc định nghĩa lại cho bài mới.
- **Job dài chạy nền chịu rớt SSH:** `setsid nohup ... & disown`, verify PPID=1. Watchdog auto-restart.
- **Quy trình 3 bước trước mẻ lớn:** chuẩn bị (verify lưới ô + logging đủ cột) → smoke (ô khó nhất)
  → phóng. KHÔNG phóng mù.

## 5. RANH GIỚI — KHÔNG ĐỤNG / KHÔNG MANG (từ dự án cũ)

- **KHÔNG mang logic bài cũ:** RISWU, SWM (`_apply_swm_to_hide`), SDIF/Max/Min-RISWU, Sub-Alg 3.4,
  baseline SMSE/MSU-MIU bản-adapt-cũ, HF, SFWUP đóng băng. Baseline mới → adapt LẠI từ gốc literature.
- **KHÔNG mang kết quả/số liệu bài cũ** (final_results, GĐ1/GĐ2, escalation/stress CSV) — sẽ nhầm
  là kết quả bài mới.
- **KHÔNG tái dùng danh sách pattern đóng băng** (calib/sfwups cũ). Giá trị **ξ chuẩn** (tham số
  dataset) thì tham khảo được, nhưng phải **re-mine** pattern theo định nghĩa MỚI.
- **KHÔNG rebase/force/amend** trên branch đang chạy thực nghiệm.
- **KHÔNG commit** log runtime/cache/lock (xem .gitignore). Checkpoint JSON thì PHẢI commit.

## 6. DATASET (dùng lại — chi tiết ở docs/REUSE_KIT/01_DATASET.md)

7 dataset, đọc bằng `src/data_loader.py` (format `item:qty` / `item:weight`, item là string key).
Dense: chess/mushroom/accident. Sparse: retail/kosarak/chainstore/bms-pos. bms-pos là bản ĐÃ LÀM
SẠCH (515,596 giao dịch — dùng bản .txt sạch, không đọc CSV gốc). Dataset lớn nạp hết vào RAM
(cần ≥16GB). Thống kê đầy đủ + quirk: xem docs/REUSE_KIT/01_DATASET.md.

## 7. CẦN CHỐT KHI KHỞI TẠO (đánh dấu từ REUSE_KIT)

- [ ] chainstore ξ chuẩn: 0.007 (config cũ) vs 0.003 (results cũ) — chốt số cho bài mới.
- [ ] requirements.txt: pin version (numpy, psutil tối thiểu; openpyxl nếu xuất xlsx).
- [ ] Định nghĩa "đối tượng quan tâm" của bài mới (thay SFWUP cũ) → calib lại theo đó.
- [ ] Nếu cần calibrate/pipeline bms-pos: lấy script từ branch cũ (exp/sensitivity-hide-eval,
      fix/bms-pos-data).
