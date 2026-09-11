# -*- coding: utf-8 -*-
"""
Script doc file kich ban Melloday Kids (dang .md) va tao audio tieng Anh
voi 3 giong khac nhau: Narrator, Mel (nu), Biscuit (thu cung, giong cao/vui).

Dung edge-tts (giong doc AI mien phi, chat luong cao, khong can API key)
thay vi gTTS vi gTTS chi co 1 giong/ngon ngu, khong the phan biet nhan vat.

MOI: doc luon phan mo ta cam xuc trong ngoac don cua tung cau thoai
(vi du "(groggy)", "(panicked)", "(pleading)"...) de tu dong chinh
toc do + cao do giong theo cam xuc, thay vi doc deu deu tu dau den cuoi.

Cai dat:
    pip install edge-tts pydub
    (can ffmpeg de ghep audio: sudo apt-get install -y ffmpeg, hoac co san tren Mac/Windows neu da cai)

Chay:
    python generate_episode_audio.py duong_dan_file_script.md

Ket qua: thu muc "episode_audio/" gom:
    - scene_00.mp3, scene_01.mp3, ... (audio rieng tung canh, ghep san cac dong thoai)
    - full_episode.mp3 (toan bo episode noi lien nhau, de nghe thu)
"""

import asyncio
import os
import re
import sys

import edge_tts
from pydub import AudioSegment

# ---- CAU HINH GIONG DOC ----
# Cac giong "Multilingual" (Ava, Andrew...) la giong the he moi cua Microsoft,
# nghe tu nhien/bieu cam hon han giong cu (Aria, Guy...).
# Xem danh sach day du bang lenh: edge-tts --list-voices
VOICES = {
    "Narrator": {"voice": "en-US-AndrewMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"},
    "Mel": {"voice": "en-US-AvaMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"},
    "Biscuit": {"voice": "en-US-AnaNeural", "rate": "+8%", "pitch": "+25Hz"},  # giong tre con, cao vui tai
}
DEFAULT_VOICE = {"voice": "en-US-AndrewMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"}

# ---- CAM XUC -> DIEU CHINH TOC DO / CAO DO ----
# (rate_offset_%, pitch_offset_Hz) cong them vao gia tri goc cua giong.
# Sap xep tu cu the den chung chung; dong nao khong khop tu nao thi giu nguyen.
EMOTION_RULES = [
    (r"out of breath|panicked|excited|startled", (20, 20)),
    (r"jolting|surprised|shocked", (15, 25)),
    (r"groggy|sleepy|yawning|soft sigh|tired", (-15, -15)),
    (r"dismayed|sad|worried|nervous", (-10, -10)),
    (r"pleading|apolog", (-8, 8)),
    (r"deadpan|flat", (-8, -10)),
    (r"mock-annoyed|annoyed|arms crossed", (-3, -12)),
    (r"embarrassed|sheepish|scratching", (-5, 5)),
    (r"amused|playful|grinning|laughing|smiling|teasing|proud", (8, 15)),
    (r"warm", (0, 5)),
    (r"thought bubble", (0, 10)),  # Biscuit noi trong dau, hoi tang nhe cho vui tai
]


def parse_rate_or_pitch(value, unit):
    """'+8%' -> 8, '-15Hz' -> -15"""
    m = re.match(r"([+-]?\d+)", value.replace(unit, ""))
    return int(m.group(1)) if m else 0


def emotion_offsets(parenthetical):
    """Doc phan mo ta trong ngoac don, tra ve (rate_offset, pitch_offset) cong don
    tu tat ca cac tu khoa khop duoc (cho phep nhieu cam xuc trong 1 dong, vd
    "smiling, sleepy")."""
    if not parenthetical:
        return 0, 0
    text = parenthetical.lower()
    rate_total, pitch_total = 0, 0
    for pattern, (r_off, p_off) in EMOTION_RULES:
        if re.search(pattern, text):
            rate_total += r_off
            pitch_total += p_off
    return rate_total, pitch_total


PAUSE_BETWEEN_LINES_MS = 450   # khoang lang giua cac cau thoai trong 1 canh
PAUSE_BETWEEN_SCENES_MS = 900  # khoang lang giua cac canh trong file full_episode

OUTPUT_DIR = "episode_audio"
TEMP_DIR = os.path.join(OUTPUT_DIR, "_tmp_lines")


def parse_script(md_path):
    """Doc file .md, tra ve list[(scene_num, scene_title, [(speaker, parenthetical, line), ...])]"""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    scene_pattern = re.compile(r"^### (\d+)\.\s+(.+?)\s*\([^)]+\)\s*$", re.MULTILINE)
    scenes = list(scene_pattern.finditer(content))
    # Nhom 2: phan trong ngoac don (mo ta cam xuc/hanh dong), co the khong co.
    line_pattern = re.compile(r'\*\*(\w+)\s*(?:\(([^)]*)\))?:\*\*\s*"([^"]+)"')

    result = []
    for i, m in enumerate(scenes):
        scene_num = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = scenes[i + 1].start() if i + 1 < len(scenes) else len(content)
        block = content[start:end]
        lines = line_pattern.findall(block)  # [(speaker, parenthetical, text), ...]
        result.append((scene_num, title, lines))
    return result


async def synth_line(text, speaker, parenthetical, out_path):
    cfg = VOICES.get(speaker, DEFAULT_VOICE)
    base_rate = parse_rate_or_pitch(cfg["rate"], "%")
    base_pitch = parse_rate_or_pitch(cfg["pitch"], "Hz")

    rate_off, pitch_off = emotion_offsets(parenthetical)

    # gioi han bien do de khong bi qua da/meo tieng
    final_rate = max(-50, min(50, base_rate + rate_off))
    final_pitch = max(-50, min(50, base_pitch + pitch_off))

    communicate = edge_tts.Communicate(
        text,
        cfg["voice"],
        rate=f"{final_rate:+d}%",
        pitch=f"{final_pitch:+d}Hz",
    )
    await communicate.save(out_path)


async def build_episode(scenes):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    full_episode = AudioSegment.silent(duration=0)
    scene_pause = AudioSegment.silent(duration=PAUSE_BETWEEN_SCENES_MS)
    line_pause = AudioSegment.silent(duration=PAUSE_BETWEEN_LINES_MS)

    for scene_num, title, lines in scenes:
        if not lines:
            print(f"[Canh {scene_num:02d}] '{title}' - khong co thoai, bo qua.")
            continue

        print(f"[Canh {scene_num:02d}] '{title}' - {len(lines)} dong thoai")
        scene_audio = AudioSegment.silent(duration=0)

        for idx, (speaker, parenthetical, text) in enumerate(lines):
            tmp_path = os.path.join(TEMP_DIR, f"s{scene_num:02d}_{idx:02d}.mp3")
            tag = f" ({parenthetical})" if parenthetical else ""
            print(f"    [{speaker}{tag}] {text}")
            await synth_line(text, speaker, parenthetical, tmp_path)
            clip = AudioSegment.from_file(tmp_path)
            scene_audio += clip
            if idx < len(lines) - 1:
                scene_audio += line_pause

        scene_out = os.path.join(OUTPUT_DIR, f"scene_{scene_num:02d}.mp3")
        scene_audio.export(scene_out, format="mp3")
        print(f"    -> luu: {scene_out} ({len(scene_audio)/1000:.1f}s)\n")

        if len(full_episode) > 0:
            full_episode += scene_pause
        full_episode += scene_audio

    full_out = os.path.join(OUTPUT_DIR, "full_episode.mp3")
    full_episode.export(full_out, format="mp3")
    print(f"Hoan tat! Toan bo episode: {full_out} ({len(full_episode)/1000:.1f}s)")


def main():
    if len(sys.argv) < 2:
        print("Cach dung: python generate_episode_audio.py duong_dan_script.md")
        sys.exit(1)

    md_path = sys.argv[1]
    scenes = parse_script(md_path)
    if not scenes:
        print("Khong tim thay canh nao trong file. Kiem tra lai dinh dang file .md.")
        sys.exit(1)

    asyncio.run(build_episode(scenes))


if __name__ == "__main__":
    main()
