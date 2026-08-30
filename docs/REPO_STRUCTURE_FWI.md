# REPO STRUCTURE — Repo FWI Hiding (IoT-63257-2026)

> Bám handoff §5.3 (cấu trúc a — tách module). Tài liệu thiết kế — mang về control duyệt trước khi tạo
> repo thật. Nhất quán với SPEC_PART4_HIDING.md và CLAUDE.md (bản đã sửa 4 vòng).

---

## 1. Cây thư mục
```
FWI_hiding_system/
├── CLAUDE.md                       # chỉ dẫn agent (deliverable 1)
├── README.md                       # §3
├── requirements.txt                # numpy, psutil  (+ openpyxl nếu xuất xlsx)
├── .gitignore                      # §2
│
├── config/
│   └── experiment_config.py        # per-dataset: file names, ξ (≤3dp), |S|, timeout,
│                                    #   NUM_WORKERS=4, seed=42, cờ order/safe_check; RUN_ORDER fast→slow
│
├── src/
│   ├── mining/                     # PART 3 — gỡ Colab + 2 fix SPEC_PART3_FIX, KHÔNG đổi logic khác (Q9)
│   │   └── miner.py                #   weighted N-list/SWU-N-list FWI miner [21] (port từ v38; gỡ Colab;
│   │                               #   sửa 2 chỗ theo SPEC_PART3_FIX: tw bỏ qty + swunl_intersection tidset)
│   ├── hiding/
│   │   ├── common.py               #   tw / ws / delete / inverted index / backend số  (SPEC §2)
│   │   ├── select_victim.py        #   helper two-stage ĐÃ KHÓA (Việc 0 chốt — SPEC §3.5)
│   │   ├── hfpriority.py           #   SPEC §3.2
│   │   ├── mcpriority.py           #   SPEC §3.3 (Safe toàn ~S + no-op; safe_check/order tham số hóa)
│   │   └── baseline_ppum.py        #   Q10 — adapt PPUM-HUIM (spec riêng, sau)
│   ├── metrics/
│   │   └── metrics.py              #   HF, MC, AC, RT trên tw/ws (SPEC §5). KHÔNG IUS/DUS/TMR/DDI.
│   └── datautil/
│       └── preprocess.py           #   load + /10 + bỏ qty + kiểm định dạng (SPEC §4)
│
├── calibration/
│   ├── calibrate.py                #   tính ξ chuẩn per-dataset THEO ĐỊNH NGHĨA FWI (không tái dùng
│   │                               #     ξ cũ — ξ cũ tính trên utility+qty, sai regime; xem §4)
│   └── calib_<ds>.json             #   output: ξ (≤3dp), #FWI, #SFWI (đóng băng để tái lập)
│
├── coordinator/
│   └── run_coordinator.py          #   ô tuần tự, checkpoint+push mỗi ô, resume skip
│
├── datasets/                       # [TÁI DÙNG NGUYÊN] copy từ repo cũ (7 + IoT tĩnh Q7)
│   ├── chess_*.txt  mushroom_*.txt  bms-pos_*.txt  retail_*.txt
│   ├── chainstore_*.txt  accident_*.txt  kosarak_*.txt        # bms-pos: bản SẠCH
│   └── <iot>_quantities.txt  <iot>_weights.txt                # Q7 — CẦN CHỌN dataset
│
├── results/                        # KẾT QUẢ MỚI (rỗng lúc đầu)
│   ├── result_<ds>_<method>.json   #   per-ô: HF, MC, AC, RT, #no-op, #safe-blocked, source, status
│   ├── progress_<ds>.json          #   checkpoint {done, attempts}
│   └── summary.csv                 #   regenerate từ JSON
│
├── logs/                           # live-log (đã .gitignore)
├── figures/                        # hình cho bài
│
├── tests/
│   └── oracle_bruteforce.py        # G6 oracle độc lập (Apriori tidset; KHÔNG import engine)
│
└── docs/
    ├── CONTEXT_HANDOFF_PHA2.md
    ├── SPEC_PART4_HIDING.md         # deliverable 2
    ├── SPEC_PART3_FIX.md            # sửa engine PART 3 đúng 2 chỗ (tw + swunl_intersection)
    ├── CHUNG_MINH_A1_A3_C5.md       # chứng minh lý thuyết — CÓ SẴN trong project
    └── FORMALISM_COMPLEXITY_V0_B2_B3_C.md   # complexity — CÓ SẴN trong project
```

Khác biệt cố ý (vì bài FWI): tách `src/hiding/ metrics/ datautil/`; thêm `select_victim.py` (helper
two-stage đã khóa) và `common.py` (gom `delete`); `metrics.py` chỉ 4 metric FWI; `calibrate.py` tính
lại ξ theo FWI.

---

## 2. `.gitignore`
```gitignore
# Python
__pycache__/
*.pyc
# Log runtime (checkpoint đã commit mới là dữ liệu thật)
logs/*.log
**/*.log
# Cache mining (regenerate tự động)
**/fwi_cache_*.json
# Coordinator live-log + lock (single git writer = coordinator)
coordinator/*.log
coordinator/.*.lock
```
> **KHÔNG ignore** `results/*.json` và `calibration/*.json` — tiến độ/kết quả thật, phải push.

---

## 3. README nên có
1. Tiêu đề + tóm tắt đóng góp MỚI (HFPriority/MCPriority ẩn FWI). Không chép contributions bài cũ.
2. **Datasets:** bảng 7 dataset + thống kê + IoT dataset (Q7); ghi rõ bms-pos là bản đã làm sạch.
3. **Định nghĩa FWI** (tw=Σw/|T|, ws, ξ) — nêu rõ **không dùng quantity**.
4. **Cách chạy:** `pip install -r requirements.txt` → `calibrate.py` → `run_coordinator.py` → đọc
   `results/summary.csv`.
5. **Metrics:** HF/MC/AC/RT (định nghĩa trên ws) — nêu rõ khác metric utility repo cũ.
6. **Backend số:** golden/calibration = Fraction; production = float64 + `round(ws,3)≥ξ`; ξ ≤ 3dp.
7. **Reproducibility:** seed=42, checkpoint/resume, môi trường (Python 3.11, numpy/psutil), 1 máy GCP.
8. **Provenance:** dataset + khung hạ tầng kế thừa repo cũ (trích dẫn); thuật toán là đóng góp mới.

---

## 4. ξ KHÔNG tái dùng trực tiếp (điểm dễ sai)
ξ chuẩn cũ (chess 0.89, mushroom 0.40, …) tính trên **utility+qty** (regime khác định nghĩa FWI). Sau
khi sửa tw (bỏ qty) + /10, cùng một ξ số sẽ ra **số FWI khác hẳn**. → phải **recalibrate** ξ per-dataset
theo định nghĩa FWI mới; ξ cũ chỉ là điểm khởi đầu tham khảo. chainstore: ξ cũ lệch nguồn (0.007 config
vs 0.003 csv) — bỏ, calibrate lại từ đầu.

---

## 5. CẦN QUYẾT ĐỊNH — còn đúng 2 mục (cần Trung, ngoài Q1–Q10/§3)
1. **IoT dataset tĩnh (Q7):** chọn dataset nào (tên / nguồn / kích thước).
2. **Target #FWI/#SFWI mỗi dataset** để calibrate ξ quanh đó.

Đã tự đóng: vị trí `CHUNG_MINH_*` và `FORMALISM_COMPLEXITY_*` — **cả hai có sẵn trong project**, copy
thẳng vào `docs/`. Baseline PPUM-HUIM (Q10): nguồn `Efficient…hiding sensitive high utility itemsets.pdf`
có trong project — cấu trúc `baseline_ppum.py` là việc riêng sau, không chặn PART 4.
