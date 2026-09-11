# -*- coding: utf-8 -*-
"""
Ghep nhieu anh (moi anh ~1 canh ngan, vd ~2s) voi audio tuong ung tung canh
(da tao san boi generate_episode_audio.py, dang scene_01.mp3, scene_02.mp3...)
thanh 1 video lien mach, kieu doc thoai khong ngat quang.

Khac voi merge_audio_video.py (ghep audio vao 1 video DA DUNG SAN theo dung
thoi diem cat canh) - script nay TU TAO video moi tu ANH + AUDIO, giong het
quy trinh anh->video ben du an tieng Trung.

Cai dat: pip install moviepy pillow
Chay:    python make_episode_video.py melloday-kids-ep02-script.md
"""

import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

# ---- BAT/TAT PHU DE O DAY - chi can doi True/False roi chay lai ----
SHOW_SUBTITLES = True
# ---------------------------------------------------------------------

IMAGE_DIR = "images"
AUDIO_DIR = "episode_audio"
OUTPUT_FILE = "episode_video.mp4"
TARGET_WIDTH = 720  # anh nho hon se duoc phong to len cho do net


def find_font():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


FONT_PATH = find_font()
if FONT_PATH is None:
    print("CANH BAO: khong tim thay font, phu de se dung font mac dinh cua he thong (co the xau hon).")


def extract_scene_number(filename):
    m = re.search(r"(\d+)", filename)
    return int(m.group(1)) if m else float("inf")


def parse_line_texts(md_path):
    """Doc lai file script, tra ve dict {scene_num: "text hien thi lam phu de"}.
    Gop tat ca cau thoai (khong tinh SFX) trong 1 canh thanh 1 dong phu de."""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    scene_pattern = re.compile(r"^### (\d+)\.\s+(.+?)\s*\([^)]+\)\s*$", re.MULTILINE)
    scenes = list(scene_pattern.finditer(content))
    line_pattern = re.compile(r'\*\*(\w+)\s*(?:\([^)]*\))?:\*\*\s*"([^"]+)"')

    result = {}
    for i, m in enumerate(scenes):
        scene_num = int(m.group(1))
        start = m.end()
        end = scenes[i + 1].start() if i + 1 < len(scenes) else len(content)
        block = content[start:end]
        lines = line_pattern.findall(block)
        text = " ".join(t for _, t in lines)
        result[scene_num] = text
    return result


def upscale_if_needed(img):
    if img.width < TARGET_WIDTH:
        ratio = TARGET_WIDTH / img.width
        img = img.resize((TARGET_WIDTH, round(img.height * ratio)), Image.LANCZOS)
    return img


def draw_rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def add_subtitle(image_path, text, out_path):
    img = Image.open(image_path).convert("RGB")
    img = upscale_if_needed(img)
    if img.width % 2:
        img = img.crop((0, 0, img.width - 1, img.height))
    if img.height % 2:
        img = img.crop((0, 0, img.width, img.height - 1))

    if not text:
        img.save(out_path)
        return

    W, H = img.size
    draw = ImageDraw.Draw(img, "RGBA")

    font_size = max(14, H // 14)
    padding = max(6, H // 40)

    font = ImageFont.truetype(FONT_PATH, font_size) if FONT_PATH else ImageFont.load_default()

    # xuong dong don gian neu cau qua dai so voi be rong anh
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] > W * 0.86 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    lines = lines[:2]  # toi da 2 dong cho gon

    line_heights = []
    max_w = 0
    for l in lines:
        bbox = draw.textbbox((0, 0), l, font=font)
        line_heights.append(bbox[3] - bbox[1])
        max_w = max(max_w, bbox[2] - bbox[0])

    line_gap = max(2, padding // 2)
    block_h = sum(line_heights) + line_gap * (len(lines) - 1)
    box_w = max_w + padding * 4
    box_h = block_h + padding * 2
    box_left = (W - box_w) / 2
    box_top = H - box_h - 14

    draw_rounded_rect(draw, [box_left, box_top, box_left + box_w, box_top + box_h], 14, (0, 0, 0, 150))

    y = box_top + padding
    for l, lh in zip(lines, line_heights):
        draw.text((W / 2, y + lh / 2), l, font=font, fill=(255, 255, 255, 255), anchor="mm")
        y += lh + line_gap

    img.save(out_path)


def main():
    if len(sys.argv) < 2:
        print("Cach dung: python make_episode_video.py duong_dan_script.md")
        sys.exit(1)

    md_path = sys.argv[1]
    subtitles = parse_line_texts(md_path) if SHOW_SUBTITLES else {}

    image_files = sorted(
        [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))],
        key=extract_scene_number,
    )
    if not image_files:
        raise SystemExit(f"Khong tim thay anh nao trong thu muc '{IMAGE_DIR}/'.")

    tmp_dir = "temp_episode_frames"
    os.makedirs(tmp_dir, exist_ok=True)

    clips = []
    for i, img_name in enumerate(image_files, start=1):
        audio_path = os.path.join(AUDIO_DIR, f"scene_{i:02d}.mp3")
        if not os.path.exists(audio_path):
            print(f"[{i:02d}] Khong co audio ({audio_path}), bo qua anh nay.")
            continue

        audio_clip = AudioFileClip(audio_path)
        img_path = os.path.join(IMAGE_DIR, img_name)

        frame_path = os.path.join(tmp_dir, f"{i:02d}.png")
        text = subtitles.get(i, "") if SHOW_SUBTITLES else ""
        add_subtitle(img_path, text, frame_path)

        clip = ImageClip(frame_path).with_duration(audio_clip.duration).with_audio(audio_clip)
        clips.append(clip)
        print(f"[{i:02d}] {img_name} + {os.path.basename(audio_path)} ({audio_clip.duration:.2f}s)")

    if not clips:
        raise SystemExit("Khong ghep duoc canh nao - kiem tra lai thu muc images/ va episode_audio/.")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        OUTPUT_FILE,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    print(f"\nHoan tat! Video: {OUTPUT_FILE} ({final.duration:.1f}s)")
    print(f"Phu de dang: {'BAT' if SHOW_SUBTITLES else 'TAT'} (doi SHOW_SUBTITLES o dau file de bat/tat)")


if __name__ == "__main__":
    main()
