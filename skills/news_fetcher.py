"""
skills/news_fetcher.py

職責：抓取國際新聞候選清單。
資料源：公開 RSS（Reuters、NPR World 等），不需 API 金鑰。
排序/摘要邏輯依 rules/CONTENT_RULES.md 的權重規則，由呼叫端（main.py 或接上 LLM）處理——
這個模組只負責「抓原始候選新聞」，不做摘要或判斷，保持單一職責。
"""

from dataclasses import dataclass

# 可依需求增減來源；全部是公開 RSS，不需授權
RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/worldNews",
    "https://feeds.npr.org/1004/rss.xml",  # NPR World
    "https://www.taipeitimes.com/xml/rss.xml",
]


@dataclass
class NewsCandidate:
    title: str
    summary: str
    link: str
    source: str


def fetch_candidates(max_per_feed: int = 8) -> list[NewsCandidate]:
    """抓取所有 RSS 來源的最新條目，回傳原始候選清單（未排序、未篩選）。"""
    import feedparser

    candidates = []
    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            source_name = parsed.feed.get("title", feed_url)
            for entry in parsed.entries[:max_per_feed]:
                candidates.append(NewsCandidate(
                    title=entry.get("title", ""),
                    summary=entry.get("summary", ""),
                    link=entry.get("link", ""),
                    source=source_name,
                ))
        except Exception as e:
            print(f"[news_fetcher] 抓取 {feed_url} 失敗，略過：{e}")
            continue

    print(f"[news_fetcher] 共抓到 {len(candidates)} 則候選新聞")
    return candidates


# 備註：
# 這裡只做「抓取」，不做「依權重排序成 5 則 + 寫摘要」——那一步需要語意理解，
# 建議接上 LLM（例如呼叫 Claude API）處理 candidates，套用
# rules/CONTENT_RULES.md 的權重規則產出最終 5 則。
# main.py 裡有預留這段串接的位置與範例 prompt。
