# -*- coding: utf-8 -*-
"""
Script tạo 30 file audio tiếng Trung tương ứng với 30 ảnh câu chuyện.
CHẠY SCRIPT NÀY TRÊN MÁY TÍNH CỦA BẠN (cần có internet để gọi Google TTS).

Cài đặt trước khi chạy:
    pip install gTTS

Chạy:
    python generate_audio.py

Kết quả: thư mục "audio/" chứa 30 file 01.mp3 -> 30.mp3
Tên file khớp với thứ tự 30 ảnh đã tạo trước đó, dễ ghép vào video.
"""

from gtts import gTTS
import os
import time

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mỗi dòng = 1 ảnh. Nội dung là câu thoại/tường thuật tiếng Trung tương ứng
# từng cảnh trong câu chuyện (đã dùng để viết prompt ảnh trước đó).
scenes = [
    ("01", "早上七点，闹钟响了。"),                     # ngủ, chuông báo thức
    ("02", "我很累。"),                                  # thức dậy mệt
    ("03", "现在几点?"),                                 # đánh răng
    ("04", "早饭很好吃。"),                              # ăn sáng
    ("05", "今天下雨。"),                                # nhìn trời mưa
    ("06", "天气不好。"),                                # mặc áo mưa
    ("07", "我走路去咖啡店。"),                          # đi bộ dưới mưa
    ("08", "你好!好久不见!"),                            # gặp bạn
    ("09", "咖啡店在哪儿?"),                             # hỏi đường
    ("10", "我们一起去吧。"),                            # đi cùng nhau
    ("11", "我们到了咖啡店。"),                          # vào quán
    ("12", "你要喝什么?"),                               # order
    ("13", "我要一杯咖啡。"),                            # gọi cà phê
    ("14", "这个很好喝。"),                              # trò chuyện
    ("15", "我要工作。"),                                # mở laptop
    ("16", "电脑坏了!"),                                 # laptop lỗi
    ("17", "怎么了?"),                                   # bạn hỏi
    ("18", "没问题了!"),                                 # ổn rồi
    ("19", "我们去吃午饭。"),                            # vào quán ăn
    ("20", "你想吃什么?"),                               # xem menu
    ("21", "很好吃!"),                                   # ăn ngon
    ("22", "我们去市场看看。"),                          # đi chợ
    ("23", "多少钱?"),                                   # hỏi giá
    ("24", "太贵了!"),                                   # đắt quá
    ("25", "便宜一点吧。"),                              # trả giá
    ("26", "谢谢!"),                                     # cảm ơn
    ("27", "再见!"),                                     # tạm biệt
    ("28", "我走路回家。"),                              # về nhà
    ("29", "妈妈，我很好。"),                            # gọi mẹ
    ("30", "晚安。"),                                    # chúc ngủ ngon
]

for idx, (num, text) in enumerate(scenes, start=1):
    filepath = os.path.join(OUTPUT_DIR, f"{num}.mp3")
    print(f"[{idx}/30] Đang tạo: {filepath}  ->  {text}")
    try:
        tts = gTTS(text=text, lang="zh-CN", slow=False)
        tts.save(filepath)
    except Exception as e:
        print(f"  Lỗi tại câu '{text}': {e}")
    time.sleep(0.5)  # tránh gọi API quá nhanh bị chặn

print("\nHoàn tất! 30 file audio nằm trong thư mục 'audio/'.")
print("Tên file 01.mp3 -> 30.mp3 khớp với thứ tự 30 ảnh đã tạo trước đó.")
