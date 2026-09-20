# 資安規則

這份文件是強制規則，`skills/` 底下任何模組都必須遵守。

## 1. 密鑰管理

- 所有金鑰、憑證、token 一律透過環境變數讀取（`os.environ`），**禁止**寫死在程式碼裡
- 本機開發用 `.env`（已在 `.gitignore`，不會進 git）
- 正式排程（GitHub Actions）用 repo 的 **Settings → Secrets and variables → Actions** 設定，
  不會出現在程式碼、log 或 Actions 執行紀錄中
- `.env.example` 只放「欄位名稱」示範，不可放真實金鑰

## 2. 最小權限原則

- **Google Sheets**：Service Account 權限設為「檢視者」（Viewer），不給編輯權限
- **Gmail**：OAuth scope 只開 `gmail.send`，不要求讀信、刪信、修改信件的權限
- 兩個服務都用獨立的憑證，不共用同一組帳密

## 3. 收件人資料保護

- Email 名單只在記憶體中處理，執行完畢即釋放，不寫入任何 log 檔案
- 禁止把收件人 email 印在 print()/log 訊息中（debug 時可印遮罩版本，如 `r***@gmail.com`）
- 逐一寄送（見 CONTENT_RULES.md 第 5 條），避免收件人互看彼此 email

## 4. 程式碼審查檢查點

commit 前檢查（建議設定 pre-commit hook 或至少手動過一次）：

```bash
git diff --cached | grep -iE "(api[_-]?key|secret|password|token|AIza|ya29\.)" 
```

如果有任何符合，代表可能不小心把金鑰寫進程式碼，**停止 commit**。

## 5. GitHub Actions 排程的資安注意事項

- Secrets 只在 workflow 執行當下注入環境變數，執行完畢即銷毀
- 不要在 workflow yaml 中用 `echo $SECRET` 等方式印出秘密值（GitHub 會自動遮罩，但仍應避免）
- Repo 若為 public，任何人都能看到程式碼邏輯（這是刻意的，作品集目的），
  但看不到任何一組真實金鑰——這正是本專案架構要保證的事

## 6. 依賴套件

- `requirements.txt` 鎖定版本號，避免上游套件被劫持後自動引入惡意程式碼
- 定期用 `pip list --outdated` 檢查更新，抓安全性修補
