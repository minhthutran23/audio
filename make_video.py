# -*- coding: utf-8 -*-
"""
Script ghep 30 anh + 30 audio thanh 1 video cau chuyen hoan chinh,
co PHU DE (chu Han + pinyin) de tren moi anh, va co the them NHAC NEN.

CHAY TREN GITHUB ACTIONS HOAC MAY BAN, sau khi da co:
  - Thu muc "images/" chua 30 anh (ten file bat dau bang 01_, 02_... da dung thu tu)
  - Thu muc "audio/"  chua 30 audio: 01.mp3, 02.mp3, ..., 30.mp3
  - (Tuy chon) file "background_music.mp3" o thu muc goc de them nhac nen

Cai dat: pip install moviepy pillow
         (can font chu Han: sudo apt-get install -y fonts-noto-cjk)
Chay:    python make_video.py
"""

import os
import re
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
    CompositeAudioClip,
)

from dialogue_data import SCENES

# ---- AI super-resolution (Real-ESRGAN), neu khong cai duoc thi tu dong dung
# cach cu (phong to LANCZOS + lam net) khong lam hong ca video ----
AI_UPSAMPLER = None
try:
    import numpy as np
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet

    MODEL_PATH = "weights/RealESRGAN_x4plus_anime_6B.pth"
    if os.path.exists(MODEL_PATH):
        _model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                          num_block=6, num_grow_ch=32, scale=4)
        AI_UPSAMPLER = RealESRGANer(
            scale=4, model_path=MODEL_PATH, model=_model,
            tile=0, tile_pad=10, pre_pad=0, half=False
        )
        print("Da bat AI upscaler (Real-ESRGAN).")
    else:
        print(f"Khong thay model tai {MODEL_PATH}, dung cach phong to thuong.")
except Exception as e:
    print(f"Khong dung duoc Real-ESRGAN ({e}), dung cach phong to thuong.")

IMAGE_DIR = "images"
AUDIO_DIR = "audio"
OUTPUT_FILE = "story_video.mp4"

# ---- CAC THAM SO BAN CO THE CHINH ----
PAUSE_BETWEEN_SCENES = 1.0     # giay nghi giua cac canh (tang/giam so nay tuy y)
TARGET_WIDTH = 720             # anh nho hon se duoc phong to len do net hon; anh to hon giu nguyen
BG_MUSIC_FILE = "background_music.mp3"  # dat file nhac nen (mp3) o thu muc goc, khong co thi tu bo qua
BG_MUSIC_VOLUME = 0.15         # am luong nhac nen (0.0 - 1.0), de nho hon loi thoai
# ----------------------------------------

TEMP_DIR = "temp_subtitled"
os.makedirs(TEMP_DIR, exist_ok=True)


def find_cjk_font():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    try:
        out = subprocess.check_output(
            ["fc-match", "-f", "%{file}", "Noto Sans CJK SC"]
        ).decode().strip()
        if out and os.path.exists(out):
            return out
    except Exception:
        pass
    return None


FONT_PATH = find_cjk_font()
if FONT_PATH is None:
    print("CANH BAO: Khong tim thay font CJK, chu Han co the hien loi (o vuong).")
    print("  Them buoc 'sudo apt-get install -y fonts-noto-cjk' vao workflow.")


def upscale_image(img):
    """Phong to anh len TARGET_WIDTH. Dung AI (Real-ESRGAN) neu co,
    khong thi dung LANCZOS + lam net (unsharp mask) nhu cu."""
    if img.width >= TARGET_WIDTH:
        return img

    if AI_UPSAMPLER is not None:
        try:
            img_np = np.array(img)          # RGB
            img_bgr = img_np[:, :, ::-1]     # Real-ESRGAN can BGR (kieu cv2)
            output, _ = AI_UPSAMPLER.enhance(img_bgr, outscale=4)
            img = Image.fromarray(output[:, :, ::-1])
            if img.width != TARGET_WIDTH:
                ratio = TARGET_WIDTH / img.width
                img = img.resize((TARGET_WIDTH, round(img.height * ratio)), Image.LANCZOS)
            return img
        except Exception as e:
            print(f"  AI upscale loi ({e}), chuyen sang cach thuong cho anh nay.")

    ratio = TARGET_WIDTH / img.width
    img = img.resize((TARGET_WIDTH, round(img.height * ratio)), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    return img


def add_subtitle(image_path, hanzi, pinyin, out_path):
    img = Image.open(image_path).convert("RGB")
    img = upscale_image(img)

    W, H = img.size
    draw = ImageDraw.Draw(img, "RGBA")

    # Cong thuc theo chieu cao anh (H): khung nen om sat chu, chiem ~1/4 anh
    hanzi_size = max(9, H // 13)
    pinyin_size = max(6, H // 20)
    padding = max(3, H // 25)

    if FONT_PATH:
        font_hanzi = ImageFont.truetype(FONT_PATH, hanzi_size)
        font_pinyin = ImageFont.truetype(FONT_PATH, pinyin_size)
    else:
        font_hanzi = ImageFont.load_default()
        font_pinyin = ImageFont.load_default()

    def text_size(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    hw, hh = text_size(hanzi, font_hanzi)
    pw, ph = text_size(pinyin, font_pinyin)

    line_gap = max(2, padding // 2)
    box_w = max(hw, pw) + padding * 4
    box_h = hh + ph + line_gap + padding * 2
    box_left = (W - box_w) / 2
    box_top = H - box_h - 14

    radius = 16
    draw.rounded_rectangle(
        [box_left, box_top, box_left + box_w, box_top + box_h],
        radius=radius, fill=(0, 0, 0, 150)
    )

    block_h = hh + line_gap + ph
    start_y = box_top + (box_h - block_h) / 2
    draw.text((W / 2, start_y + hh / 2), hanzi, font=font_hanzi, fill=(255, 255, 255, 255), anchor="mm")
    draw.text((W / 2, start_y + hh + line_gap + ph / 2), pinyin, font=font_pinyin, fill=(255, 221, 130, 255), anchor="mm")

    # libx264 bat buoc chieu rong/cao phai la SO CHAN, cat bot 1px neu le
    if img.width % 2 != 0 or img.height % 2 != 0:
        img = img.crop((0, 0, img.width - (img.width % 2), img.height - (img.height % 2)))

    img.save(out_path)


def get_looped_audio(path, duration):
    clip = AudioFileClip(path)
    if clip.duration >= duration:
        return clip.subclipped(0, duration)
    loops = int(duration // clip.duration) + 1
    looped = concatenate_audioclips([clip] * loops)
    return looped.subclipped(0, duration)


def extract_scene_number(filename):
    """Lay so dau tien trong ten file de sap xep dung thu tu canh
    (vd: image_2_2_xxx.jpeg -> 2), thay vi sap theo chu cai
    (se bi lech: 1, 10, 11 ... 19, 2, 20 ...)."""
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else float("inf")


image_files = sorted(
    [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))],
    key=extract_scene_number,
)

clips = []

for i, img_name in enumerate(image_files, start=1):
    num = f"{i:02d}"
    img_path = os.path.join(IMAGE_DIR, img_name)
    audio_path = os.path.join(AUDIO_DIR, f"{num}.mp3")

    if not os.path.exists(audio_path):
        print(f"Khong tim thay audio: {audio_path} - bo qua canh {num} ({img_name})")
        continue

    scene = next((s for s in SCENES if s[0] == num), None)
    hanzi, pinyin = (scene[1], scene[2]) if scene else ("", "")

    subtitled_path = os.path.join(TEMP_DIR, f"{num}.png")
    add_subtitle(img_path, hanzi, pinyin, subtitled_path)

    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration + PAUSE_BETWEEN_SCENES

    img_clip = ImageClip(subtitled_path).with_duration(duration)
    img_clip = img_clip.with_audio(audio_clip.with_start(0))

    clips.append(img_clip)
    print(f"[{num}] {duration:.1f}s  {hanzi}")

if not clips:
    print("Khong co canh nao de ghep. Kiem tra lai thu muc images/ va audio/.")
else:
    final = concatenate_videoclips(clips, method="compose")

    if os.path.exists(BG_MUSIC_FILE):
        print(f"Dang them nhac nen: {BG_MUSIC_FILE}")
        bg_audio = get_looped_audio(BG_MUSIC_FILE, final.duration).with_volume_scaled(BG_MUSIC_VOLUME)
        mixed_audio = CompositeAudioClip([bg_audio, final.audio])
        final = final.with_audio(mixed_audio)
    else:
        print("Khong co file nhac nen (background_music.mp3) - bo qua, chi dung loi thoai.")

    final.write_videofile(
        OUTPUT_FILE,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    print(f"\nHoan tat! Video da luu tai: {OUTPUT_FILE}")

    shutil.rmtree(TEMP_DIR, ignore_errors=True)
