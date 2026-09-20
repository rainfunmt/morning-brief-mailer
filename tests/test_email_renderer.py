"""
簡單的單元測試，確認 email_renderer 在沒有真實金鑰的情況下也能正確組出信件內容。
執行：python -m pytest tests/ 或 python -m unittest tests/test_email_renderer.py
"""

import unittest

from skills.email_renderer import render_email, build_subject, NewsItem
from skills.market_data import MarketRow


class TestEmailRenderer(unittest.TestCase):
    def test_render_email_contains_recipient_name(self):
        html, text = render_email(
            recipient_name="測試用戶",
            date_display="2026 年 9 月 20 日（週日）",
            thesis="這是測試用的今日一句。",
            news_items=[NewsItem(title="測試新聞標題", summary="測試新聞摘要內容。")],
            market_rows=[MarketRow(label="現貨黃金 XAU/USD", value="4,378.23（+0.84%）", positive=True)],
            market_data_asof="2026/09/18 收盤",
        )
        self.assertIn("測試用戶 您好", html)
        self.assertIn("測試用戶 您好", text)
        self.assertIn("測試新聞標題", html)
        self.assertIn("<strong", html)  # 標題必須是粗體（CONTENT_RULES.md 第 4 條）

    def test_build_subject_format(self):
        subject = build_subject("2026/09/20")
        self.assertEqual(subject, "台北九點晨報｜2026/09/20")


if __name__ == "__main__":
    unittest.main()
