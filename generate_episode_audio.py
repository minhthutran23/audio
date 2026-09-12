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
import hashlib
import os
import random
import re
import sys

import edge_tts
from pydub import AudioSegment
from pydub.generators import Sine


# ---- THU VIEN HIEU UNG AM THANH (SFX) - tu tong hop, khong can file ngoai ----
# Moi dong "SFX: mo ta" trong script se duoc doi thanh 1 doan am thanh tuong ung,
# chen dung vi tri giua cac cau thoai.

def _beep(freq=1000, duration_ms=150, gain_db=-6, fade_out_ms=30):
    return (
        Sine(freq)
        .to_audio_segment(duration=duration_ms)
        .fade_in(8)
        .fade_out(fade_out_ms)
        .apply_gain(gain_db)
    )


def _sfx_alarm():
    beep = _beep(1000, 150, gain_db=-4)
    gap = AudioSegment.silent(duration=90)
    return beep + gap + beep + gap + beep


def _sfx_chime():
    notes = [660, 880, 1320]
    result = AudioSegment.silent(duration=0)
    for f in notes:
        result += _beep(f, 220, gain_db=-8, fade_out_ms=160)
    return result


def _sfx_sparkle():
    notes = [1200, 1600, 2000, 1600]
    result = AudioSegment.silent(duration=0)
    for f in notes:
        result += _beep(f, 80, gain_db=-12, fade_out_ms=40)
    return result


def _sfx_buzz():
    return _beep(220, 300, gain_db=-8, fade_out_ms=60)


def _sfx_pop():
    return _beep(1400, 60, gain_db=-3, fade_out_ms=20)


def _sfx_click():
    return _beep(2000, 40, gain_db=-4, fade_out_ms=10)


def _sfx_thud():
    return _beep(150, 120, gain_db=-6, fade_out_ms=60)


def _sfx_swish():
    notes = [900, 700, 500]
    result = AudioSegment.silent(duration=0)
    for f in notes:
        result += _beep(f, 60, gain_db=-10, fade_out_ms=30)
    return result


def _sfx_zipper():
    notes = [500, 650, 800, 950, 1100, 1250]
    result = AudioSegment.silent(duration=0)
    for f in notes:
        result += _beep(f, 35, gain_db=-10, fade_out_ms=10)
    return result


def _sfx_tada():
    notes = [523, 659, 784, 1046]  # do-mi-son-do, am vang tuoi sang
    result = AudioSegment.silent(duration=0)
    for f in notes:
        result += _beep(f, 140, gain_db=-6, fade_out_ms=100)
    return result


def _sfx_scratch():
    notes = [1000, 700, 400, 200]
    result = AudioSegment.silent(duration=0)
    for f in notes:
        result += _beep(f, 50, gain_db=-6, fade_out_ms=20)
    return result


def _sfx_funny():
    notes = [400, 700, 350]
    result = AudioSegment.silent(duration=0)
    for f in notes:
        result += _beep(f, 90, gain_db=-8, fade_out_ms=40)
    return result


def _sfx_suspense():
    return _beep(180, 500, gain_db=-10, fade_out_ms=250)


def _sfx_sniff():
    return (
        _beep(300, 90, gain_db=-8, fade_out_ms=30)
        + AudioSegment.silent(duration=60)
        + _beep(320, 70, gain_db=-8, fade_out_ms=30)
    )


def _sfx_footsteps():
    thud = _beep(140, 90, gain_db=-8, fade_out_ms=40)
    gap = AudioSegment.silent(duration=120)
    return thud + gap + thud + gap + thud


def _sfx_pause(description):
    """'0.5s pause' -> 0.5s im lang. Neu khong tim thay so giay cu the, mac dinh 0.5s."""
    m = re.search(r"([\d.]+)\s*s", description)
    dur_ms = int(float(m.group(1)) * 1000) if m else 500
    return AudioSegment.silent(duration=dur_ms)


def _sfx_default():
    return _beep(880, 150, gain_db=-8)


SFX_LIBRARY = [
    (r"alarm", _sfx_alarm),
    (r"record scratch|scratch", _sfx_scratch),
    (r"zipper", _sfx_zipper),
    (r"ta-?da", _sfx_tada),
    (r"sparkle|twinkle", _sfx_sparkle),
    (r"chime|bell", _sfx_chime),
    (r"buzz|vibrat", _sfx_buzz),
    (r"sniff", _sfx_sniff),
    (r"footstep|steps", _sfx_footsteps),
    (r"pop|surprise", _sfx_pop),
    (r"click", _sfx_click),
    (r"place|thud|drop", _sfx_thud),
    (r"spread|swish", _sfx_swish),
    (r"funny|comedic|comic", _sfx_funny),
    (r"suspense|dramatic", _sfx_suspense),
]


def synth_sfx(description):
    """Doc mo ta SFX (vd 'alarm clock ringing'), tra ve 1 AudioSegment tuong ung.
    - "pause"/"silence" -> im lang dung so giay ghi trong mo ta (vd "0.5s pause")
    - co chu "music" ma khong khop tu khoa cu the nao khac -> chi de 1 khoang lang
      ngan, vi day la nhac nen that su (can ghep nhac rieng luc dung phim, khong
      the tong hop bang song sin don gian)
    - khong khop gi ca -> dung 1 tieng "ting" ngan mac dinh, khong bao gio loi."""
    text = (description or "").lower()
    if re.search(r"pause|silence", text):
        return _sfx_pause(text)
    for pattern, fn in SFX_LIBRARY:
        if re.search(pattern, text):
            return fn()
    if "music" in text:
        print(f"      (luu y: '{description}' la nhac nen - can ghep nhac that luc dung phim)")
        return AudioSegment.silent(duration=300)
    return _sfx_default()

# ---- CAU HINH GIONG DOC ----
# Cac giong "Multilingual" (Ava, Andrew...) la giong the he moi cua Microsoft,
# nghe tu nhien/bieu cam hon han giong cu (Aria, Guy...).
# Xem danh sach day du bang lenh: edge-tts --list-voices
VOICES = {
    "Narrator": {"voice": "en-US-AndrewMultilingualNeural", "rate": "+15%", "pitch": "+0Hz"},
    "Mel": {"voice": "en-US-AnaNeural", "rate": "+15%", "pitch": "+8Hz"},  # giong be gai, tre + cute
    "Biscuit": {"voice": "en-US-JennyNeural", "rate": "+35%", "pitch": "+60Hz"},  # chi dung de "sua", khong doc thoai that
}
DEFAULT_VOICE = {"voice": "en-US-AndrewMultilingualNeural", "rate": "+15%", "pitch": "+0Hz"}

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


PAUSE_BETWEEN_LINES_MS = 350   # khoang lang giua cac cau thoai trong 1 canh (rut ngan cho nhip nhanh hon)
PAUSE_BETWEEN_SCENES_MS = 900  # khoang lang giua cac canh trong file full_episode

OUTPUT_DIR = "episode_audio"
TEMP_DIR = os.path.join(OUTPUT_DIR, "_tmp_lines")


def parse_script(md_path):
    """Doc file .md, tra ve list[(scene_num, scene_title, items)] trong do items
    la danh sach cac phan tu THEO DUNG THU TU xuat hien trong file, moi phan tu la:
      ("line", speaker, parenthetical, text)   - 1 cau thoai
      ("sfx", description)                     - 1 hieu ung am thanh (dong "SFX: ...")
    """
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    scene_pattern = re.compile(r"^### (\d+)\.\s+(.+?)\s*\([^)]+\)\s*$", re.MULTILINE)
    scenes = list(scene_pattern.finditer(content))
    # Nhom 2: phan trong ngoac don (mo ta cam xuc/hanh dong), co the khong co.
    line_pattern = re.compile(r'\*\*(\w+)\s*(?:\(([^)]*)\))?:\*\*\s*"([^"]+)"')
    sfx_pattern = re.compile(r"^SFX:\s*(.+)$", re.MULTILINE)

    result = []
    for i, m in enumerate(scenes):
        scene_num = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = scenes[i + 1].start() if i + 1 < len(scenes) else len(content)
        block = content[start:end]

        raw_items = []
        for dm in line_pattern.finditer(block):
            raw_items.append((dm.start(), "line", dm.group(1), dm.group(2), dm.group(3)))
        for sm in sfx_pattern.finditer(block):
            raw_items.append((sm.start(), "sfx", sm.group(1).strip()))
        raw_items.sort(key=lambda x: x[0])

        items = [tuple(it[1:]) for it in raw_items]  # bo cot vi tri, chi giu du lieu
        result.append((scene_num, title, items))
    return result


BARK_WORDS = ["Woof", "Ruff", "Arf", "Yip"]


def biscuit_bark_text(original_text):
    """Doi cau thoai cua Biscuit thanh tieng sua "Woof! Woof!" thay vi doc
    nguyen van (nghe khong ra tieng nguoi khi ep giong cho vao cau tieng Anh
    day du). So tieng sua ti le theo do dai cau goc de van giu duoc nhip
    dieu / muc do hao hung cua dong thoai."""
    word_count = len(original_text.split())
    if word_count <= 2:
        n_barks = 1
    elif word_count <= 5:
        n_barks = 2
    else:
        n_barks = 3

    # chon tu "sua" on dinh theo noi dung cau (de cung 1 cau luon ra cung ket qua)
    seed = int(hashlib.md5(original_text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    word = rng.choice(BARK_WORDS)

    punct = "?" if original_text.strip().endswith("?") else "!"
    return " ".join([f"{word}{punct}"] * n_barks)


async def synth_line(text, speaker, parenthetical, out_path):
    cfg = VOICES.get(speaker, DEFAULT_VOICE)
    base_rate = parse_rate_or_pitch(cfg["rate"], "%")
    base_pitch = parse_rate_or_pitch(cfg["pitch"], "Hz")

    rate_off, pitch_off = emotion_offsets(parenthetical)

    # gioi han bien do de khong bi qua da/meo tieng
    final_rate = max(-50, min(80, base_rate + rate_off))
    final_pitch = max(-50, min(80, base_pitch + pitch_off))

    speak_text = biscuit_bark_text(text) if speaker == "Biscuit" else text

    communicate = edge_tts.Communicate(
        speak_text,
        cfg["voice"],
        rate=f"{final_rate:+d}%",
        pitch=f"{final_pitch:+d}Hz",
    )
    await communicate.save(out_path)


# Bat/tat hieu ung am thanh (SFX) tong hop o day - dat False neu nghe khong tu nhien
ENABLE_SFX = False

async def build_episode(scenes):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    full_episode = AudioSegment.silent(duration=0)
    scene_pause = AudioSegment.silent(duration=PAUSE_BETWEEN_SCENES_MS)
    line_pause = AudioSegment.silent(duration=PAUSE_BETWEEN_LINES_MS)

    for scene_num, title, all_items in scenes:
        items = all_items if ENABLE_SFX else [it for it in all_items if it[0] != "sfx"]
        if not items:
            print(f"[Canh {scene_num:02d}] '{title}' - khong co thoai, bo qua.")
            continue

        print(f"[Canh {scene_num:02d}] '{title}' - {len(items)} phan tu")
        scene_audio = AudioSegment.silent(duration=0)
        line_idx = 0

        for idx, item in enumerate(items):
            if item[0] == "line":
                _, speaker, parenthetical, text = item
                tmp_path = os.path.join(TEMP_DIR, f"s{scene_num:02d}_{line_idx:02d}.mp3")
                line_idx += 1
                tag = f" ({parenthetical})" if parenthetical else ""
                print(f"    [{speaker}{tag}] {text}")
                await synth_line(text, speaker, parenthetical, tmp_path)
                clip = AudioSegment.from_file(tmp_path)
                scene_audio += clip
            else:
                _, description = item
                print(f"    [SFX] {description}")
                scene_audio += synth_sfx(description)

            if idx < len(items) - 1:
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
    import argparse

    global PAUSE_BETWEEN_LINES_MS, PAUSE_BETWEEN_SCENES_MS

    parser = argparse.ArgumentParser(description="Tao audio tieng Anh tu file script Melloday Kids.")
    parser.add_argument("md_path", help="Duong dan file script .md")
    parser.add_argument(
        "--line-pause-ms", type=int, default=None,
        help=f"Khoang lang giua cac cau/SFX trong 1 canh (mac dinh {PAUSE_BETWEEN_LINES_MS}ms). "
             f"Dat gan 0 (vd 80) neu muon doc lien tuc kieu doc thoai, khong ngat quang."
    )
    parser.add_argument(
        "--scene-pause-ms", type=int, default=None,
        help=f"Khoang lang giua cac canh trong full_episode.mp3 (mac dinh {PAUSE_BETWEEN_SCENES_MS}ms). "
             f"Dat gan 0 neu muon toan bo episode nghe lien mach, khong ngat quang giua cac canh."
    )
    args = parser.parse_args()

    if args.line_pause_ms is not None:
        PAUSE_BETWEEN_LINES_MS = args.line_pause_ms
    if args.scene_pause_ms is not None:
        PAUSE_BETWEEN_SCENES_MS = args.scene_pause_ms

    scenes = parse_script(args.md_path)
    if not scenes:
        print("Khong tim thay canh nao trong file. Kiem tra lai dinh dang file .md.")
        sys.exit(1)

    asyncio.run(build_episode(scenes))


if __name__ == "__main__":
    main()
