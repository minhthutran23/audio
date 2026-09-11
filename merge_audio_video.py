# -*- coding: utf-8 -*-
"""
Ghep audio tung canh (scene_00.mp3, scene_01.mp3, ...) vao dung vi tri
thoi gian tren video da dung san (story_final.mp4), thay vi chi noi lien
audio lai voi nhau - tranh bi lech dan ve sau neu do dai audio thuc te
khac voi uoc tinh.

Gia dinh: canh 0 (Title Card) dai 6s, cac canh 1-10 moi canh dai 10s
(khop voi tong do dai video 106s). Neu cau truc video cua ban khac,
sua lai SCENE_DURATIONS ben duoi cho dung.

Cai dat: pip install moviepy
Chay:    python merge_audio_video.py
"""

import os
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips

VIDEO_FILE = "story_final.mp4"
AUDIO_DIR = "episode_audio"
OUTPUT_FILE = "melloday_ep01_final.mp4"

# So giay MOI CANH chiem tren video that (canh 0 la title card)
SCENE_DURATIONS = {
    0: 6,
    1: 10, 2: 10, 3: 10, 4: 10, 5: 10,
    6: 10, 7: 10, 8: 10, 9: 10, 10: 10,
}


def compute_start_times():
    """Tra ve dict {scene_num: thoi diem bat dau tren video (giay)}."""
    starts = {}
    t = 0
    for scene_num in sorted(SCENE_DURATIONS):
        starts[scene_num] = t
        t += SCENE_DURATIONS[scene_num]
    return starts, t


def main():
    if not os.path.exists(VIDEO_FILE):
        raise SystemExit(f"Khong tim thay {VIDEO_FILE}. Dat file video cung thu muc voi script nay.")

    video = VideoFileClip(VIDEO_FILE)
    print(f"Video: {VIDEO_FILE} - {video.duration:.1f}s")

    starts, total_expected = compute_start_times()
    if abs(total_expected - video.duration) > 1.0:
        print(
            f"CANH BAO: tong thoi luong theo SCENE_DURATIONS ({total_expected}s) "
            f"khac voi video that ({video.duration:.1f}s). Kiem tra lai SCENE_DURATIONS."
        )

    audio_clips = []
    for scene_num, start_time in starts.items():
        path = os.path.join(AUDIO_DIR, f"scene_{scene_num:02d}.mp3")
        if not os.path.exists(path):
            print(f"[Canh {scene_num:02d}] khong co audio, bo qua.")
            continue
        clip = AudioFileClip(path).with_start(start_time)
        audio_clips.append(clip)
        print(f"[Canh {scene_num:02d}] dat audio tai giay {start_time} (dai {clip.duration:.1f}s)")

    if not audio_clips:
        raise SystemExit("Khong co file audio nao trong thu muc episode_audio/.")

    final_audio = CompositeAudioClip(audio_clips)
    final_video = video.with_audio(final_audio)

    final_video.write_videofile(
        OUTPUT_FILE,
        fps=video.fps,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    print(f"\nHoan tat! Video co tieng: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
