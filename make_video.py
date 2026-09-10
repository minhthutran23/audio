# -*- coding: utf-8 -*-
"""
Script ghép 30 ảnh + 30 audio thành 1 video câu chuyện hoàn chỉnh.
CHẠY SCRIPT NÀY TRÊN MÁY TÍNH CỦA BẠN, sau khi đã có:
  - Thư mục "images/" chứa 30 ảnh: 01.png, 02.png, ..., 30.png
  - Thư mục "audio/"  chứa 30 audio: 01.mp3, 02.mp3, ..., 30.mp3
    (đặt tên đúng số thứ tự như trên, không cần trùng tên gốc)

Yêu cầu cài đặt:
    pip install moviepy

Chạy:
    python make_video.py

Kết quả: file "story_video.mp4" — mỗi ảnh hiển thị đúng bằng độ dài audio
tương ứng, có thêm 0.5 giây khoảng lặng giữa các cảnh cho dễ nghe.
"""

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
import os

IMAGE_DIR = "images"
AUDIO_DIR = "audio"
OUTPUT_FILE = "story_video.mp4"
PAUSE_BETWEEN_SCENES = 0.5  # giây

clips = []

for i in range(1, 31):
    num = f"{i:02d}"
    img_path = os.path.join(IMAGE_DIR, f"{num}.png")
    audio_path = os.path.join(AUDIO_DIR, f"{num}.mp3")

    if not os.path.exists(img_path):
        print(f"⚠️  Không tìm thấy ảnh: {img_path} — bỏ qua cảnh {num}")
        continue
    if not os.path.exists(audio_path):
        print(f"⚠️  Không tìm thấy audio: {audio_path} — bỏ qua cảnh {num}")
        continue

    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration + PAUSE_BETWEEN_SCENES

    img_clip = ImageClip(img_path).set_duration(duration)
    img_clip = img_clip.set_audio(audio_clip.set_start(0))

    clips.append(img_clip)
    print(f"[{num}] {duration:.1f}s")

if not clips:
    print("Không có cảnh nào để ghép. Kiểm tra lại thư mục images/ và audio/.")
else:
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(OUTPUT_FILE, fps=24)
    print(f"\nHoàn tất! Video đã lưu tại: {OUTPUT_FILE}")
