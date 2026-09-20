"""
skills/sheet_reader.py

職責：從 Google Sheet 讀取最新的收件人名單。
資安：Service Account 憑證只用「檢視者」權限，見 rules/SECURITY_RULES.md 第 2 條。
"""

import json
import os
from dataclasses import dataclass

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


@dataclass
class Recipient:
    name: str
    email: str


def _mask_email(email: str) -> str:
    """log 用的遮罩版本，避免把完整 email 印進任何輸出（SECURITY_RULES.md 第 3 條）。"""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def get_recipients() -> list[Recipient]:
    """
    讀取環境變數指定的 Google Sheet，回傳收件人清單。
    每次呼叫都即時讀取，不快取——名單新增/刪除會立即反映。
    """
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")

    if not sa_json or not sheet_id:
        raise RuntimeError(
            "缺少 GOOGLE_SERVICE_ACCOUNT_JSON 或 GOOGLE_SHEET_ID 環境變數，"
            "請參考 .env.example 設定"
        )

    import gspread
    from google.oauth2.service_account import Credentials

    creds_dict = json.loads(sa_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_id).sheet1
    rows = sheet.get_all_records()  # 第一列當作 header：cust_id, name, email, note

    recipients = []
    for row in rows:
        name = str(row.get("name", "")).strip()
        email = str(row.get("email", "")).strip()
        if name and email and "@" in email:
            recipients.append(Recipient(name=name, email=email))

    print(f"[sheet_reader] 讀到 {len(recipients)} 位收件人：{[_mask_email(r.email) for r in recipients]}")
    return recipients
