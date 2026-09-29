---
name: claude-packer-a4
description: >
  店面 A4 宣傳物每季套版全流程：讀需求信（使用者貼上優先，打「抓信」才用 Gmail）→ Notion 開卡（選配，
  首次使用時問；只填內文）→ 素材下載 → Figma 開新 page、用模版副本換 4 組藝人照／封面／文字＋配色 →
  停下等使用者確認配色 → 輸出 4x JPG 到交付夾。觸發詞：「做好丘A4」（可依自己習慣改）。
  需要 Figma MCP（use_figma／upload_assets／get_screenshot）；Notion MCP、Gmail MCP 選配。
---

# 店面 A4 宣傳物套版

每季把需求信變成 4 組藝人照／專輯封面／藝人名／作品的 A4 宣傳物，套版＋換色一次做完。

## 🔴 這是去識別化的公開版，安裝後要先設定

原始版本含公司內部真值（Figma 檔、Notion 資料庫、素材主機、路徑）。本版全部改讀環境變數，**第一次用之前**：

```bash
mkdir -p ~/.config/claude-packer-a4
cat > ~/.config/claude-packer-a4/env <<'EOF'
DELIVERY_DIR="<成品交付夾絕對路徑，例 ~/Documents/A4文宣>"
REFERENCE_DIR="<配色參考圖資料夾絕對路徑，沒有就留空，跳過取樣>"
FIGMA_FILE_KEY="<你的 Figma 檔 key>"
NOTION_DATA_SOURCE_ID="<你的 Notion 資料庫 data_source_id，不開卡可留空>"
SEAFILE_HOST="<你的素材主機網域，例 seafile.example.com；用別的素材服務就不會用到這個變數>"
USE_NOTION=true
EOF
```

`scripts/` 內 4 支腳本已改成讀這個 env 檔，不用改程式碼。

## 你的 Figma 檔要有這個結構（本 skill 假設的骨架）

- 一個「模版」頁，內含一個模版 frame：595×842、四組 `Artist_1`~`Artist_4`，每組一張照片區塊（`Img`）＋一個資訊塊（`Context`，內含 `Cover`／`Title`／`Song`）
- **不直接改模版本體**——每次都 clone 一份到當季新 page
- 換模版檔／node id 時，把下面「變數」段的 node id 換成你自己的（`get_metadata` 現查）

## 先決條件

| 需要 | 用途 | 沒有的話 |
|---|---|---|
| Figma MCP | 讀結構、換圖、換字、輸出 | **無法繼續**，停下請使用者確認 |
| Notion MCP | 開需求卡（選配） | `USE_NOTION=false` 就不需要 |
| Gmail MCP | 使用者打「抓信」時才用 | 請使用者直接貼信內文 |
| macOS `sips` | 壓縮素材、驗尺寸、轉檔 | 系統內建 |
| Python 3 | 跑 `scripts/` 內腳本 | — |

⚠️ **動 `use_figma` 前一定要先載入 `/figma-use` skill**（Figma MCP 官方硬性要求）。

變數：`FK="$FIGMA_FILE_KEY"`（讀 env）；模版 node id、clone 來源 node id 請依你自己的 Figma 檔填（首次使用時問使用者，之後寫進 env 或直接寫死在這裡都可以）
命名代號（`parse_mail.py` 產出）：`{批次}`＝`{製作日YYYYMMDD}-Q{季度}`（例 `20260929-Q4`），`{file_stem}`＝`{批次}_多國`，`{素材夾}`＝`asset_dir`＝`{年}Q{季}`（例 `2026Q4`）
素材位置：`W=$DELIVERY_DIR/素材暫存/{素材夾}`

⚠️ **Figma MCP 有呼叫額度限制**（實測合併寫入與截圖、不要同一輪並行發，避免拍到舊畫面）。

## SOP

使用者主動喊觸發詞 → ①檢查 MCP＋首次問交付檔存哪／要不要開 Notion 卡 → ②抓信＆開卡（選配）→ ③Figma 開新 page 用模版副本製作 → **④停下等使用者點頭** → ⑤輸出交付

**停點＝② 沒附信時的「請貼信」提示，和第 ④ 步**。其餘步驟只在「腳本退出碼 1／配不到檔／同名已存在」這類異常時才停下問。
**Figma 額度用完**（`use_figma` 回 rate limit）→ 立刻停，回報做到哪一步＋已建立的 page／node id，不重試。

### 🧪 測試模式（使用者說「測試」時）
- `parse_mail.py` 一律加 `--test` → `batch`＝`{製作日}-Q{季}-測試`、`notion_title` 加 ` (測試)`，`file_stem`／page 名／素材暫存夾／交付夾全部跟著變 → **不會撞到正式批次**
- ⑤ 的「參考庫加一張」與「更新紀錄」**跳過**
- 測完收尾（刪除前先問）：刪 Figma 測試 page、刪測試素材暫存夾、刪測試交付夾；Notion 測試卡（若有開）**請使用者手動封存**

### ① 開工檢查：MCP（每次都查）＋交付位置／要不要開 Notion 卡（只有首次問）
**先讀 `~/.config/claude-packer-a4/env`**：有這個檔就跳過「首次問」，直接照 `USE_NOTION` 的值決定要不要查 Notion。

**首次（沒有這個 env 檔）** → 先用 3–4 行白話說明這支 skill 會做哪幾步、哪裡會停下等他，再一次問：
1. 交付檔要存哪？
2. 要順便在 Notion 開需求卡嗎？（只是存檔紀錄，不影響套版本身）
→ 都確認完，把值寫進 `~/.config/claude-packer-a4/env`（見上方安裝段），並 `mkdir -p` 交付資料夾
- 使用者之後想改主意 → 直接改這個 env 檔，不用整支重跑

**MCP 檢查（每次都跑，第一個動作）**：`claude mcp list 2>/dev/null | grep -i -E 'gmail|notion|figma'`
- 必要 `plugin:figma:figma` 為 `✔ Connected`
- `USE_NOTION=true` 時才連帶檢查 Notion；`false` 時完全跳過
- Gmail 只有使用者回「抓信」時才需要
- 有缺 → 停下，一次列出全部缺的，附操作步驟：「在對話框輸入 `/mcp` → 選該項目 → 啟用（或登入）→ 回來打『繼續』」

**交付位置**：讀 env 的 `DELIVERY_DIR=`；最終路徑 `$DELIVERY_DIR/{批次}/{file_stem}@4x.jpg`

### ② 抓信＆開卡
**信件來源——貼信優先，沒貼才用 Gmail**
- 使用者喊觸發詞時沒附信 → ①做完後停下，提示照抄：

  > **請貼上這季的需求信內文**（複製貼上）
  > 要包含：死線、4 組藝人與作品、素材連結。
  > 手邊沒有信的話，打「**抓信**」我就去 Gmail 找最新一封。

- **A. 使用者有貼信** → 原文照存 scratchpad 的 `mail.txt`（🚫 不改字、不刪行），跑腳本時加 `--pasted`
- **B. 使用者回「抓信」** → Gmail：`search_threads(...)` → 取最新 thread → `get_thread(threadId, messageFormat='PLAIN_TEXT')` → 第一封 `plaintextBody` 存 `mail.txt`
  - Gmail 沒接上或搜不到 → 請使用者直接貼信內文（＝改走 A）
- `python3 scripts/parse_mail.py <mail.txt> [--test] [--pasted]` 取得 `batch`
  → `mkdir -p $W`、把 mail.txt 移進去 → 再跑一次（旗標同上）加 `--order $W/順序.txt`
  - 退出碼 1 ＝ 有欄位抓不到 → 停下給使用者看，🚫 不要自己補
- 在對話列一行摘要（4 組藝人／作品、死線、需求負責人），**不停**，直接往下做
- Notion（**只有 `USE_NOTION=true` 才做這段；`false` 就整段跳過，直接進③**）：
  - `notion-search(query=..., data_source_url='collection://'+NOTION_DATA_SOURCE_ID)` → 同名卡已存在就停下問
  - `notion-create-pages(parent={data_source_id: NOTION_DATA_SOURCE_ID}, pages=[{properties:{Name:<notion_title>}, icon:'🐦', content:<骨架，見下方〉}])`
  - 內文骨架：`- 需求敘述：` `- 素材：<連結>` `- 預期交稿：<deadline，YYYY-MM-DD>` `- 主題：<theme_short，只放關鍵字，不貼整句>` ＋ `### 音樂人資訊` 4 行 `- 藝人：作品`（🚫 不含「配色：」欄位——色值不寫回 Notion，只留在 Figma 與你自己的專案筆記）
  - 🚫 properties 只帶 Name；回報卡片連結，提醒使用者欄位手動填

### ③ Figma 製作
**素材**
- `/bin/bash scripts/fetch_assets.sh {素材夾} {token} $W/順序.txt`（素材夾已有 `輸出/` 會拒跑＝防覆蓋正式批次）
- 4 張 `_上傳用/{n}_photo.jpg` 拼成一張縮圖用 Read 看：臉在上 1/3 的 → `python3 scripts/crop_photo.py <圖> <top>`，上傳改用 `_crop.jpg`
- `python3 scripts/palette_check.py covers $W/_上傳用` → 記下封面主色相

**開新 page＋套版**（先載 `figma:figma-use` skill）——一次 `use_figma`：
```js
if (figma.root.children.some(p => p.name === '{批次}')) throw new Error('page {批次} 已存在');
const page = figma.createPage(); page.name = '{批次}';
await figma.setCurrentPageAsync(page);
const tpl = await figma.getNodeByIdAsync('<你的模版 node id>');   // 🚫 本體不改
const c = tpl.clone(); page.appendChild(c); c.x = 0; c.y = 0; c.name = '{file_stem}';
await figma.loadFontAsync({family:'Noto Sans TC',style:'Bold'});
await figma.loadFontAsync({family:'Noto Sans TC',style:'Regular'});
const data = [[藝人1,作品1],…];
const hex = h => ({r:parseInt(h.slice(1,3),16)/255,g:parseInt(h.slice(3,5),16)/255,b:parseInt(h.slice(5,7),16)/255});
const bg = '#……', blocks = ['#……','#……','#……','#……'];
c.fills = [{type:'SOLID', color:hex(bg)}];
const ids = {img:[],cover:[],w:[]};
for (let i=1;i<=4;i++){
  const a = c.findOne(n=>n.name===`Artist_${i}`);
  const ctx = a.children.find(k=>k.name!=='Img');   // 不靠名稱，防誤改名
  ctx.fills = [{type:'SOLID', color:hex(blocks[i-1])}];
  const t = ctx.findOne(n=>n.name==='Title'), s = ctx.findOne(n=>n.name==='Song');
  t.characters = data[i-1][0]; s.characters = data[i-1][1];
  ids.img.push(a.children.find(k=>k.name==='Img').id);
  ids.cover.push(ctx.findOne(n=>n.name==='Cover').id);
  ids.w.push([t.width, s.width]);   // 須 ≤170（依你的框寬調整）
}
return {page:page.id, frame:c.id, ids};
```
- 換圖：`upload_assets(count=8, nodeIds=[img1,cover1,img2,cover2,…], scaleMode='FILL', currentPageId=<新 page id>)`
  → 逐一 `curl -F "file=@{n}_photo.jpg;type=image/jpeg" <submitUrl>`（順序＝nodeIds 順序）

**配色**
- 參考：本機 `$REFERENCE_DIR`（程式取樣、不耗 Figma 額度；沒設就跳過）
- 外底色依當季主題；4 個資訊塊色互不相同、依外底色搭配、避開封面主色相
- 寫入前 `python3 scripts/palette_check.py check <底> <塊1..4>` 驗（退出碼 1＝有重複色）
- 只做**一組**，直接套在上面的 `bg`／`blocks`（使用者會自己手調）

換圖完成後截圖一次（`get_screenshot` 新框）。

### ④ 停點：等使用者點頭
回覆使用者（提示語照抄）：

> **製作完畢，請確認配色資訊無誤，可存打OK**

並附上：新 page 名、外底色與 4 個資訊塊色值表、截圖。
- 使用者回 OK 之前**不輸出、不存檔**
- 使用者在 Figma 手調後回 OK → 用 `use_figma` 回讀定稿框的外底色與 4 個色值（以回讀為準）

### ⑤ 輸出交付
- `use_figma`：clone 定稿框 → `rescale(4)` → 名稱前綴 `_tmp_export_`，回傳 id
- `get_screenshot(nodeId=<tmp>, maxDimension=<長邊像素>, contentsOnly=true)` → 立刻 curl 下載
- `sips -s format jpeg -s formatOptions 100 x.png --out $W/輸出/{file_stem}@4x.jpg`；`sips -g pixelWidth -g pixelHeight` 驗尺寸
- `use_figma` 刪 `_tmp_export_` clone
- `mkdir $DELIVERY_DIR/{批次}`（**已存在就停下問**，不覆蓋）→ cp → `shasum` 比對
- `$REFERENCE_DIR` 有設定 → 參考庫加一張：`sips -Z 1190 <交付檔> --out $REFERENCE_DIR/{file_stem}.jpg`（已存在就跳過）
- 回報交付絕對路徑；`USE_NOTION=true` 才提醒使用者上傳素材並貼回 Notion

## 完成標準
- 4 組順序、文字逐字對信；照片／封面對應正確；臉沒被切
- 4 個資訊塊底色互不相同，外底色符合當季主題且經使用者拍板
- 交付夾只有 1 張 `@4x.jpg`
- Figma 無 `_tmp_export_` 殘留

## 卡關規則
同一步驟卡兩次就停下回報，附失敗原文，不要硬試第三次。
