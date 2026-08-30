# PLAYBOOK THỰC NGHIỆM — SETUP + CHẠY LẠI (chi tiết, cho project sửa bài)

> File tham chiếu chi tiết cho phần C của INSTRUCTION_PROJECT.md. Lôi ra khi CẦN chạy lại thực
> nghiệm. Chắt từ dự án đã hoàn thành (resubmit bài reject). Thay `<...>` bằng giá trị cụ thể.
> Nguyên tắc xuyên suốt: DEFENSIBLE (đo được, giải thích được, chạy thật) + CHỊU RỚT MẠNG.

---

## 0. TRIẾT LÝ (đọc trước — vì sao làm vậy)

- Bài reject thường vì **thực nghiệm không defensible**: đo runtime trên máy bất ổn, baseline bị
  xử ép, số không truy được. Playbook này loại các lỗ hổng đó.
- **Chạy thật > suy luận.** Tốn thời gian nhưng loại rủi ро + hay lộ điều bất ngờ (baseline đổi
  theo tham số). ĐỪNG "ghi-theo-verify".
- **Chịu rớt SSH** là yêu cầu thực tế (mạng di động không ổn). Coordinator phải sống độc lập session.

---

## 1. TẠO & CẤU HÌNH MÁY GCP

### 1.1 Tạo VM
```bash
# on-demand (KHÔNG preemptible), cấu hình cố định, zone cố định
gcloud compute instances create <vm-name> \
  --zone=<zone> \
  --machine-type=c2-standard-16 \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB
```
- **c2-standard-16** (16 vCPU/32GB): đủ mạnh, RT ổn định. Tăng nếu dataset rất lớn.
- **KHÔNG preemptible/spot** — bị ngắt giữa chừng hỏng RT + baseline dài.
- Ghi lại cấu hình để viết vào bài (mục Experimental Setup).

### 1.2 SSH + môi trường
```bash
gcloud compute instances ssh <vm-name> --zone=<zone>

# Trên VM:
sudo apt update && sudo apt install -y python3-venv tmux git
cd ~ && git clone https://github.com/<user>/<repo>.git && cd <repo>
python3 -m venv .venv && source .venv/bin/activate
pip install numpy pandas openpyxl psutil matplotlib   # + gói riêng của bài
```

### 1.3 Git credential (để coordinator tự push không cần gõ mật khẩu)
```bash
git config --global credential.helper store
# Tạo PAT (Personal Access Token) trên GitHub: Settings > Developer settings > 
#   Fine-grained/classic token, scope repo. KHÔNG dùng mật khẩu tài khoản.
# Push tay MỘT lần, nhập username + PAT (làm password) → lưu vào ~/.git-credentials
git push   # nhập PAT lần này; sau đó coordinator tự push
```

### 1.4 Stop khi xong (ngừng tính tiền)
```bash
gcloud compute instances stop <vm-name> --zone=<zone>    # disk giữ nguyên
gcloud compute instances start <vm-name> --zone=<zone>   # bật lại khi cần
# Chỉ stop SAU KHI git ahead 0 (mọi thứ đã push).
```

---

## 2. COORDINATOR (bộ điều phối) — thiết kế bắt buộc

Coordinator là script điều phối chạy các "ô" thực nghiệm (cell = một tổ hợp dataset×tham số×method).

### 2.1 Nguyên tắc thiết kế
- **Chạy các ô TUẦN TỰ.** Song song chỉ TRONG một ô (nhiều worker xử lý phần việc của ô đó). Lý do:
  RT mỗi ô không bị tranh CPU/RAM với ô khác → **RT defensible, so sánh được.**
- **Checkpoint mỗi ô:** ghi kết quả ra file JSON/CSV NGAY sau khi xong ô + `git commit` + `git push`.
  Mất máy/rớt mạng không mất tiến độ.
- **Resume tự SKIP:** đầu mỗi ô, kiểm file kết quả đã tồn tại chưa; có rồi thì bỏ qua. Chạy lại an
  toàn (idempotent).
- **Lưới ô cố định (CELLS):** định nghĩa rõ danh sách ô, không quét động (tránh bắt nhầm file cũ).
- **Ghi ĐỦ cột cần** (mọi metric + cột phụ như counter escalation). KIỂM trước khi phóng.
- **Một git writer duy nhất** (coordinator). KHÔNG script khác push cùng lúc.

### 2.2 Cảnh báo code
- Nếu file thực nghiệm KHÔNG có `if __name__=="__main__":` guard → chạy trần `python file.py` sẽ
  thực thi ngay lúc import. **Luôn chạy QUA coordinator**, không chạy trần.
- Deadline/van (nếu có, vd giới hạn 2h/ô cho baseline) áp ĐÚNG pha cần đo, KHÔNG áp nhầm pha khác
  (vd van chỉ áp pha "ẩn/xử lý", không áp pha đánh giá lại).

### 2.3 Log & tiến độ
- Coordinator ghi `PROGRESS_<phase>.md` (ô nào xong, kết quả tóm tắt) + log file + `RESUME_CMD.txt`.
- `PROGRESS` là nguồn đếm ĐÁNG TIN nhất (đừng đếm file thô — dễ bắt dư file cũ/ngoài phạm vi).

---

## 3. CHẠY NỀN SỐNG SÓT RỚT SSH (quan trọng)

### 3.1 Launch coordinator detach
```bash
cd ~/<repo> && source .venv/bin/activate
setsid nohup python3 tools/<coordinator>.py > tools/<coordinator>.log 2>&1 < /dev/null &
disown
sleep 5
# XÁC MINH độc lập session (bắt buộc):
pgrep -af <coordinator>
ps -o ppid= -p $(pgrep -f <coordinator> | head -1)   # phải in "1" (PPID=1)
```
→ Chỉ yên tâm khi thấy process + **PPID=1**. PPID=1 = độc lập session SSH → rớt SSH không giết.

### 3.2 tmux cho phiên tương tác (watch, gõ lệnh, agent)
```bash
tmux new -s work            # tạo phiên
#   Ctrl+b  c   = cửa sổ mới
#   Ctrl+b  %   = chia dọc | Ctrl+b " = chia ngang
#   Ctrl+b  d   = thoát (phiên vẫn chạy trên VM)
tmux attach -t work         # gắn lại sau khi rớt SSH
tmux ls                     # liệt kê phiên
```
→ Hai lớp: coordinator (nohup, PPID=1) sống độc lập cả tmux; tmux giữ cửa sổ tương tác của bạn.

---

## 4. THEO DÕI TIẾN ĐỘ

### 4.1 Nguyên tắc: `pgrep` là SỰ THẬT
- Job dài (vd baseline 2h) chạy IM LẶNG → log mtime KHÔNG đổi. **Log cũ ≠ chết.** Chỉ `pgrep`
  trống mới là chết thật.

### 4.2 Lệnh kiểm một lần
```bash
cd ~/<repo> && \
(pgrep -f <coordinator> >/dev/null && echo "DANG CHAY PID $(pgrep -f <coordinator>|tr '\n' ' ')" || echo "KHONG CHAY") && \
echo "Tien do:" && tail -4 PROGRESS_<phase>.md 2>/dev/null && \
git status -sb | head -1 && tail -3 tools/<coordinator>.log
```

### 4.3 Watch định kỳ (300s)
```bash
watch -n 300 'cd ~/<repo> && echo "=== $(date +%H:%M:%S) ===" && \
(pgrep -f <coordinator> >/dev/null && echo "DANG CHAY" || echo ">>> KHONG CHAY <<<") && \
(tail -4 PROGRESS_<phase>.md 2>/dev/null || echo "chua co progress") && \
git status -sb | head -1'
```
→ `watch` chết theo SSH; coordinator không. Rớt SSH → kết nối lại, gõ lại watch (hoặc chạy trong tmux).

### 4.4 Nếu "KHONG CHAY" + chưa đủ ô → resume
```bash
cat ~/<repo>/RESUME_CMD.txt    # chạy lệnh trong đó; coordinator skip ô đã xong, chạy tiếp ô dở
```

---

## 5. QUY TRÌNH 3 BƯỚC (KHÔNG phóng mù)

Trước mẻ lớn (nhiều giờ/ngày), chia 3 bước — giao cho agent (Claude Code) từng bước, duyệt rồi tiếp:

**BƯỚC 1 — CHUẨN BỊ (chưa chạy ô nào):**
- Viết/kiểm coordinator. Verify lưới ô đúng spec (đếm đúng số ô). Verify LOGGING đủ mọi cột cần
  (vd counter phụ). `ast.parse` + import module-level để kiểm, KHÔNG gọi main. Báo cáo ra file.

**BƯỚC 2 — SMOKE TEST (1-2 ô):**
- Chạy ô **KHÓ NHẤT** (tham số cực đoan) → verify: đủ metric + cột phụ (không NaN/lỗi) + push OK.
  Ô khó nhất test luôn edge case + hé lộ tín hiệu khoa học sớm. Báo cáo ra file. CHƯA phóng.

**BƯỚC 3 — PHÓNG (sau khi smoke đạt):**
- Launch toàn bộ (nền, detach mục 3.1). Xác minh PPID=1. Thứ tự ô: nhẹ→nặng; trong ô: phần nhanh
  trước. Baseline dài chạy thật (KHÔNG verify-theo-suy-luận).

→ Lý do: phóng 48h rồi mới phát hiện thiếu cột logging = công cốc. Smoke bắt lỗi sớm.

---

## 6. PROMPT CHO AGENT THỰC THI (Claude Code) — khuôn mẫu

Agent mất lịch sử khi mở cửa sổ mới → prompt phải TỰ ĐỦ + dựa file.
```
[KHÔI PHỤC CONTEXT nếu cửa sổ mới]
Đọc PLAN_<...>.md, PROGRESS_<phase>.md, RESUME_CMD.txt, các báo cáo BUOC*.md để nắm trạng thái. 
Đừng làm gì, tóm tắt: đang ở đâu, coordinator còn chạy không (pgrep), còn bao nhiêu ô.

[GIAO VIỆC — rõ + cụ thể]
NHIỆM VỤ: <mô tả>. Phạm vi: <giới hạn>. 
- Output ghi ra file <tên>.md, in 1 dòng xác nhận "<X> DONE" rồi DỪNG.
- KHÔNG đụng: <danh sách file/logic không được sửa>.
- <Các bước cụ thể đánh số>.
```
Nguyên tắc: chia việc, không dồn; mỗi bước in xác nhận rồi dừng; ranh giới "KHÔNG đụng" rõ ràng.

---

## 7. GIT — AN TOÀN + ĐÓNG GÓI

### 7.1 Trong lúc chạy
- Experiment trên **branch riêng** (`exp/<...>`). KHÔNG rebase/force/amend trên branch đang chạy.
- Coordinator tự commit+push mỗi ô. `.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `*.log`.

### 7.2 Đóng gói lên main (khi xong)
```bash
# main == origin/main trước đã (không tự diverge). exp là feature branch bình thường.
git checkout main && git pull origin main
git merge --squash exp/<branch>            # main sạch 1 commit; exp giữ lịch sử chi tiết
# Conflict (thường .gitignore + vài file kết quả): lấy bản exp nếu là superset/số fresh:
git checkout exp/<branch> -- <file-conflict> && git add <file-conflict>
git commit -m "Add complete experiment: <mô tả GD/EXP>"
git push origin main                        # push thường, KHÔNG force
```

### 7.3 VERIFY sau merge (bắt buộc)
```bash
git ls-tree -r --name-only main | grep -E "<file mới cần có>"   # main CÓ đủ file mới
git ls-tree -r --name-only main | grep -E "<file cũ>"          # main VẪN GIỮ file cũ (squash THÊM, không xóa)
git log origin/main --oneline -2
```
→ Ghi VERIFY_MERGE.md. Chỉ stop VM sau khi verify + `git status -sb` = ahead 0 (cả branch lẫn main).

---

## 8. CHECKLIST TRƯỚC KHI STOP VM
- [ ] Smoke đã đạt trước khi phóng (đủ metric + cột phụ, không NaN).
- [ ] Toàn bộ ô xong (theo PROGRESS, không phải đếm file thô).
- [ ] Coordinator dừng sạch; git ahead 0 trên branch.
- [ ] Đã đóng gói main (nếu cần) + VERIFY (đủ mới, giữ cũ).
- [ ] Đã chắt kết quả + kết luận vào master plan (cho phần viết).
- [ ] CHỈ stop VM sau khi các mục trên xong: `gcloud compute instances stop <vm> --zone=<zone>`

---

## 9. NHỮNG BÀI HỌC ĐẮT (đừng lặp lại)
- **Không đo RT trên hạ tầng bất ổn** (VM tự recycle) → RT vô nghĩa, reviewer đâm.
- **Không trộn RT 2 môi trường** → chạy lại hết một nguồn.
- **Không ghi-theo-verify baseline** → baseline có thể đổi theo tham số (fail chỗ này, ổn chỗ kia).
- **Không dựa log mtime để kết luận sống/chết** → dùng pgrep.
- **Không launch quên detach** → rớt SSH giết job; luôn setsid+nohup+disown, verify PPID=1.
- **Không phóng mù** → 3 bước: chuẩn bị → smoke (ô khó nhất) → phóng.
- **Không quên kiểm đủ số cột metric** → từng sót metric trong bảng.
- **Không stop VM trước khi push xong** → mất thay đổi chưa push.
- **Để bằng chứng quyết định đóng góp** → reframe trung thực nếu thực nghiệm bác claim ban đầu.
