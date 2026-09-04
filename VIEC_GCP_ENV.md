# VIEC_GCP_ENV.md — PHA 0: Provision + Verify môi trường (§V / GCP)

> Repo: `TrungDuong83/FWI_hiding_system` · Branch: `exp/v5-sectionV` · Commit: `f5d8d20`
> Ngày: 2026-09-04 · Kỹ sư thực thi §V trên GCP VM.
> **Trạng thái: PHA 0 XONG — mọi cổng verify PASS. CHƯA phóng PHA 1 (chờ control).**

---

## 1. Cấu hình VM

| Mục | Giá trị (đo thật) |
|-----|-------------------|
| Máy | GCP **c2-standard-16** |
| vCPU | **16** (`nproc`=16) |
| RAM | **64 GB** (danh nghĩa c2-standard-16; `free -h` báo 62Gi khả dụng) |
| OS | **Ubuntu 22.04.5 LTS** |
| Kernel | Linux 6.8.0-1060-gcp |
| Disk | 49 GB tổng, **43 GB free** (12% dùng) |
| Loại | on-demand (non-preemptible) — theo control verify |
| Python | 3.10.12 (hệ thống) → venv `.venv` |
| Tools | git, tmux, python3-venv: sẵn sàng |
| Working dir | `/home/tvmyfamily2018/FWI_hiding_system` |

**Lưu ý:** thư mục cũ `~/Hiding_SFWUP` là DỰ ÁN KHÁC — không dùng, không verify.

---

## 2. Repo + branch + auth

- Clone: `git clone https://github.com/TrungDuong83/FWI_hiding_system.git` → **EXIT=0**.
- Git auth: credential store đã có sẵn PAT hợp lệ → clone chạy thẳng, KHÔNG cần nhập tay.
- Checkout: `git checkout exp/v5-sectionV` → `git branch --show-current` = **`exp/v5-sectionV`** ✅
- `git status -sb`: `## exp/v5-sectionV...origin/exp/v5-sectionV` (ahead 0). Chỉ `.venv/` untracked.
- HEAD: `f5d8d20 VIEC_SAFE_INCREMENTAL: re-gate + re-smoke (2 blockers cleared)`

---

## 3. Virtualenv + packages

- `python3 -m venv .venv` → OK.
- Cài (pip): **numpy 2.2.6 · pandas 2.3.3 · openpyxl 3.1.5 · psutil 7.2.2 · matplotlib 3.10.9** ✅

---

## 4. VERIFY DATASETS — 7/7 ĐỦ ✅

`datasets/*_quantities.txt` + `*_weights.txt`, đủ 7 dataset (quantities=7, weights=7):

| Dataset | quantities.txt | weights.txt |
|---------|----------------|-------------|
| accident   | 59,322,389 B | 2,750 B |
| bms-pos    | 17,939,857 B | 10,663 B |
| chainstore | 62,425,764 B | 362,196 B |
| chess_fimi | 587,341 B | 370 B |
| kosarak    | 48,869,268 B | 323,171 B |
| mushroom   | 1,001,707 B | 622 B |
| retail     | 5,989,277 B | 122,219 B |

Không thiếu file, không bị gitignore. Calib: `calibration/calib_<ds>.json` ×7 đủ.

---

## 5. GATE NHANH — TẤT CẢ PASS ✅

Cách chạy: `python3 tests/<test>.py` (standalone, entry-guarded, exit≠0 nếu FAIL). Backend Fraction (exact).

| Gate | File | Kết quả | Chi tiết đo thật |
|------|------|---------|------------------|
| **G1** golden nền | test_g1.py | **PASS (EXIT=0)** | W_total=16/5 ✓ ; ws(AC)=3/4 ✓ ; #FWI=9 ✓ ; ScoreHFP{A:9/10,C:7/5,E:1/5} ✓ ; ScoreMCP ✓ ; delete cập nhật W_total (Bẫy#1) ✓ ; ws(AC) 3/4→219/379 strict_dec ✓ |
| **G2** HFPriority | test_g2_hfp.py | **PASS (EXIT=0)** | trace **C@T3→C@T1** ✓ ; HF=0 ✓ ; MC=3/7 lost{ACD,C,CD} ✓ ; AC=0 ✓ |
| **G3** MCPriority | test_g3_mcp.py | **PASS (EXIT=0)** | safe=True **E@T1→C@T2→C@T4** HF=1/2 MC=0 AC=0 residual{AC} ✓ ; safe=False E@T1→E@T2→A@T3 HF=0 MC=4/7 ✓ ; Safe-fixture full=False/reduced=True ✓ ; filter-guard HF=1/2 MC=0 AC=0 ✓ |
| **G-B\*** baseline | test_baseline_golden.py | **PASS 7/7 (EXIT=0)** | G-B1 MAU **A@T3→C@T1** HF=0 MC=4/7 lost{A,ACD,AD,CD} AC=0 ✓ ; MIU C@T3→E@T1 HF=0 MC=2/7 ✓ ; G-B2..G-B7 (non-collapse, dynamic, invariance, fairness, parity, determinism) ✓ |
| **G-C\*** calibration | test_calib_gates.py | **PASS (EXIT=0)** | 7/7 ds: G-C1 #FWI∈[50,300]+#SFWI=clamp ✓ ; G-C2 |X|≥2∧ws>ξ ✓ ; G-C3 max|X|<CAP ✓ ; G-C4 determinism+re-mine khớp json (chess/mushroom/retail) ✓ |

**Trace bắt buộc tái tạo (handoff PHA 0) — khớp CHÍNH XÁC:**
- HFP `C@T3→C@T1` ✅ (G2)
- MCP-safe `E@T1→C@T2→C@T4` ✅ (G3)
- baseline MAU `A@T3→C@T1` ✅ (G-B1)

Không có boundary_mismatch, không gate fail, không sanity sai.

---

## 6. ⚠️ CẦN QUYẾT ĐỊNH (control) — TRƯỚC KHI PHÓNG PHA 1

**`PROMPT_LAUNCH_SECTIONV.md` KHÔNG có trong repo.** `find . -iname '*PROMPT_LAUNCH*'` = rỗng.
Handoff PHA 1 yêu cầu "TUÂN ĐÚNG spec cell-level trong PROMPT_LAUNCH_SECTIONV.md". File này thiếu.

→ **DỪNG, chờ control**: cần chuyển file này vào repo (hoặc chỉ định spec cell-level thay thế) trước khi
phóng 35 cell. KHÔNG tự bịa spec cell-level. (Coordinator `coordinator/run_coordinator.py` có sẵn nhưng
chưa đối chiếu với spec launch — sẽ verify ở đầu PHA 1 sau khi có file.)

Ghi chú phụ (không phải blocker): `.venv/` đang untracked (chưa trong .gitignore) — cần đảm bảo
coordinator KHÔNG commit `.venv/` khi push từng cell. Sẽ xử ở đầu PHA 1, không tự đổi repo lúc này.

---

## 7. RESUME_CMD (vào lại phiên làm việc PHA 1)

```bash
cd ~/FWI_hiding_system
source .venv/bin/activate
git branch --show-current          # kỳ vọng: exp/v5-sectionV
git log -1 --oneline
# Gate nhanh lại nếu cần:
for t in test_g1 test_g2_hfp test_g3_mcp test_baseline_golden test_calib_gates; do
  python3 tests/$t.py && echo "$t OK"; done
# PHA 1 (CHỈ sau khi control OK + có PROMPT_LAUNCH_SECTIONV.md):
#   đọc PROMPT_LAUNCH_SECTIONV.md → verify coordinator → smoke ô khó nhất → phóng nền.
```

---

**PHA 0 XONG — chờ control.** Chưa phóng 35 cell. Blocker cần control xử: thiếu
`PROMPT_LAUNCH_SECTIONV.md` (mục 6).
