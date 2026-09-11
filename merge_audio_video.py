# -*- coding: utf-8 -*-
"""
Ghep audio tung canh + phu de (tuy chon) vao dung vi tri thoi gian tren
video da dung san - dung CHUNG cho moi tap phim, khong can sua code moi
lan doi tap.

Thoi luong tung canh duoc doc TRUC TIEP tu tieu de trong file script .md
(vi du "### 2. Waking Up (0:06-0:16)"), khong con phai go tay
SCENE_DURATIONS nhu truoc - chi can ghi dung thoi gian that vao file .md
la moi lan doi tap deu chay dung.

Quy uoc ten file CO DINH (khong doi ten moi tap):
  - story_final.mp4     : video da dung san
  - melloday_script.md  : script cua tap dang lam (de vao dung ten nay
                           moi lan doi tap, khong doi ten file)
  - episode_audio/scene_NN.mp3 : audio tung canh (da tao boi
                           generate_episode_audio.py melloday_script.md)

Cai dat: pip install moviepy pillow
Chay:    python merge_audio_video.py
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip,
    CompositeAudioClip, CompositeVideoClip,
)

VIDEO_FILE = "story_final.mp4"
SCRIPT_FILE = "melloday_script.md"
AUDIO_DIR = "episode_audio"
OUTPUT_FILE = "melloday_final.mp4"

# Bat/tat phu de o day - chi can doi True/False roi chay lai, khong can sua gi khac
SHOW_SUBTITLES = True


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


def parse_timecode(tc):
    """'0:06' -> 6.0, '1:03.9' -> 63.9"""
    tc = tc.strip()
    m = re.match(r"(\d+):(\d+(?:\.\d+)?)", tc)
    if not m:
        raise ValueError(f"Khong doc duoc timecode: {tc!r}")
    minutes = int(m.group(1))
    seconds = float(m.group(2))
    return minutes * 60 + seconds


def parse_scenes(md_path):
    """Doc file script, tra ve list[(scene_num, start_sec, end_sec, subtitle_text)],
    sap xep theo scene_num. subtitle_text la tat ca cau thoai (khong tinh SFX) noi lai."""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    scene_pattern = re.compile(
        r"^### (\d+)\.\s+(.+?)\s*\(([^)]+)\)\s*$", re.MULTILINE
    )
    scenes = list(scene_pattern.finditer(content))
    line_pattern = re.compile(r'\*\*(\w+)\s*(?:\([^)]*\))?:\*\*\s*"([^"]+)"')

    result = []
    for i, m in enumerate(scenes):
        scene_num = int(m.group(1))
        timing = m.group(3)
        start_str, end_str = re.split(r"[-–]", timing, maxsplit=1)
        start_sec = parse_timecode(start_str)
        end_sec = parse_timecode(end_str)

        block_start = m.end()
        block_end = scenes[i + 1].start() if i + 1 < len(scenes) else len(content)
        block = content[block_start:block_end]
        lines = line_pattern.findall(block)
        subtitle_text = " ".join(t for _, t in lines)

        result.append((scene_num, start_sec, end_sec, subtitle_text))

    result.sort(key=lambda x: x[0])
    return result


def make_subtitle_overlay(text, video_size):
    """Tao 1 anh PNG trong suot (RGBA), chi ve khung phu de + chu, dung kich
    thuoc voi video, de chong (composite) len tren video goc."""
    W, H = video_size
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = max(14, H // 16)
    padding = max(6, H // 45)
    font = ImageFont.truetype(FONT_PATH, font_size) if FONT_PATH else ImageFont.load_default()

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
    lines = lines[:2]

    line_heights, max_w = [], 0
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

    draw.rounded_rectangle(
        [box_left, box_top, box_left + box_w, box_top + box_h],
        radius=14, fill=(0, 0, 0, 150)
    )

    y = box_top + padding
    for l, lh in zip(lines, line_heights):
        draw.text((W / 2, y + lh / 2), l, font=font, fill=(255, 255, 255, 255), anchor="mm")
        y += lh + line_gap

    return img


def main():
    if not os.path.exists(VIDEO_FILE):
        raise SystemExit(f"Khong tim thay {VIDEO_FILE}.")
    if not os.path.exists(SCRIPT_FILE):
        raise SystemExit(f"Khong tim thay {SCRIPT_FILE}.")

    video = VideoFileClip(VIDEO_FILE)
    print(f"Video: {VIDEO_FILE} - {video.duration:.1f}s, kich thuoc {video.w}x{video.h}")

    scenes = parse_scenes(SCRIPT_FILE)
    total_expected = scenes[-1][2] if scenes else 0
    if abs(total_expected - video.duration) > 1.5:
        print(
            f"CANH BAO: tong thoi luong theo script ({total_expected:.1f}s) "
            f"khac kha nhieu so voi video that ({video.duration:.1f}s). "
            f"Kiem tra lai timestamp trong file {SCRIPT_FILE}."
        )

    audio_clips = []
    overlay_clips = []

    for scene_num, start_sec, end_sec, subtitle_text in scenes:
        audio_path = os.path.join(AUDIO_DIR, f"scene_{scene_num:02d}.mp3")
        if os.path.exists(audio_path):
            clip = AudioFileClip(audio_path).with_start(start_sec)
            audio_clips.append(clip)
            print(f"[Canh {scene_num:02d}] audio tai {start_sec:.1f}s (dai {clip.duration:.1f}s)")
        else:
            print(f"[Canh {scene_num:02d}] khong co audio, bo qua.")

        if SHOW_SUBTITLES and subtitle_text:
            overlay_img = make_subtitle_overlay(subtitle_text, (video.w, video.h))
            tmp_path = f"_sub_{scene_num:02d}.png"
            overlay_img.save(tmp_path)
            duration = max(0.1, end_sec - start_sec)
            overlay_clip = ImageClip(tmp_path).with_start(start_sec).with_duration(duration)
            overlay_clips.append(overlay_clip)

    if not audio_clips:
        raise SystemExit(f"Khong co file audio nao trong thu muc '{AUDIO_DIR}/'.")

    final_audio = CompositeAudioClip(audio_clips)

    if overlay_clips:
        final_video = CompositeVideoClip([video] + overlay_clips)
    else:
        final_video = video

    final_video = final_video.with_audio(final_audio)

    final_video.write_videofile(
        OUTPUT_FILE,
        fps=video.fps,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )

    for scene_num, *_ in scenes:
        tmp_path = f"_sub_{scene_num:02d}.png"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    print(f"\nHoan tat! Video: {OUTPUT_FILE}")
    print(f"Phu de dang: {'BAT' if SHOW_SUBTITLES else 'TAT'} (doi SHOW_SUBTITLES o dau file de bat/tat)")


if __name__ == "__main__":
    main()
