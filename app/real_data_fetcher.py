#!/usr/bin/env python3
"""
真实数据采集模块 - 油价 + 新闻
从汽车之家、百度、东方财富等抓取真实数据
"""
import re
import os
import json
import sqlite3
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "/app/data/oil_prices.db")

GUANGXI_REGIONS = [
    "南宁", "柳州", "桂林", "梧州", "北海", "防城港",
    "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# ============================================================
# 油价采集
# ============================================================

def fetch_oil_prices_autohome() -> Optional[Dict[str, float]]:
    """从汽车之家抓取广西真实油价"""
    try:
        r = requests.get("https://www.autohome.com.cn/oil/450000.html", headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        html = r.text
        m92 = re.search(r'92.{0,15}汽油.{0,10}(\d+\.\d+)', html)
        m95 = re.search(r'95.{0,15}汽油.{0,10}(\d+\.\d+)', html)
        m0  = re.search(r'0.{0,15}柴油.{0,10}(\d+\.\d+)', html)
        if m92 and m95 and m0:
            return {
                "gasoline_92": float(m92.group(1)),
                "gasoline_95": float(m95.group(1)),
                "diesel_0": float(m0.group(1)),
            }
    except Exception as e:
        logger.error(f"汽车之家抓取失败: {e}")
    return None

def fetch_oil_prices_history() -> List[Dict[str, Any]]:
    """从汽车之家抓取广西历史油价走势"""
    history = []
    try:
        r = requests.get("https://www.autohome.com.cn/oil/450000.html", headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return history
        html = r.text
        # 提取走势表: 日期 92# 95# 98# 0#
        # 格式类似: 03-268.629.3110.598.31
        pattern = r'(\d{2}-\d{2})(\d+\.?\d*)(\d+\.?\d*)(\d+\.?\d*)(\d+\.?\d*)'
        for m in re.finditer(pattern, html):
            day_str = m.group(1)
            g92 = float(m.group(2))
            g95 = float(m.group(3))
            g0 = float(m.group(5))
            # 判断年份
            month = int(day_str.split('-')[0])
            year = 2026 if month >= 3 else 2025 if month <= 2 else 2026
            full_date = f"{year}-{day_str}"
            history.append({
                "date": full_date,
                "gasoline_92": g92,
                "gasoline_95": g95,
                "diesel_0": g0,
                "source": "汽车之家(历史)"
            })
    except Exception as e:
        logger.error(f"历史油价抓取失败: {e}")
    return history

def save_oil_prices(prices: Dict[str, float], source: str = "汽车之家"):
    """保存油价到数据库"""
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS oil_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL, date TEXT NOT NULL,
            gasoline_92 REAL NOT NULL, gasoline_95 REAL NOT NULL, diesel_0 REAL NOT NULL,
            source TEXT NOT NULL DEFAULT '汽车之家',
            collected_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            UNIQUE(region, date)
        )
    """)
    for region in GUANGXI_REGIONS:
        conn.execute(
            "INSERT OR REPLACE INTO oil_prices (region, date, gasoline_92, gasoline_95, diesel_0, source) VALUES (?,?,?,?,?,?)",
            (region, today, prices["gasoline_92"], prices["gasoline_95"], prices["diesel_0"], source)
        )
    conn.commit()
    conn.close()

def save_oil_history(history: List[Dict[str, Any]]):
    """保存历史油价到数据库"""
    conn = sqlite3.connect(DB_PATH)
    for h in history:
        for region in GUANGXI_REGIONS:
            conn.execute(
                "INSERT OR IGNORE INTO oil_prices (region, date, gasoline_92, gasoline_95, diesel_0, source) VALUES (?,?,?,?,?,?)",
                (region, h["date"], h["gasoline_92"], h["gasoline_95"], h["diesel_0"], h["source"])
            )
    conn.commit()
    conn.close()

# ============================================================
# 新闻采集（真实数据）
# ============================================================

def fetch_news_baidu(keyword: str = "油价", max_items: int = 8) -> List[Dict[str, Any]]:
    """从百度新闻搜索抓取真实新闻"""
    news = []
    try:
        url = f"https://www.baidu.com/s?wd={keyword}&tn=news&rtt=1&bsst=1&cl=2&medium=0"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return news
        html = r.text
        
        # 提取新闻标题和链接
        # 百度新闻格式: <h3 class="news-title-font_1xS-F"><a href="..." target="_blank">标题</a></h3>
        items = re.findall(r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
        
        for link, title in items[:max_items]:
            title = re.sub(r'<[^>]+>', '', title).strip()
            if len(title) > 5:
                news.append({
                    "title": title,
                    "url": link,
                    "source": "百度新闻",
                    "category": "财经",
                    "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "relevance_score": 0.8,
                })
    except Exception as e:
        logger.error(f"百度新闻抓取失败: {e}")
    return news

def fetch_news_eastmoney(keyword: str = "油价", max_items: int = 8) -> List[Dict[str, Any]]:
    """从东方财富抓取真实新闻"""
    news = []
    try:
        url = f"https://so.eastmoney.com/news/s?keyword={keyword}&pageindex=1&searchrange=8&channelid=0"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return news
        html = r.text
        
        # 提取新闻
        items = re.findall(r'<div class="news-item".*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?<span class="news-time">(.*?)</span>', html, re.DOTALL)
        
        for link, title, pub_time in items[:max_items]:
            title = re.sub(r'<[^>]+>', '', title).strip()
            if len(title) > 8 and any(kw in title for kw in ["油", "能源", "汽油", "柴油", "原油"]):
                if not link.startswith('http'):
                    link = "https:" + link if link.startswith('//') else "https://www.eastmoney.com" + link
                news.append({
                    "title": title,
                    "url": link,
                    "source": "东方财富",
                    "category": "财经",
                    "published_at": pub_time.strip() or datetime.now().strftime("%Y-%m-%d"),
                    "relevance_score": 0.85,
                })
    except Exception as e:
        logger.error(f"东方财富新闻抓取失败: {e}")
    return news

def fetch_news_163(keyword: str = "油价", max_items: int = 5) -> List[Dict[str, Any]]:
    """从网易新闻抓取"""
    news = []
    try:
        url = f"https://news.163.com/search?keyword={keyword}"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return news
        html = r.text
        
        items = re.findall(r'<a[^>]*href="(https?://[^"]*news[^"]*)"[^>]*title="([^"]*)"', html)
        seen = set()
        for link, title in items[:max_items * 2]:
            title = title.strip()
            if title not in seen and len(title) > 8 and any(kw in title for kw in ["油", "能源", "汽油", "柴油"]):
                seen.add(title)
                news.append({
                    "title": title,
                    "url": link,
                    "source": "网易",
                    "category": "财经",
                    "published_at": datetime.now().strftime("%Y-%m-%d"),
                    "relevance_score": 0.75,
                })
                if len(news) >= max_items:
                    break
    except Exception as e:
        logger.error(f"网易新闻抓取失败: {e}")
    return news

def fetch_news_sina(keyword: str = "油价", max_items: int = 5) -> List[Dict[str, Any]]:
    """从新浪财经抓取"""
    news = []
    try:
        url = f"https://search.sina.com.cn/news?q={keyword}&c=news&sort=time"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return news
        html = r.text
        
        items = re.findall(r'<h2><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h2>', html, re.DOTALL)
        for link, title in items[:max_items]:
            title = re.sub(r'<[^>]+>', '', title).strip()
            if len(title) > 8:
                news.append({
                    "title": title,
                    "url": link,
                    "source": "新浪财经",
                    "category": "财经",
                    "published_at": datetime.now().strftime("%Y-%m-%d"),
                    "relevance_score": 0.8,
                })
    except Exception as e:
        logger.error(f"新浪新闻抓取失败: {e}")
    return news

def fetch_all_news() -> List[Dict[str, Any]]:
    """从多个源抓取新闻，去重合并"""
    all_news = []
    
    # 并行抓取多个源
    sources = [
        ("百度", lambda: fetch_news_baidu("油价 广西")),
        ("百度2", lambda: fetch_news_baidu("今日油价调整")),
        ("东方财富", lambda: fetch_news_eastmoney("油价")),
        ("网易", lambda: fetch_news_163("油价")),
        ("新浪", lambda: fetch_news_sina("油价")),
    ]
    
    for name, func in sources:
        try:
            articles = func()
            logger.info(f"✅ {name}: {len(articles)}条新闻")
            all_news.extend(articles)
        except Exception as e:
            logger.error(f"❌ {name}: {e}")
    
    # 去重
    seen_titles = set()
    unique_news = []
    for n in all_news:
        t = n["title"]
        if t not in seen_titles and len(t) > 8:
            seen_titles.add(t)
            unique_news.append(n)
    
    # 按相关性排序
    unique_news.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return unique_news[:15]

def save_news(articles: List[Dict[str, Any]]):
    """保存新闻到数据库"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, summary TEXT, url TEXT,
            source TEXT NOT NULL, category TEXT DEFAULT '新闻',
            published_at TEXT NOT NULL, relevance_score REAL DEFAULT 0.5,
            collected_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            UNIQUE(title, source)
        )
    """)
    for a in articles:
        conn.execute(
            "INSERT OR IGNORE INTO news_articles (title, summary, url, source, category, published_at, relevance_score) VALUES (?,?,?,?,?,?,?)",
            (a["title"], a.get("title", "")[:200], a.get("url", ""), a["source"], a.get("category", "新闻"), a["published_at"], a.get("relevance_score", 0.5))
        )
    conn.commit()
    conn.close()

# ============================================================
# 主采集函数
# ============================================================

def collect_all():
    """采集所有真实数据"""
    logger.info("🔄 开始采集真实数据...")
    
    # 1. 油价
    prices = fetch_oil_prices_autohome()
    if prices:
        save_oil_prices(prices, "汽车之家(实时)")
        logger.info(f"✅ 油价: 92号={prices['gasoline_92']}  95号={prices['gasoline_95']}  柴油={prices['diesel_0']}")
    else:
        logger.warning("⚠️ 油价抓取失败，使用已有数据")
    
    # 2. 历史油价
    history = fetch_oil_prices_history()
    if history:
        save_oil_history(history)
        logger.info(f"✅ 历史油价: {len(history)}条记录")
    
    # 3. 新闻
    news = fetch_all_news()
    if news:
        save_news(news)
        logger.info(f"✅ 新闻: {len(news)}条")
    else:
        logger.warning("⚠️ 新闻抓取失败")
    
    return {
        "oil_prices": prices,
        "history_count": len(history),
        "news_count": len(news),
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    result = collect_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
