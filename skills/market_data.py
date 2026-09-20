"""
skills/market_data.py

職責：抓取黃金現貨、台股加權指數、美 10 年期公債殖利率、道瓊指數。
資料源：yfinance（免費、公開，不需 API 金鑰）。
"""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

TICKERS = {
    "gold": "GC=F",       # 黃金期貨（近似現貨價）
    "taiex": "^TWII",     # 台股加權指數
    "us10y": "^TNX",      # 美 10 年期公債殖利率 (需 /10 還原成 %)
    "dow": "^DJI",        # 道瓊工業指數
}


@dataclass
class MarketRow:
    label: str
    value: str
    positive: bool | None  # True=漲 False=跌 None=無方向（如殖利率絕對值）


def _fmt_num(n: float, decimals: int = 2) -> str:
    return f"{n:,.{decimals}f}"


def _fetch_last_two_closes(ticker: str) -> tuple[float, float, str]:
    """回傳 (最新收盤, 前一日收盤, 資料日期字串)。yfinance 延遲載入，讓本模組在離線環境下也能被 import 與測試。"""
    import yfinance as yf

    hist = yf.Ticker(ticker).history(period="5d")
    if hist.empty or len(hist) < 2:
        raise RuntimeError(f"[market_data] 抓不到 {ticker} 的歷史資料")
    last = hist.iloc[-1]
    prev = hist.iloc[-2]
    asof = hist.index[-1].strftime("%Y/%m/%d")
    return float(last["Close"]), float(prev["Close"]), asof


def get_market_snapshot() -> tuple[list[MarketRow], str]:
    """
    回傳 (市場數據列表, 資料時間說明字串)。
    若當下是台北時間週末，附註休市與實際資料日期。
    """
    rows = []
    asof_dates = []

    # 黃金
    gold_now, gold_prev, gold_asof = _fetch_last_two_closes(TICKERS["gold"])
    gold_chg_pct = (gold_now - gold_prev) / gold_prev * 100
    rows.append(MarketRow(
        label="現貨黃金 XAU/USD",
        value=f"{_fmt_num(gold_now)}（{gold_chg_pct:+.2f}%）",
        positive=gold_chg_pct >= 0,
    ))
    asof_dates.append(gold_asof)

    # 台股
    taiex_now, taiex_prev, taiex_asof = _fetch_last_two_closes(TICKERS["taiex"])
    taiex_chg_pct = (taiex_now - taiex_prev) / taiex_prev * 100
    rows.append(MarketRow(
        label="台股加權指數",
        value=f"{_fmt_num(taiex_now)}（{taiex_chg_pct:+.2f}%）",
        positive=taiex_chg_pct >= 0,
    ))
    asof_dates.append(taiex_asof)

    # 美債殖利率（^TNX 是 x10 表示法）
    us10y_now, us10y_prev, us10y_asof = _fetch_last_two_closes(TICKERS["us10y"])
    rows.append(MarketRow(
        label="美 10 年期公債殖利率",
        value=f"{us10y_now / 10:.2f}%",
        positive=None,
    ))
    asof_dates.append(us10y_asof)

    # 道瓊
    dow_now, dow_prev, dow_asof = _fetch_last_two_closes(TICKERS["dow"])
    dow_chg_pct = (dow_now - dow_prev) / dow_prev * 100
    rows.append(MarketRow(
        label="道瓊工業指數",
        value=f"{_fmt_num(dow_now)}（{dow_chg_pct:+.2f}%）",
        positive=dow_chg_pct >= 0,
    ))
    asof_dates.append(dow_asof)

    latest_asof = max(asof_dates)
    tz = ZoneInfo("Asia/Taipei")
    today = datetime.now(tz)
    is_weekend = today.weekday() >= 5  # 5=Sat, 6=Sun

    if is_weekend or latest_asof != today.strftime("%Y/%m/%d"):
        asof_note = f"休市，數據為最近一個交易日收盤（{latest_asof}）"
    else:
        asof_note = f"{latest_asof} 收盤"

    return rows, asof_note
