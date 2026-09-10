# -*- coding: utf-8 -*-
"""
Script cat 1 tam anh gop (dang luoi N hang x M cot, cac o co the KHONG deu nhau)
thanh tung anh rieng, danh so 01.png -> 30.png theo thu tu tu trai sang phai,
tren xuong duoi.

Thay vi chia deu theo toa do (de bi lech neu AI ve o to o nho khac nhau),
script nay TU DO duong vien den that trong anh (dua vao mat do pixel den)
de tim dung ranh gioi giua cac o.

Cai dat: pip install pillow numpy
Chay:    python crop_grid.py
"""

from PIL import Image
import numpy as np
import os

# ---- CAC THAM SO CAN CHINH ----
CANDIDATE_INPUTS = ["combined_sheet.png", "combined_sheet.jpg", "combined_sheet.jpeg"]
OUTPUT_DIR = "images"                # thu muc luu 30 anh rieng
ROWS = 5                             # so hang
COLS = 6                             # so cot
INSET = 3                            # so pixel cat bot vien den quanh moi o
FORCE_ASPECT_169 = True              # True = ep moi anh ve dung ti le 16:9 sau khi cat
BLACK_THRESH = 100                   # gia tri xam duoi muc nay coi la "den" (0-255)
LINE_FRAC_THRESH = 0.9               # 1 dong/cot duoc coi la duong vien neu >90% pixel la den
SEARCH_WINDOW_FRAC = 0.22            # tim duong vien that trong pham vi +-22% kich thuoc 1 o quanh vi tri chia deu
# --------------------------------

INPUT_IMAGE = next((f for f in CANDIDATE_INPUTS if os.path.exists(f)), None)
if INPUT_IMAGE is None:
    raise SystemExit(
        "Khong tim thay anh gop. Dat file ten 'combined_sheet.png' (hoac .jpg) "
        "cung thu muc voi script nay."
    )

os.makedirs(OUTPUT_DIR, exist_ok=True)


def refine_lines(frac, n, total_len, thresh):
    """Bat dau tu vi tri chia deu (0, 1/n, 2/n, ... total_len), voi moi vi tri
    tim duong vien den THAT gan nhat trong 1 cua so nho quanh do. Neu khong
    thay duong vien ro rang, giu nguyen vi tri chia deu (an toan)."""
    even = [round(i * total_len / n) for i in range(n + 1)]
    window = int((total_len / n) * SEARCH_WINDOW_FRAC)
    result = [0]
    for i in range(1, n):
        guess = even[i]
        lo = max(0, guess - window)
        hi = min(total_len, guess + window)
        local = frac[lo:hi]
        if len(local) == 0 or local.max() < thresh:
            result.append(guess)
            continue
        best = lo + int(np.argmax(local))
        result.append(best)
    result.append(total_len)
    return result


def find_grid_lines(img):
    arr = np.array(img.convert("L"))
    H, W = arr.shape
    black = arr < BLACK_THRESH

    row_frac = black.mean(axis=1)
    row_lines = refine_lines(row_frac, ROWS, H, LINE_FRAC_THRESH)

    col_lines_per_row = []
    for r in range(ROWS):
        y0 = row_lines[r] + 8
        y1 = row_lines[r + 1] - 8
        if y1 <= y0:
            y0, y1 = row_lines[r], row_lines[r + 1]
        band = black[y0:y1, :]
        col_frac = band.mean(axis=0)
        col_lines = refine_lines(col_frac, COLS, W, LINE_FRAC_THRESH)
        col_lines_per_row.append(col_lines)

    return row_lines, col_lines_per_row


def force_aspect_169(panel):
    pw, ph = panel.size
    target_ratio = 16 / 9
    cur_ratio = pw / ph if ph else 1
    if cur_ratio > target_ratio:
        new_w = round(ph * target_ratio)
        offset = (pw - new_w) // 2
        panel = panel.crop((offset, 0, offset + new_w, ph))
    elif cur_ratio < target_ratio:
        new_h = round(pw / target_ratio)
        offset = (ph - new_h) // 2
        panel = panel.crop((0, offset, pw, offset + new_h))
    return panel


img = Image.open(INPUT_IMAGE).convert("RGB")
row_lines, col_lines_per_row = find_grid_lines(img)
print(f"Anh goc: {img.width}x{img.height}px")
print(f"Duong vien hang: {row_lines}")

count = 0
for row in range(ROWS):
    for col in range(COLS):
        count += 1
        top = row_lines[row] + INSET
        bottom = row_lines[row + 1] - INSET
        left = col_lines_per_row[row][col] + INSET
        right = col_lines_per_row[row][col + 1] - INSET

        panel = img.crop((left, top, right, bottom))

        if FORCE_ASPECT_169:
            panel = force_aspect_169(panel)

        num = f"{count:02d}"
        out_path = os.path.join(OUTPUT_DIR, f"{num}.png")
        panel.save(out_path)
        print(f"[{num}] da luu: {out_path}  ({panel.size[0]}x{panel.size[1]}px)")

print(f"\nHoan tat! Da cat ra {count} anh trong thu muc '{OUTPUT_DIR}/'.")
