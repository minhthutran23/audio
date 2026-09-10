# -*- coding: utf-8 -*-
"""
Script tao 30 file audio tieng Trung, doc CHAM de luyen phat am.
CHAY TREN MAY BAN HOAC GITHUB ACTIONS (can internet de goi Google TTS).

Cai dat: pip install gTTS
Chay:    python generate_audio.py

Ket qua: thu muc "audio/" chua 30 file 01.mp3 -> 30.mp3
"""

from gtts import gTTS
import os
import time

from dialogue_data import SCENES

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for idx, (num, hanzi, pinyin) in enumerate(SCENES, start=1):
    filepath = os.path.join(OUTPUT_DIR, f"{num}.mp3")
    print(f"[{idx}/30] Dang tao: {filepath}  ->  {hanzi}")
    try:
        # slow=True: doc cham hon, phu hop de luyen phat am
        tts = gTTS(text=hanzi, lang="zh-CN", slow=True)
        tts.save(filepath)
    except Exception as e:
        print(f"  Loi tai cau '{hanzi}': {e}")
    time.sleep(0.5)  # tranh goi API qua nhanh bi chan

print("\nHoan tat! 30 file audio nam trong thu muc 'audio/'.")
