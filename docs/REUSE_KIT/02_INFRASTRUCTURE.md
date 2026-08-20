# REUSE_KIT — 02 INFRASTRUCTURE

Hạ tầng thực nghiệm tái dùng được — **không kèm thuật toán ẩn của bài cũ**. Đây là phần
"khung chạy thí nghiệm" mà bài mới có thể bê nguyên: cách tổ chức chạy, checkpoint/resume,
đo metric utility tổng quát, và scheme lưu kết quả.

---

## 1. Coordinator pattern (chạy tuần tự + checkpoint + resume + push)

Mẫu thật trên branch hiện tại: `tools/run_all_batteries.py`. Bản "thế hệ mới" (per-cell,
mịn hơn): `tools/run_compare_xistd.py` + `tools/run_sensitivity_full.py` (branch
`exp/sensitivity-hide-eval`). Cùng một khuôn:

**Cấu trúc:**
- **Danh sách đơn vị công việc** (cell) chạy theo thứ tự **nhẹ → nặng** (fast first), ví dụ
  `RUN_ORDER = ["chess","mushroom","retail","chainstore","accident","kosarak","bms-pos"]`.
- **Checkpoint file** (`tools/coordinator_checkpoint.json`, hoặc `progress_<ds>.json` per
  cell): ghi cell nào đã xong + số attempt. Ghi **atomic** (ghi file tạm rồi `os.replace`).
- **Resume = idempotent**: chạy lại script → đọc checkpoint / kiểm tra file kết quả tồn tại
  → **bỏ qua cell đã done**, tiếp cell dở. Không phụ thuộc tiến trình còn sống.
- **Commit + push sau mỗi cell** ngay khi xong (đề kháng mất máy giữa chừng). **Một
  người ghi git duy nhất = coordinator** (tránh đua ghi).
- **Đếm attempt chống reboot**: tăng bộ đếm attempt **trước** khi chạy cell (pre-increment
  + push), tới ngưỡng `MAX_REBOOT_ATTEMPTS` thì cell được chốt trạng thái "blocked/partial"
  thay vì lặp vô hạn.
- **Retry mạng**: `git pull/push` thử lại 4 lần, backoff mũ (2s,4s,8s,16s).

**Watchdog** (`tools/*watchdog*.sh`, `monitor_and_intervene.sh`): `flock` giữ 1 instance;
vòng lặp gọi coordinator, **tự khởi động lại tối đa N lần nếu coordinator crash** (exit≠0);
coordinator exit 0 = xong hết → dừng. Reboot VM giết cả watchdog+con → lần khởi động thủ
công sau reset bộ đếm restart, nên "N restart liên tiếp trong 1 watchdog" tự nó là bằng
chứng lỗi thật (không phải reboot).

**Chạy nền độc lập agent** (sống sót khi phiên agent kết thúc):
```
setsid nohup bash tools/<watchdog>.sh > /dev/null 2>&1 < /dev/null & disown
```
→ tiến trình thành session leader (PPID về init=1), độc lập terminal.

> Bài mới tái dùng **nguyên khuôn này**, chỉ thay "chạy cell = gọi thuật toán ẩn cũ" bằng
> "chạy cell = gọi thuật toán MỚI của bạn". Toàn bộ phần checkpoint/resume/push/watchdog
> là hạ tầng thuần, không dính đóng góp bài cũ.

---

## 2. Metric framework

Đo trong `SanitizedDBEvaluator.comprehensive_evaluation()` (`run_experiments.py`). Công
thức đọc trực tiếp từ code (không diễn giải lại):

Ký hiệu: TU(t)=Σ_{i∈t} w(i)·qty(i,t); "pattern" = itemset FWUP; `orig`=DB gốc,
`san`=DB đã chỉnh sửa.

| Metric | Công thức (từ code) | Tái dùng cho bài mới? |
|---|---|---|
| **HF** Hiding Failure | \|sensitive ∩ patterns(san)\| / \|sensitive(orig)\| | **[ĐẶC THÙ]** — chỉ có nghĩa cho bài toán "ẩn". Bỏ nếu bài mới không phải hiding. |
| **MC** Missing Cost | \|nonsensitive(orig) − patterns(san)\| / \|nonsensitive(orig)\| | **[TÁI DÙNG]** — "mất pattern hợp lệ" (side-effect của mọi phép chỉnh DB) |
| **AC** Artificial Cost | \|patterns(san) − patterns(orig)\| / \|FWUP(orig)\| | **[TÁI DÙNG]** — "pattern giả sinh ra" |
| **DUS** DB Utility Similarity | min( Σ_t TU_san(t) / Σ_t TU_orig(t), 1 ) | **[TÁI DÙNG]** — bảo toàn utility tổng của DB |
| **IUS** Itemset Utility Similarity | min( Σ_Y u_san(Y) / Σ_Y u_orig(Y), 1 ),  u(Y)=Σ_{T⊇Y} TU(T) | **[TÁI DÙNG]** — bảo toàn utility của tập pattern |
| **TMR** Transaction Modification Rate | #giao dịch bị sửa / #tổng giao dịch | **[TÁI DÙNG]** — mức can thiệp DB |
| **DDI** DB Distortion Index | #giao dịch bị **xóa item** / #tổng giao dịch | **[TÁI DÙNG]** — mức méo DB |
| **RT** Runtime | wall-clock **chỉ pha xử lý** (đo trước khi eval) | **[TÁI DÙNG]** — quy ước tách RT |

**Điểm tái dùng mạnh**: MC/AC/DUS/IUS/TMR/DDI là **metric utility-mining tổng quát** cho
"đo tác động của một phép biến đổi DB lên tập pattern & utility" — độc lập với việc bạn ẩn,
nén, ẩn danh, hay biến đổi gì. Chỉ cần:
1. `patterns(orig)` / `patterns(san)` = FWUP mine trên DB gốc/mới (dùng lại miner).
2. TU per-transaction (công thức trên).
> HF gắn chặt khái niệm "sensitive pattern" của bài ẩn → cân nhắc bỏ/định nghĩa lại theo
> đóng góp mới.

**Quy ước RT quan trọng**: `execution_time` được chốt **ngay sau pha xử lý chính, TRƯỚC khi
dựng evaluator** → RT không lẫn thời gian re-mine/đánh giá. Nếu bài mới cần "thời gian thuật
toán" sạch, giữ đúng quy ước này. Bước eval (re-mine tính MC/AC/IUS) **không** có deadline —
chạy tới xong.

---

## 3. Scheme kết quả (thư mục / đặt tên / CSV)

- **Per-cell JSON**: `<exp>_results/result_<dataset>_<method>.json` — 1 file/ô, chứa đủ
  metric + `source` + `status`. Cho phép resume theo sự tồn tại file.
- **Progress per-dataset**: `<exp>_results/progress_<dataset>.json` = `{done:{}, attempts:{}}`.
- **CSV tổng hợp**: regenerate từ toàn bộ JSON sau mỗi cell, cột chuẩn:
  `dataset, method, HF, MC, AC, IUS, DUS, TMR, DDI, RT, source, status`.
  (Ví dụ thật: `compare_xistd_results/compare_xistd.csv`.)
- **Cột `source`**: gắn provenance mỗi số (`reused_*` / `fresh_*`) để minh bạch tái dùng.
- **Cột `status`**: `done` / `partial` / `*_reboot_blocked` … để phân biệt số đo thật vs
  số bị chặn bởi hạ tầng.

---

## 4. Môi trường

- **Python**: 3.11 (đo được: **3.11.15**).
- **Thư viện ngoài**: `numpy`, `psutil` (đọc từ import thật trong `run_experiments.py`).
  Còn lại là stdlib: `collections, concurrent, copy, dataclasses, functools, gc, itertools,
  json, logging, math, multiprocessing, os, random, statistics, subprocess, sys, time,
  traceback, typing`.
- ⚠️ **Không có `requirements.txt`** trên branch hiện tại → bài mới nên tạo mới
  (`numpy`, `psutil` tối thiểu; thêm `openpyxl` nếu xuất `.xlsx`). **[CẦN NGƯỜI DÙNG XÁC NHẬN]**
  phiên bản pin.
- **Quirk môi trường (VM recycle)**: môi trường chạy nền có thể **reboot bất chợt** (uptime
  reset về 0, filesystem clone lại). Vì vậy toàn bộ pattern ở §1 (checkpoint + push per cell
  + resume idempotent + watchdog) là **bắt buộc** cho job dài — không phải tùy chọn. Ô nào
  cần thời gian > cửa sổ recycle phải có cơ chế "blocked/partial" để không kẹt.
- **Xác định reboot vs crash**: `uptime`≈0 + không có dòng `Out of memory/Killed process`
  trong `dmesg` ⇒ recycle hạ tầng (không sửa được phía mình); có OOM-kill trong `dmesg`
  ngay trước ⇒ tiến trình mình gây (sửa được: giảm RAM/deadline).
- **Đơn luồng ghi git** + log runtime để `.gitignore` (xem `03_REPO_STRUCTURE.md`).
