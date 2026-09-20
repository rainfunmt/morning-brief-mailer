# 台北九點晨報自動寄送（Morning Brief Mailer）

每天台北時間 09:00（週一~週六）自動整理國際新聞、市場數據，寄送個人化晨報 email 給名單上的每一位收件人。

## 這是什麼

一開始這是用 Claude 的自然語言排程做出來的原型（連結 Gmail / Google Sheets connector）。
這個 repo 是同一套邏輯改寫成的真正程式碼版本——可以獨立執行、可以放上 GitHub、
別人（或未來的你）可以直接看懂邏輯、重新部署。

## 架構

```
morning-brief-mailer/
├── rules/                    ← 固定格式規則（改規則不用改程式碼）
│   ├── CONTENT_RULES.md      ← 新聞權重、欄位結構、語氣規則
│   └── SECURITY_RULES.md     ← 資安規則（密鑰管理、最小權限、審查檢查點）
├── skills/                   ← 各自獨立、單一職責的模組
│   ├── sheet_reader.py       ← 讀 Google Sheet 收件人名單
│   ├── market_data.py        ← 抓黃金/台股/美債/道瓊數據（yfinance，免費）
│   ├── news_fetcher.py       ← 抓 RSS 新聞候選（免費，不需金鑰）
│   ├── news_curator.py       ← 依規則篩選+摘要成 5 則（呼叫 Claude API，可選）
│   ├── email_renderer.py     ← 套模板 + 外觀設定，組出 HTML/純文字信件
│   └── mailer.py             ← 透過 Gmail API 逐一寄送
├── templates/                ← Jinja2 信件模板（HTML + 純文字版）
├── config/
│   └── theme.example.yaml    ← 外觀設定範例（顏色/字體，複製成 theme.yaml 調整）
├── .github/workflows/
│   └── morning-brief.yml     ← GitHub Actions 排程（cron，用 repo secrets）
├── tests/                    ← 單元測試
├── main.py                   ← 主流程，整合以上所有模組
├── requirements.txt
├── .env.example               ← 環境變數範例（本機開發用）
└── .gitignore                 ← 排除所有機密檔案
```

## 快速開始（本機測試）

```bash
git clone <your-repo-url>
cd morning-brief-mailer
pip install -r requirements.txt

cp .env.example .env
# 編輯 .env，填入你自己的 Google/Gmail/Anthropic 憑證（見下方「憑證申請」）

cp config/theme.example.yaml config/theme.yaml
# 依喜好調整顏色、字體（非必要，有預設值）

python main.py
```

## 憑證申請（一次性設定）

### Google Sheets（讀收件人名單）
1. [Google Cloud Console](https://console.cloud.google.com/) 建立專案 → 啟用 **Google Sheets API**
2. 建立 **Service Account**，下載 JSON 金鑰
3. 把 Google Sheet 分享給 Service Account 的 email（**檢視者**權限即可，不要給編輯權限）
4. 把整份 JSON 內容貼進 `.env` 的 `GOOGLE_SERVICE_ACCOUNT_JSON`

### Gmail（寄信）
1. 同一個 Google Cloud 專案，啟用 **Gmail API**
2. 設定 OAuth 同意畫面，建立 OAuth Client ID（類型：Desktop app）
3. 用 OAuth Playground 或本機腳本跑一次授權流程，取得 `refresh_token`
4. scope 只勾 `https://www.googleapis.com/auth/gmail.send`（不要多要權限）

### Anthropic API（選用，讓新聞篩選品質更好）
1. [console.anthropic.com](https://console.anthropic.com/) 申請 API key
2. 不設定的話，程式會自動降級成陽春版新聞篩選（品質較低但仍可執行）

## 外觀客製化

改 `config/theme.yaml`，不用碰任何程式碼：

```yaml
colors:
  accent: "#2f6f6b"   # 改成你的品牌色
fonts:
  heading: "..."       # 改字體
branding:
  title: "台北九點晨報"  # 改標題文字
```

## 排程部署（GitHub Actions，免費）

1. Push 這個 repo 到你的 GitHub
2. Repo → **Settings → Secrets and variables → Actions** → 新增以下 secrets：
   - `GOOGLE_SERVICE_ACCOUNT_JSON`
   - `GOOGLE_SHEET_ID`
   - `GMAIL_CLIENT_ID`
   - `GMAIL_CLIENT_SECRET`
   - `GMAIL_REFRESH_TOKEN`
   - `GMAIL_SENDER_EMAIL`
   - `ANTHROPIC_API_KEY`（選用）
3. `.github/workflows/morning-brief.yml` 已經設定好週一~週六台北 09:00 自動執行
4. 想先測試：repo → **Actions** 頁籤 → 選這個 workflow → **Run workflow** 手動觸發一次

## 資安（必要條件）

完整規則見 [`rules/SECURITY_RULES.md`](rules/SECURITY_RULES.md)，重點：

- ✅ 所有金鑰只存在環境變數 / GitHub Secrets，不寫死在程式碼、不進 git
- ✅ `.env`、憑證檔案全部在 `.gitignore` 排除清單
- ✅ Google Sheets 只給「檢視者」權限，Gmail OAuth scope 只開「寄信」
- ✅ 收件人 email 不會出現在 log 中（自動遮罩成 `r***@gmail.com` 格式）
- ✅ 逐一寄送，收件人之間互相看不到彼此的 email
- ⚠️ commit 前建議跑一次：
  ```bash
  git diff --cached | grep -iE "(api[_-]?key|secret|password|token|AIza|ya29\.)"
  ```
  有任何符合就代表可能誤把金鑰寫進程式碼，停止 commit 並檢查。

## 測試

```bash
python -m unittest tests/test_email_renderer.py -v
```

## 授權

自由使用、修改、學習。
