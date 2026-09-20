"""
skills/news_curator.py

職責：把 news_fetcher 抓到的原始候選新聞，依 rules/CONTENT_RULES.md 的權重規則，
篩選+摘要成最終 5 則。這一步需要語意判斷，所以呼叫 Claude API。

資安：ANTHROPIC_API_KEY 一樣走環境變數，不寫死。
若沒有設定金鑰，退回「取前 5 則、標題當摘要」的陽春版本，讓整個流程仍可執行，
但品質會比較低（可能保留英文原文）——這是刻意的降級（degrade gracefully），不是靜默失敗。
"""

import os
from pathlib import Path

from .news_fetcher import NewsCandidate
from .email_renderer import NewsItem

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "CONTENT_RULES.md"


def _fallback_curate(candidates: list[NewsCandidate], limit: int = 5) -> list[NewsItem]:
    return [
        NewsItem(title=c.title, summary=c.summary[:200] or "（無摘要，請參考原始連結）")
        for c in candidates[:limit]
    ]


def curate_top5(candidates: list[NewsCandidate]) -> list[NewsItem]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[news_curator] 未設定 ANTHROPIC_API_KEY，使用陽春版篩選（取前5則）")
        return _fallback_curate(candidates)

    try:
        import anthropic

        rules_text = RULES_PATH.read_text(encoding="utf-8")
        candidates_text = "\n\n".join(
            f"標題：{c.title}\n摘要：{c.summary}\n來源：{c.source}"
            for c in candidates
        )

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": (
                    f"依照以下格式規則，從候選新聞中選出並重寫 5 則國際要聞：\n\n"
                    f"{rules_text}\n\n"
                    f"候選新聞（可能包含英文或其他語言的原文）：\n{candidates_text}\n\n"
                    f"重要規則：\n"
                    f"1. 不論候選新聞的原始語言是什麼，標題和摘要都必須是**繁體中文**，"
                    f"不可保留任何英文原文標題或直接翻譯腔——用你自己的話重新摘要成自然的繁體中文財經新聞寫法\n"
                    f"2. 專有名詞（人名、地名、機構名）維持通用的繁體中文譯名（例如：川普、俄羅斯、白宮）\n\n"
                    f"請用以下格式輸出，每則之間用 ---分隔：\n"
                    f"標題：<粗體標題內容，繁體中文，不含**符號>\n摘要：<2-4句摘要，繁體中文>"
                ),
            }],
        )
        raw = response.content[0].text
        items = []
        for block in raw.split("---"):
            title_line = [l for l in block.splitlines() if l.strip().startswith("標題：")]
            summary_line = [l for l in block.splitlines() if l.strip().startswith("摘要：")]
            if title_line and summary_line:
                items.append(NewsItem(
                    title=title_line[0].split("：", 1)[1].strip(),
                    summary=summary_line[0].split("：", 1)[1].strip(),
                ))
        if items:
            return items[:5]
        print("[news_curator] LLM 回應解析失敗，改用陽春版")
        return _fallback_curate(candidates)

    except Exception as e:
        print(f"[news_curator] 呼叫 Claude API 失敗（{e}），改用陽春版")
        return _fallback_curate(candidates)