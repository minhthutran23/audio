# -*- coding: utf-8 -*-
"""
Xuat audio nhanh cho 1 doan van xuoi don gian (khong can dinh dang script
day du voi nhan vat/canh) - dung khi chi can lay 1 doan lien tuc, giong nu.

Doc noi dung tu file "narration_text.txt" neu co (de chay qua trang web/
GitHub Actions), neu khong co thi dung doan van mac dinh ben duoi (de test
nhanh tren may).

Cai dat: pip install edge-tts
Chay:    python generate_simple_audio.py
"""

import asyncio
import os
import edge_tts

VOICE = "en-US-AnaNeural"   # giong nu, tre, cute
RATE = "+8%"
PITCH = "+0Hz"
OUTPUT_FILE = "narration.mp3"
TEXT_FILE = "narration_text.txt"

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


async def main():
    text = load_text()
    print(f"Dang doc: {text[:60]}...")
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(OUTPUT_FILE)
    print(f"Hoan tat! Da luu: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
