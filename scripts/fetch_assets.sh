#!/bin/bash
# fetch_assets.sh —— 好丘 A4：Seafile 素材下載＋依信件順序配對＋縮圖＋流水號（skill 步驟 3 的機械段）
#
# 用法：
#   ./fetch_assets.sh <素材夾名 例 2026Q4（parse_mail.py 的 asset_dir）> <seafile_token> <順序.txt>
#   token ＝ Seafile 分享連結 /d/ 與結尾 / 之間那 20 碼
#   順序.txt ＝ 每行一個藝人名，照信件順序（第 1 行＝Artist_1 … 第 4 行＝Artist_4）
#
# 產出：
#   $DELIVERY_DIR/素材暫存/{素材夾}/原圖/       原檔
#   $DELIVERY_DIR/素材暫存/{素材夾}/_上傳用/    {n}_photo.jpg（長邊 1800）、{n}_cover.jpg（長邊 900）
#   $DELIVERY_DIR/素材暫存/{素材夾}/清單.md     配對結果
#   DELIVERY_DIR 讀 ~/.config/claude-packer-a4/env（路徑不寫死＝去識別化）
#
# 配對規則（2026Q4 實測 Seafile 檔名）：「{藝人}_藝人照片.{jpg|png}」「{藝人}_{作品}_專輯封面.jpg」
#   配不到 → 大聲報錯、退出碼 1，請人工核對檔名，🚫 不要自己猜。
# 🚫 Seafile 若要求登入 → 停下請使用者用瀏覽器下載，不要自己找帳密。
# 🕳️ macOS bash 3.2：變數後緊接全形字元會被吃進變數名，一律寫 ${var}。

set -u
D="${1:?請給素材夾名（年Q季），例：2026Q4}"
TOK="${2:?請給 Seafile token}"
ORDER="${3:?請給順序.txt 路徑}"
CONF="$HOME/.config/claude-packer-a4/env"
[ -f "$CONF" ] && . "$CONF"
if [ -z "${DELIVERY_DIR:-}" ]; then
  echo "  [!] 找不到 DELIVERY_DIR（${CONF}）→ 先跑 skill 第 ① 步設定交付位置"; exit 1
fi
BASE="${DELIVERY_DIR}/素材暫存/${D}"
RAW="$BASE/原圖"; UP="$BASE/_上傳用"
# 🛑 批次夾已有輸出＝那是做完的批次，拒絕覆蓋（2026-09-29 交接驗收抓到：同日重跑會蓋掉正式素材）
if [ -d "$BASE/輸出" ] && [ -n "$(ls -A "$BASE/輸出" 2>/dev/null)" ]; then
  echo "  [!] ${BASE}/輸出 已有檔案＝已完成的批次，停止以免覆蓋。測試請用 parse_mail.py --test 產生的 asset_dir"
  exit 1
fi
mkdir -p "$RAW" "$UP"

echo "▶ 下載素材到 ${RAW}"
list=$(curl -sfL "https://${SEAFILE_HOST:?請設定 SEAFILE_HOST 環境變數}/d/${TOK}/" \
      | grep -oE 'files/\?p=/[^"]+&dl=1' | sed 's|^files/?p=/||; s|&dl=1$||' | sort -u)
if [ -z "$list" ]; then
  echo "  [!] 抓不到檔案清單。可能原因 -- token 過期 / 連結要求登入 / 頁面結構改版"
  echo "      請用瀏覽器開 https://${SEAFILE_HOST:?請設定 SEAFILE_HOST 環境變數}/d/${TOK}/ 確認"
  exit 1
fi
n=0
while IFS= read -r enc; do
  [ -z "$enc" ] && continue
  name=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.unquote(sys.argv[1]))' "$enc")
  if curl -sfL -o "$RAW/$name" "https://${SEAFILE_HOST:?請設定 SEAFILE_HOST 環境變數}/d/${TOK}/files/?p=/${enc}&dl=1"; then
    n=$((n+1))
  else
    echo "  [!] 下載失敗: ${name}"
  fi
done <<< "$list"
echo "  [v] 共 ${n} 個檔"

echo "▶ 依 ${ORDER} 配對＋縮圖"
{ echo "# ${D} 素材清單（fetch_assets.sh 自動產生）"; echo; echo "| # | 藝人 | 藝人照片 | 專輯封面 |"; echo "|---|---|---|---|"; } > "$BASE/清單.md"
i=0; err=0
while IFS= read -r artist || [ -n "$artist" ]; do
  artist=$(printf '%s' "$artist" | sed 's/[[:space:]]*$//')
  [ -z "$artist" ] && continue
  i=$((i+1))
  photo=$(ls "$RAW" | grep -F "${artist}_藝人照片" | head -1)
  cover=$(ls "$RAW" | grep -F "${artist}_" | grep -F "專輯封面" | head -1)
  if [ -z "$photo" ] || [ -z "$cover" ]; then
    echo "  [!] 第 ${i} 組「${artist}」配不到：照片=${photo:-無} 封面=${cover:-無}"
    err=1; continue
  fi
  sips -s format jpeg -s formatOptions 92 -Z 1800 "$RAW/$photo" --out "$UP/${i}_photo.jpg" >/dev/null
  sips -s format jpeg -s formatOptions 92 -Z 900  "$RAW/$cover" --out "$UP/${i}_cover.jpg" >/dev/null
  echo "| ${i} | ${artist} | ${photo} | ${cover} |" >> "$BASE/清單.md"
  echo "  [v] ${i} ${artist}"
done < "$ORDER"
[ "$i" -ne 4 ] && { echo "  [!] 順序.txt 有 ${i} 組，模版固定 4 組"; err=1; }
echo "▶ 清單：$BASE/清單.md"
exit $err
