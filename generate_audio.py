# -*- coding: utf-8 -*-
"""
Script tao 30 file audio tieng Trung, doc cham vua phai (hoi nhanh hon slow=True mac dinh).
CHAY TREN MAY BAN HOAC GITHUB ACTIONS (can internet de goi Google TTS, va can ffmpeg cai san).

Cai dat: pip install gTTS
Chay:    python generate_audio.py
"""

from gtts import gTTS
import os
import time
import subprocess

from dialogue_data import SCENES

OUTPUT_DIR = "audio"
SPEED_FACTOR = 1.15  # >1.0 = nhanh hon, <1.0 = cham hon. Chinh so nay de doi toc do.
os.makedirs(OUTPUT_DIR, exist_ok=True)


def speed_up(filepath, factor):
    tmp = filepath + ".tmp.mp3"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", filepath, "-filter:a", f"atempo={factor}", tmp],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        os.replace(tmp, filepath)
    except Exception as e:
        print(f"  Khong chinh duoc toc do (giu nguyen file goc): {e}")


for idx, (num, hanzi, pinyin) in enumerate(SCENES, start=1):
    filepath = os.path.join(OUTPUT_DIR, f"{num}.mp3")
    print(f"[{idx}/30] Dang tao: {filepath}  ->  {hanzi}")
    try:
        tts = gTTS(text=hanzi, lang="zh-CN", slow=True)
        tts.save(filepath)
        speed_up(filepath, SPEED_FACTOR)
    except Exception as e:
        print(f"  Loi tai cau '{hanzi}': {e}")
    time.sleep(0.5)

print("\nHoan tat! 30 file audio nam trong thu muc 'audio/'.")
