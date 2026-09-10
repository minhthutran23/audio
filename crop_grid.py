# -*- coding: utf-8 -*-
"""
Script cat 1 tam anh gop (dang luoi N hang x M cot) thanh tung anh rieng,
danh so 01.png -> 30.png theo thu tu tu trai sang phai, tren xuong duoi.

Cai dat: pip install pillow
Chay:    python crop_grid.py

Chinh cac bien duoi day cho dung voi anh cua ban:
"""

from PIL import Image
import os

# ---- CAC THAM SO CAN CHINH ----
CANDIDATE_INPUTS = ["combined_sheet.png", "combined_sheet.jpg", "combined_sheet.jpeg"]
OUTPUT_DIR = "images"                # thu muc luu 30 anh rieng
ROWS = 5                             # so hang
COLS = 6                             # so cot
BORDER_TRIM = 2                      # so pixel cat bot vien den giua cac o (tang neu con dinh vien den)
FORCE_ASPECT_169 = True              # True = ep moi anh ve dung ti le 16:9 sau khi cat
# --------------------------------

INPUT_IMAGE = next((f for f in CANDIDATE_INPUTS if os.path.exists(f)), None)
if INPUT_IMAGE is None:
    raise SystemExit(
        "Khong tim thay anh gop. Dat file ten 'combined_sheet.png' (hoac .jpg) "
        "cung thu muc voi script nay."
    )

os.makedirs(OUTPUT_DIR, exist_ok=True)

img = Image.open(INPUT_IMAGE).convert("RGB")
W, H = img.size
cell_w = W / COLS
cell_h = H / ROWS

print(f"Anh goc: {W}x{H}px -> moi o kich thuoc ~{cell_w:.0f}x{cell_h:.0f}px")

count = 0
for row in range(ROWS):
    for col in range(COLS):
        count += 1
        left = round(col * cell_w) + BORDER_TRIM
        top = round(row * cell_h) + BORDER_TRIM
        right = round((col + 1) * cell_w) - BORDER_TRIM
        bottom = round((row + 1) * cell_h) - BORDER_TRIM

        panel = img.crop((left, top, right, bottom))

        if FORCE_ASPECT_169:
            pw, ph = panel.size
            target_ratio = 16 / 9
            current_ratio = pw / ph
            if current_ratio > target_ratio:
                # anh dang qua ngang -> cat bot 2 ben trai/phai
                new_w = round(ph * target_ratio)
                offset = (pw - new_w) // 2
                panel = panel.crop((offset, 0, offset + new_w, ph))
            elif current_ratio < target_ratio:
                # anh dang qua doc -> cat bot tren/duoi
                new_h = round(pw / target_ratio)
                offset = (ph - new_h) // 2
                panel = panel.crop((0, offset, pw, offset + new_h))

        num = f"{count:02d}"
        out_path = os.path.join(OUTPUT_DIR, f"{num}.png")
        panel.save(out_path)
        print(f"[{num}] da luu: {out_path}  ({panel.size[0]}x{panel.size[1]}px)")

print(f"\nHoan tat! Da cat ra {count} anh trong thu muc '{OUTPUT_DIR}/'.")
