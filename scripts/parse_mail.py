#!/usr/bin/env python3
"""parse_mail.py —— 好丘 A4 需求信（Gmail get_thread PLAIN_TEXT 的第一封 plaintextBody）→ 結構化欄位。

用法：
  python3 parse_mail.py <信件純文字.txt> [--order 順序.txt輸出路徑] [--test] [--pasted]
  --pasted：信是使用者直接貼的（可能沒有轉寄標頭）→ 需求負責人抓不到只警告、不擋
  --test：測試模式，batch 加「-測試」、notion_title 加「 (測試)」（file_stem 跟著 batch 變）
輸出 JSON：requester / deadline / delivery_date(＝死線，Notion 預期交稿用) / quarter / notion_title / batch(製作日-Q季度，資料夾名) /
          file_stem(批次_多國，檔名與 Figma 框名) / asset_dir(素材夾名 {年}Q{季}，例 2026Q4) /
          theme / theme_short(Notion「主題：」用的關鍵字，例 冬季) / desc / seafile_token / artists[{name, work}]
  --order 會順便寫出 fetch_assets.sh 要吃的 順序.txt（每行一個藝人名，照信件順序）

抓法（2026Q4 信件格式）：
- 原始寄件人：內文的「寄件者： 名字 <email>」行（轉寄信才有）——🔴 不是 Gmail thread 第一封的 sender（那是轉寄人）
- 死線：「死線：YYYY-MM-DD」
- 主題：含「主題」的那一行
- 藝人：「- 藝人名：專輯《作品》」這種行；冒號全形/半形都吃
- Seafile：https://<SEAFILE_HOST>/d/{token}/
任一必填欄位抓不到 → 印出缺哪個、退出碼 1，🚫 不要自己補猜。
"""
import sys, re, json, datetime

TEST = "--test" in sys.argv
PASTED = "--pasted" in sys.argv

def parse(text):
    t = text.replace("\r", "")
    # 引用回覆（> 開頭）會重複一次內容，只看非引用行
    lines = [l for l in t.split("\n") if not l.lstrip().startswith(">")]
    body = "\n".join(lines)
    r = {}
    m = re.search(r"寄件者[:：]\s*(.+?)\s*<([^>]+)>", body)
    r["requester"] = {"name": m.group(1), "email": m.group(2)} if m else None
    m = re.search(r"死線[:：]\s*(\d{4}-\d{2}-\d{2})", body)
    r["deadline"] = m.group(1) if m else None
    # 交付日＝死線（2026-09-29 拍板；使用者另有交代才改）——只給 Notion「預期交稿」，不用於命名
    r["delivery_date"] = r["deadline"].replace("-", "") if r["deadline"] else None
    m = re.search(r"(\d{4})\s*Q([1-4])", body)
    r["quarter"] = f"Q{m.group(2)}" if m else None
    r["notion_title"] = f"Packer_好丘A4文宣{r['quarter']}" if r["quarter"] else None
    # 命名代號＝製作日（今天）-Q季度（2026-09-29 拍板），資料夾／檔名／Figma 框名都用它
    r["batch"] = f"{datetime.date.today():%Y%m%d}-{r['quarter']}" if r["quarter"] else None
    # 檔名／Figma 框名（2026-09-29 定案）：{批次}_多國；交付檔再加 @4x.jpg
    if TEST and r["batch"]:  # 測試模式：所有命名加「-測試」，避免撞到正式批次（同日重跑必撞）
        r["batch"] += "-測試"
        r["notion_title"] += " (測試)"
    r["file_stem"] = f"{r['batch']}_多國" if r["batch"] else None
    # 素材夾名＝{年}Q{季}（2026-09-29 使用者：素材放 $DELIVERY_DIR/素材暫存/Q幾；加年份避免隔年同季撞名）
    r["asset_dir"] = (f"{m.group(1)}Q{m.group(2)}" + ("-測試" if TEST else "")) if m else None
    m = re.search(r"^[\s\-•*]*(.*主題.*)$", body, re.M)
    r["theme"] = m.group(1).strip() if m else None
    # theme_short＝Notion 卡「主題：」只放關鍵字（例：冬季），其餘需求句是贅述
    m2 = re.search(r"以\s*[「『“\"]?([^，。,「」『』“”\"\s]{1,10}?)[」』”\"]?\s*(?:為|作為|当作|當作)\s*主題", r["theme"] or "")
    r["theme_short"] = m2.group(1) if m2 else None
    m = re.search(r"需求敘述[:：]\s*(.+)", body)
    r["desc"] = m.group(1).strip() if m else None
    # 素材連結主機不寫死＝去識別化；預設吃 SEAFILE_HOST 環境變數，沒設就吃任何網域（只認路徑格式 /d/{20碼}/）
    import os
    host_pat = re.escape(os.environ.get("SEAFILE_HOST", "")) if os.environ.get("SEAFILE_HOST") else r"[a-zA-Z0-9.\-]+"
    m = re.search(host_pat + r"/d/([0-9a-f]{20})", body)
    r["seafile_token"] = m.group(1) if m else None
    arts = []
    for m in re.finditer(r"^[\s\-•*]*([^\n：:]+?)\s*[:：]\s*(專輯|單曲|EP)\s*《([^》]+)》", body, re.M):
        arts.append({"name": m.group(1).strip(), "work": f"{m.group(2)}《{m.group(3).strip()}》"})
    r["artists"] = arts
    return r

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    r = parse(open(sys.argv[1], encoding="utf-8").read())
    print(json.dumps(r, ensure_ascii=False, indent=2))
    need = ("deadline", "quarter", "seafile_token") if PASTED else ("requester", "deadline", "quarter", "seafile_token")
    missing = [k for k in need if not r[k]]
    if PASTED and not r["requester"]:
        print("[!] 貼上的內容沒有「寄件者：」行 → 需求負責人留空，請使用者在 Notion 手動填", file=sys.stderr)
    if len(r["artists"]) != 4:
        missing.append(f"artists（抓到 {len(r['artists'])} 組，模版固定 4 組）")
    if "--order" in sys.argv and len(r["artists"]) == 4:
        p = sys.argv[sys.argv.index("--order") + 1]
        open(p, "w", encoding="utf-8").write("\n".join(a["name"] for a in r["artists"]) + "\n")
        print(f"▶ 已寫出 {p}", file=sys.stderr)
    if not r["theme_short"]:
        print("[!] 抓不到主題關鍵字（theme_short）→ 停下問使用者主題是什麼，別自己猜", file=sys.stderr)
    if missing:
        print("[!] 抓不到：" + "、".join(missing), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
