# claude-packer-a4

A4 宣傳物每季套版的 Claude Code skill：讀需求信 → Notion 開需求卡（選配）→ 下載素材 → Figma 套版換圖換字換色 → 輸出 4x JPG。

**觸發詞**：「做好丘A4」（可依自己習慣改成別的觸發詞）

## 這是去識別化的公開版

原始版本含公司內部真值（絕對路徑、Figma fileKey、Notion data_source_id、素材主機）。本版已全部改讀環境變數，**安裝後必須自行設定**，見 `SKILL.md` 開頭〈安裝〉段。

| 環境變數 | 意思 | 必填 |
|---|---|---|
| `DELIVERY_DIR` | 成品 JPG 的交付夾絕對路徑 | ✅ |
| `REFERENCE_DIR` | 配色參考圖資料夾絕對路徑 | 選填（沒有就跳過取樣） |
| `FIGMA_FILE_KEY` | 你的 Figma 檔 key | ✅ |
| `NOTION_DATA_SOURCE_ID` | Notion 需求資料庫的 data_source_id | `USE_NOTION=true` 才需要 |
| `SEAFILE_HOST` | 素材下載用的主機網域 | 選填（不設就用通用網域偵測） |
| `USE_NOTION` | 要不要開 Notion 需求卡 | ✅（`true`/`false`） |

## 你的 Figma 檔要長什麼樣

本 skill 假設你有一個「模版」page，內含一個 595×842 的模版 frame，四組藝人區塊（照片＋專輯封面＋藝人名＋作品）。詳見 `SKILL.md`〈你的 Figma 檔要有這個結構〉。

## 需要的 MCP

Figma（含 `use_figma`／`upload_assets`／`get_screenshot`）必要；Notion、Gmail 選配。

## 安裝

```bash
git clone <this repo> ~/.claude/skills/claude-packer-a4
```

再照 `SKILL.md` 開頭建立 `~/.config/claude-packer-a4/env`。

## scripts/ 內容

| 腳本 | 用途 |
|---|---|
| `parse_mail.py` | 信件純文字 → JSON（死線／季度／4 組藝人／素材連結 token 等） |
| `fetch_assets.sh` | 素材下載 → 依順序配對照片／封面 → 縮圖成上傳用檔案 |
| `crop_photo.py` | 藝人照裁成指定比例，指定垂直起點 |
| `palette_check.py` | 封面主色分析／候選色白字對比＋重複色檢查 |

## 授權

MIT
