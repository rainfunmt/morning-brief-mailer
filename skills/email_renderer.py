"""
skills/email_renderer.py

職責：把內容套進 templates/，依 config/theme.yaml 套用外觀設定，
輸出 (html, plain_text)。格式規則見 rules/CONTENT_RULES.md。
"""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
THEME_PATH = BASE_DIR / "config" / "theme.yaml"
THEME_EXAMPLE_PATH = BASE_DIR / "config" / "theme.example.yaml"


@dataclass
class NewsItem:
    title: str
    summary: str


def _load_theme() -> dict:
    path = THEME_PATH if THEME_PATH.exists() else THEME_EXAMPLE_PATH
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def render_email(
    recipient_name: str,
    date_display: str,
    thesis: str,
    news_items: list[NewsItem],
    market_rows: list,  # list[MarketRow] from market_data.py
    market_data_asof: str,
    market_closed_note: str | None = None,
) -> tuple[str, str]:
    """回傳 (html_body, plain_text_body)"""
    theme = _load_theme()
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    context = {
        "theme": theme,
        "recipient_name": recipient_name,
        "date_display": date_display,
        "thesis": thesis,
        "news_items": news_items,
        "market_rows": market_rows,
        "market_data_asof": market_data_asof,
        "market_closed_note": market_closed_note,
    }

    html = env.get_template("email.html.j2").render(**context)
    text = env.get_template("email.txt.j2").render(**context)
    return html, text


def build_subject(date_display_short: str) -> str:
    """依 rules/CONTENT_RULES.md 第 1 條格式：台北九點晨報｜YYYY/MM/DD"""
    return f"台北九點晨報｜{date_display_short}"
