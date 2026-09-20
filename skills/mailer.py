"""
skills/mailer.py

職責：透過 Gmail API 逐一寄送信件。
資安：OAuth scope 只開 gmail.send（見 rules/SECURITY_RULES.md 第 2 條），
      憑證全部來自環境變數，絕不寫死在程式碼中。
"""

import base64
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _get_gmail_service():
    client_id = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError(
            "缺少 Gmail OAuth 相關環境變數，請參考 .env.example 設定"
        )

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=creds)


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def send_one(to_email: str, subject: str, html_body: str, text_body: str) -> str:
    """寄出單一一封信，回傳 message id。逐一呼叫，不群發（見 CONTENT_RULES.md 第 5 條）。"""
    service = _get_gmail_service()

    message = MIMEMultipart("alternative")
    message["to"] = to_email
    message["subject"] = subject
    message.attach(MIMEText(text_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()

    print(f"[mailer] 已寄送給 {_mask_email(to_email)}，message id: {result['id']}")
    return result["id"]


def send_to_all(recipients_with_content: list[dict], delay_seconds: float = 1.0) -> list[str]:
    """
    recipients_with_content: [{"to": email, "subject": str, "html": str, "text": str}, ...]
    逐一寄送並回傳所有 message id。delay_seconds 避免短時間內大量呼叫觸發 API 限流。
    """
    message_ids = []
    for item in recipients_with_content:
        msg_id = send_one(item["to"], item["subject"], item["html"], item["text"])
        message_ids.append(msg_id)
        time.sleep(delay_seconds)
    return message_ids
