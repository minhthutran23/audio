# -*- coding: utf-8 -*-
"""
Dữ liệu kịch bản dùng chung: mỗi cảnh gồm (số thứ tự, chữ Hán, pinyin).
generate_audio.py dùng cột chữ Hán để tạo audio.
make_video.py dùng cả chữ Hán + pinyin để làm phụ đề đè lên ảnh.
Sửa nội dung ở đây là đồng bộ cho cả audio lẫn phụ đề.
"""

SCENES = [
    ("01", "早上七点，闹钟响了。", "Zǎoshang qī diǎn, nàozhōng xiǎng le."),
    ("02", "我很累。", "Wǒ hěn lèi."),
    ("03", "现在几点?", "Xiànzài jǐ diǎn?"),
    ("04", "早饭很好吃。", "Zǎofàn hěn hǎochī."),
    ("05", "今天下雨。", "Jīntiān xià yǔ."),
    ("06", "天气不好。", "Tiānqì bù hǎo."),
    ("07", "我走路去咖啡店。", "Wǒ zǒulù qù kāfēi diàn."),
    ("08", "你好!好久不见!", "Nǐ hǎo! Hǎojiǔ bùjiàn!"),
    ("09", "咖啡店在哪儿?", "Kāfēi diàn zài nǎr?"),
    ("10", "我们一起去吧。", "Wǒmen yīqǐ qù ba."),
    ("11", "我们到了咖啡店。", "Wǒmen dào le kāfēi diàn."),
    ("12", "你要喝什么?", "Nǐ yào hē shénme?"),
    ("13", "我要一杯咖啡。", "Wǒ yào yì bēi kāfēi."),
    ("14", "这个很好喝。", "Zhège hěn hǎo hē."),
    ("15", "我要工作。", "Wǒ yào gōngzuò."),
    ("16", "电脑坏了!", "Diànnǎo huài le!"),
    ("17", "怎么了?", "Zěnme le?"),
    ("18", "没问题了!", "Méi wèntí le!"),
    ("19", "我们去吃午饭。", "Wǒmen qù chī wǔfàn."),
    ("20", "你想吃什么?", "Nǐ xiǎng chī shénme?"),
    ("21", "很好吃!", "Hěn hǎochī!"),
    ("22", "我们去市场看看。", "Wǒmen qù shìchǎng kànkan."),
    ("23", "多少钱?", "Duōshǎo qián?"),
    ("24", "太贵了!", "Tài guì le!"),
    ("25", "便宜一点吧。", "Piányi yīdiǎn ba."),
    ("26", "谢谢!", "Xièxie!"),
    ("27", "再见!", "Zàijiàn!"),
    ("28", "我走路回家。", "Wǒ zǒulù huí jiā."),
    ("29", "妈妈，我很好。", "Māma, wǒ hěn hǎo."),
    ("30", "晚安。", "Wǎn'ān."),
]
