# REUSE_KIT — 03 REPO STRUCTURE (đề xuất cho repo MỚI)

Cây thư mục chuẩn để bắt đầu repo bài báo mới: giữ lại phần hạ tầng + dữ liệu, bỏ phần
thuật toán/kết quả bài cũ.

---

## 1. Cây thư mục đề xuất

```
<repo-moi>/
├── README.md                     # xem §3
├── requirements.txt              # numpy, psutil, (openpyxl nếu xuất xlsx)
├── .gitignore                    # xem §2
│
├── datasets/                     # [TÁI DÙNG NGUYÊN] copy từ repo cũ
│   ├── chess_fimi_quantities.txt / chess_fimi_weights.txt
│   ├── mushroom_quantities.txt   / mushroom_weights.txt
│   ├── bms-pos_quantities.txt    / bms-pos_weights.txt      # bản SẠCH
│   ├── retail_quantities.txt     / retail_weights.txt
│   ├── chainstore_quantities.txt / chainstore_weights.txt
│   ├── accident_quantities.txt   / accident_weights.txt
│   ├── kosarak_quantities.txt    / kosarak_weights.txt
│   └── (accident|chainstore|kosarak).zip                    # bản nén nguồn
│
├── src/                          # code bài MỚI
│   ├── data_loader.py            # port load_transactions/weights + TU() (§01_DATASET §4)
│   ├── metrics.py                # port MC/AC/DUS/IUS/TMR/DDI (bỏ/định nghĩa lại HF) (§02 §2)
│   ├── miner.py                  # miner FWUP (nếu tái dùng) — [CẦN XÁC NHẬN nguồn]
│   └── <thuat_toan_moi>.py       # đóng góp MỚI của bạn
│
├── calibration/                  # ngưỡng ξ per-dataset
│   ├── calibrate.py              # script tính ξ chuẩn + sweep ×mult
│   └── calib_<ds>_<mult>.json    # output (đóng băng pattern để tái lập)
│
├── experiments/                  # coordinator + config
│   ├── config.py                 # bảng per-dataset: file names + ξ mining (port ExperimentManager)
│   ├── run_coordinator.py        # port pattern §02 §1 (fast→slow, checkpoint, resume, push)
│   └── watchdog.sh               # port §02 §1 (flock + auto-restart)
│
├── results/                      # KẾT QUẢ MỚI (rỗng lúc đầu)
│   ├── result_<ds>_<method>.json # per-cell
│   ├── progress_<ds>.json        # checkpoint
│   └── summary.csv               # regenerate từ JSON: dataset,method,<metrics>,RT,source,status
│
└── docs/
    └── REUSE_KIT/                # copy nguyên bộ này để tham chiếu gốc dữ liệu
```

Nguyên tắc đặt tên (giữ từ repo cũ vì đã chứng minh hợp lý):
- File dữ liệu: `<dataset>_quantities.txt` / `<dataset>_weights.txt`.
- Kết quả per-cell: `result_<dataset>_<method>.json`; checkpoint: `progress_<dataset>.json`.
- CSV tổng: 1 hàng/ô, có cột `source` (provenance) + `status`.
- Thư mục kết quả theo thí nghiệm: `<ten_thi_nghiem>_results/`.

---

## 2. `.gitignore` chuẩn đề xuất

Dựa trên `.gitignore` thật của repo cũ (bỏ log runtime + cache mining + lock; **giữ**
checkpoint JSON vì đó là dữ liệu resume thật):

```gitignore
# Python
__pycache__/
*.pyc
_sfwup_core.py            # (chỉ nếu mang lại core cũ — thường KHÔNG)

# Log runtime (checkpoint đã commit mới là dữ liệu thật)
MyLogs/*.log
**/*.log

# Cache mining (regenerate tự động)
**/fwups_cache_*.json

# Coordinator live-log + lock (single git writer = coordinator)
experiments/*.log
experiments/.*.lock
tools/*.log
tools/.*.lock
```

> Ghi nhớ: **checkpoint/progress JSON KHÔNG ignore** (chúng mang tiến độ thật, phải push).
> Chỉ ignore file *live-log* và *.lock* — chúng regenerate và gây nhiễu git.

---

## 3. README nên có mục gì

1. **Tiêu đề + tóm tắt đóng góp MỚI** (1 đoạn) — KHÔNG chép mục "Key Contributions" của bài
   cũ (RISWU/SDIF/Sub-Alg 3.4).
2. **Datasets**: bảng 7 dataset + thống kê (bê từ `01_DATASET.md` §2) + ghi rõ bms-pos là
   bản đã làm sạch.
3. **Cách chạy**: `pip install -r requirements.txt` → calibrate → `run_coordinator.py` →
   đọc `results/summary.csv`.
4. **Metrics**: bảng metric dùng (bê từ `02_INFRASTRUCTURE.md` §2), nêu rõ cái nào định
   nghĩa lại cho bài mới.
5. **Reproducibility**: seed cố định (repo cũ dùng `seed=42`), checkpoint/resume, môi trường
   (Python 3.11, numpy/psutil).
6. **Cấu trúc thư mục** (bê §1 ở trên).
7. **Provenance**: nêu dataset & khung hạ tầng kế thừa từ repo luận văn cũ (trích dẫn), thuật
   toán là đóng góp mới.
