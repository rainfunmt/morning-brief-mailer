"""
main.py

台北九點晨報 — 主流程。整合 skills/ 底下所有模組，依 rules/ 的規則產生並寄送晨報。

執行方式：
    python main.py

環境變數：見 .env.example（本機用 .env，正式排程用 GitHub Actions Secrets）
"""

import os
import sys
from datetime import datetime

from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from skills.sheet_reader import get_recipients
from skills.market_data import get_market_snapshot
from skills.news_fetcher import fetch_candidates
from skills.news_curator import curate_top5
from skills.email_renderer import render_email, build_subject
from skills.mailer import send_to_all

load_dotenv()  # 本機開發讀 .env；GitHub Actions 環境已經注入 secrets，這行無害


def main():
    tz = ZoneInfo(os.environ.get("TIMEZONE", "Asia/Taipei"))
    now = datetime.now(tz)
    WEEKDAY_ZH = ["一", "二", "三", "四", "五", "六", "日"]
    weekday_zh = WEEKDAY_ZH[now.weekday()]
    date_display = f"{now.year} 年 {now.month} 月 {now.day} 日（週{weekday_zh}）"
    date_display_short = now.strftime("%Y/%m/%d")

    print(f"[main] 開始產生晨報 — {date_display_short}")

    # 1. 讀收件人名單（每次即時讀取，見 rules/CONTENT_RULES.md 第 5 條）
    try:
        recipients = get_recipients()
    except Exception as e:
        print(f"[main] 讀取收件人名單失敗，中止：{e}")
        sys.exit(1)

    if not recipients:
        print("[main] 名單是空的，沒有人要寄，中止")
        sys.exit(0)

    # 2. 抓市場數據
    try:
        market_rows, market_asof = get_market_snapshot()
    except Exception as e:
        print(f"[main] 抓取市場數據失敗，中止：{e}")
        sys.exit(1)

    is_closed = "休市" in market_asof
    market_closed_note = market_asof if is_closed else None

    # 3. 抓新聞候選 + 篩選成 5 則
    try:
        candidates = fetch_candidates()
        news_items = curate_top5(candidates)
    except Exception as e:
        print(f"[main] 新聞處理失敗，中止：{e}")
        sys.exit(1)

    # 4. 今日一句（簡化版：串接第一則新聞 + 市場漲跌方向；正式使用建議接 LLM 生成更好的判讀）
    top_news_title = news_items[0].title if news_items else "今日市場持續變動"
    thesis = f"{top_news_title}，市場動向請參考以下要聞與數據。"

    # 5. 逐一產生個人化內容並寄送
    subject = build_subject(date_display_short)
    jobs = []
    for r in recipients:
        html, text = render_email(
            recipient_name=r.name,
            date_display=date_display,
            thesis=thesis,
            news_items=news_items,
            market_rows=market_rows,
            market_data_asof=market_asof,
            market_closed_note=market_closed_note,
        )
        jobs.append({"to": r.email, "subject": subject, "html": html, "text": text})

    try:
        message_ids = send_to_all(jobs)
        print(f"[main] 完成，共寄出 {len(message_ids)} 封信")
    except Exception as e:
        print(f"[main] 寄送失敗：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
