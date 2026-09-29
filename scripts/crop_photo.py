#!/usr/bin/env python3
"""crop_photo.py —— 把藝人照裁成模版 Img 框比例（270×140），可指定垂直起點避免切到臉。

用法：
  python3 crop_photo.py <圖檔> <top比例 0~1>
  例：python3 crop_photo.py _上傳用/2_photo.jpg 0.0   → 從最上方開始裁
產出：同資料夾 <原名>_crop.jpg

為什麼要本機裁：Figma upload_assets 的 FILL 只會置中裁切，
2026Q4 有兩張（臉在上 1/3）置中裁會切到頭。先看圖判斷臉的位置再給 top。
top 超出範圍會自動夾到底，不會報錯。
"""
import sys
from pathlib import Path
from PIL import Image

RATIO = 140 / 270  # 模版 Img 框 高/寬

def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, top = Path(sys.argv[1]), float(sys.argv[2])
    im = Image.open(src).convert("RGB")
    w, h = im.size
    bh = round(w * RATIO)
    if bh > h:  # 原圖比框還扁 → 改以高為準裁寬
        bw = round(h / RATIO)
        x = (w - bw) // 2
        box = (x, 0, x + bw, h)
    else:
        y = min(max(round(h * top), 0), h - bh)
        box = (0, y, w, y + bh)
    out = src.with_name(src.stem + "_crop.jpg")
    im.crop(box).save(out, quality=92)
    print(f"{out}  box={box}")

if __name__ == "__main__":
    main()
