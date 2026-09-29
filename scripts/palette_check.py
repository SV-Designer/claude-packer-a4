#!/usr/bin/env python3
"""palette_check.py —— 配色前後的兩個機械檢查。

1) 分析封面主色（配色前）：
   python3 palette_check.py covers <_上傳用資料夾>
   → 印出每張 *_cover.jpg 的 5 個主色與色相 H，用來決定資訊塊要避開哪些色相

2) 驗算候選配色（配色後）：
   python3 palette_check.py check <外底色> <塊1> <塊2> <塊3> <塊4>
   例：python3 palette_check.py check "#608AAF" "#763B47" "#5C574D" "#99945B" "#99789C"
   → 每色的 H/S/V、白字對比；4 塊有重複色會報錯（退出碼 1）

判準（2026Q4 由 7 張過往範例歸納，見專案 CLAUDE.md〈配色規則〉）：
- 白字對比 ≥ 3.0 就放行（過往範例多在 2.5–3.5），< 3.0 印警告
- 4 個資訊塊必須互不相同
"""
import sys, glob, colorsys
from pathlib import Path
from PIL import Image

def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lum(h):
    c = [x / 255 for x in rgb(h)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def contrast(a, b="#FFFFFF"):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)

def hsv(h):
    x = colorsys.rgb_to_hsv(*[v / 255 for v in rgb(h)])
    return f"H{int(x[0]*360):>3} S{int(x[1]*100):>2} V{int(x[2]*100):>3}"

def covers(folder):
    for f in sorted(glob.glob(str(Path(folder) / "*_cover.jpg"))):
        im = Image.open(f).convert("RGB").resize((120, 120))
        q = im.quantize(5, method=Image.Quantize.MEDIANCUT)
        pal = q.getpalette()
        parts = []
        for cnt, i in sorted(q.getcolors(), reverse=True):
            h = "#%02X%02X%02X" % tuple(pal[i*3:i*3+3])
            parts.append(f"{h}({cnt*100//14400}% {hsv(h)})")
        print(Path(f).name, " ".join(parts))

def check(bg, blocks):
    print(f"外底色 {bg} {hsv(bg)}")
    bad = 0
    for i, b in enumerate(blocks, 1):
        c = contrast(b)
        flag = "" if c >= 3.0 else "  ⚠️ 白字對比偏低"
        print(f"  Artist_{i} {b} {hsv(b)} 白字{c:.2f}{flag}")
    if len({b.upper() for b in blocks}) != len(blocks):
        print("  [!] 4 個資訊塊有重複色"); bad = 1
    if len(blocks) != 4:
        print("  [!] 資訊塊要剛好 4 色"); bad = 1
    return bad

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "covers":
        covers(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "check":
        sys.exit(check(sys.argv[2], sys.argv[3:]))
    else:
        sys.exit(__doc__)
