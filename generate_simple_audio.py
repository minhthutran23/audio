# -*- coding: utf-8 -*-
"""
Xuat audio nhanh cho 1 doan van xuoi don gian (giong nu), sau do tu dong
ghep vao 1 video nen den (khong can anh/video nao khac) - dung khi chi
can file video co tieng, khong can file audio rieng.

Doc noi dung tu file "narration_text.txt" neu co (de chay qua trang web/
GitHub Actions), neu khong co thi dung doan van mac dinh ben duoi (de test
nhanh tren may).

Cai dat: pip install edge-tts moviepy
Chay:    python generate_simple_audio.py
"""

import asyncio
import os
import edge_tts
from moviepy import ColorClip, AudioFileClip

VOICE = "en-US-AnaNeural"   # giong nu, tre, cute
RATE = "+8%"
PITCH = "+0Hz"
AUDIO_FILE = "narration.mp3"
VIDEO_FILE = "narration_video.mp4"
TEXT_FILE = "narration_text.txt"

VIDEO_SIZE = (1280, 720)   # doi kich thuoc video o day neu can (vd doc: (720,1280))

DEFAULT_TEXT = """Today, I wanted something warm and comforting, so I decided to make Japanese chicken curry.
I started with some chicken, carrots, onions, and potatoes. First, I browned the chicken until it got a little golden on the outside.
Then came the vegetables, followed by the curry sauce. And honestly, this is when the kitchen started smelling really good.
I let everything simmer together until the sauce became thick and rich, and the chicken was nice and tender.
And of course... I couldn't just serve it normally. So I turned the rice into a little Corgi.
And now, this is definitely my kind of comfort food."""


def load_text():
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content
    return DEFAULT_TEXT


async def synth(text):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(AUDIO_FILE)


def make_black_video():
    audio = AudioFileClip(AUDIO_FILE)
    video = ColorClip(size=VIDEO_SIZE, color=(0, 0, 0), duration=audio.duration)
    video = video.with_audio(audio)
    video.write_videofile(
        VIDEO_FILE,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )


async def main():
    text = load_text()
    print(f"Dang doc: {text[:60]}...")
    await synth(text)
    print(f"Da tao audio: {AUDIO_FILE}")
    make_black_video()
    print(f"Hoan tat! Video: {VIDEO_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
