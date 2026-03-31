"""
广西油价监控分析系统 - 完整版
整合所有功能：油价收集、图表生成、新闻收集、AI分析、定时任务
"""
import os
import sys
import json
import sqlite3
import logging
import asyncio
import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config_simple import settings

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# 数据库层 - 同步SQLite
# ============================================================
# 数据库路径 - 优先使用环境变量，fallback到项目目录
DB_PATH = os.environ.get("DB_PATH", os.path.join("/app", "data", "oil_prices.db"))

def _ensure_db_dir():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        # 确保目录可写
        if not os.access(db_dir, os.W_OK):
            logger.warning(f"数据库目录不可写: {db_dir}")

def init_db():
    """初始化数据库表"""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS oil_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            date TEXT NOT NULL,
            gasoline_92 REAL NOT NULL,
            gasoline_95 REAL NOT NULL,
            diesel_0 REAL NOT NULL,
            source TEXT NOT NULL DEFAULT '模拟数据',
            collected_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            UNIQUE(region, date)
        );
        
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            source TEXT NOT NULL,
            category TEXT DEFAULT '新闻',
            published_at TEXT NOT NULL,
            relevance_score REAL DEFAULT 0.5,
            collected_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            UNIQUE(title, source)
        );
        
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_date TEXT NOT NULL,
            analysis_type TEXT NOT NULL DEFAULT 'daily',
            summary TEXT NOT NULL,
            trend_analysis TEXT,
            recommendation TEXT NOT NULL,
            confidence_score REAL DEFAULT 0.0,
            price_change_prediction REAL,
            raw_data TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_oil_prices_date ON oil_prices(date);
        CREATE INDEX IF NOT EXISTS idx_oil_prices_region ON oil_prices(region);
        CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_at);
        CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date);
    """)
    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")

@contextmanager
def get_db():
    """获取数据库连接"""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ============================================================
# 油价数据收集
# ============================================================
GUANGXI_REGIONS = settings.guangxi_regions

# 基础油价（模拟数据用）
# 基准油价（来自汽车之家2026-03-31真实数据，广西全区统一价）
BASE_PRICES = {
    "南宁": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "柳州": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "桂林": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "梧州": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "北海": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "防城港": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "钦州": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "贵港": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "玉林": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "百色": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "贺州": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "河池": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "来宾": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
    "崇左": {"gasoline_92": 8.62, "gasoline_95": 9.31, "diesel_0": 8.31},
}

def collect_oil_prices() -> List[Dict[str, Any]]:
    """从汽车之家抓取广西真实油价"""
    import requests
    import re
    
    today = date.today().isoformat()
    prices = []
    
    try:
        # 抓取汽车之家广西油价页面
        resp = requests.get(
            "https://www.autohome.com.cn/oil/450000.html",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html",
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
            timeout=15,
        )
        
        if resp.status_code == 200:
            text = resp.text
            # 提取价格数据
            # 格式: 92号汽油为X.XX元，95号汽油为X.XX元，0号柴油为X.XX元
            match_92 = re.search(r'92号汽油为(\d+\.?\d*)元', text)
            match_95 = re.search(r'95号汽油为(\d+\.?\d*)元', text)
            match_diesel = re.search(r'0号柴油为(\d+\.?\d*)元', text)
            
            if match_92 and match_95 and match_diesel:
                p92 = float(match_92.group(1))
                p95 = float(match_95.group(1))
                p0 = float(match_diesel.group(1))
                
                logger.info(f"✅ 从汽车之家获取到真实油价: 92号={p92}, 95号={p95}, 0号={p0}")
                
                # 广西全区统一价，各地区使用相同价格
                for region in GUANGXI_REGIONS:
                    prices.append({
                        "region": region,
                        "date": today,
                        "gasoline_92": p92,
                        "gasoline_95": p95,
                        "diesel_0": p0,
                        "source": "汽车之家(真实)",
                    })
                
                return prices
            else:
                logger.warning("无法解析油价数据，使用备用方案")
    except Exception as e:
        logger.error(f"抓取汽车之家失败: {e}，使用备用方案")
    
    # 备用方案: 使用基准数据+随机波动
    for region, base in BASE_PRICES.items():
        p92 = round(base["gasoline_92"] + random.uniform(-0.05, 0.05), 2)
        p95 = round(base["gasoline_95"] + random.uniform(-0.05, 0.05), 2)
        p0  = round(base["diesel_0"]   + random.uniform(-0.05, 0.05), 2)
        prices.append({
            "region": region, "date": today,
            "gasoline_92": p92, "gasoline_95": p95, "diesel_0": p0,
            "source": "备用数据",
        })
    return prices

def save_oil_prices(prices: List[Dict[str, Any]]):
    """保存油价到数据库"""
    with get_db() as conn:
        for p in prices:
            conn.execute("""
                INSERT OR REPLACE INTO oil_prices (region, date, gasoline_92, gasoline_95, diesel_0, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p["region"], p["date"], p["gasoline_92"], p["gasoline_95"], p["diesel_0"], p["source"]))

def seed_historical_data(days: int = 30):
    """生成历史数据用于图表展示"""
    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM oil_prices").fetchone()[0]
        if existing > 50:
            return  # 已有足够数据
    
    logger.info(f"生成最近{days}天历史数据...")
    today = date.today()
    
    for d in range(days, 0, -1):
        target_date = (today - timedelta(days=d)).isoformat()
        prices = []
        for region, base in BASE_PRICES.items():
            # 日期越近价格越高（模拟上涨趋势），加随机波动
            trend_factor = 1 + (days - d) * 0.001
            p92 = round(base["gasoline_92"] * trend_factor + random.uniform(-0.08, 0.08), 2)
            p95 = round(base["gasoline_95"] * trend_factor + random.uniform(-0.08, 0.08), 2)
            p0  = round(base["diesel_0"]   * trend_factor + random.uniform(-0.08, 0.08), 2)
            prices.append({
                "region": region, "date": target_date,
                "gasoline_92": p92, "gasoline_95": p95, "diesel_0": p0,
                "source": "历史数据",
            })
        save_oil_prices(prices)
    logger.info("历史数据生成完成")

# ============================================================
# 新闻收集（模拟 - 真实爬取需要处理反爬）
# ============================================================
NEWS_TEMPLATES = [
    {"title": "国际原油价格小幅波动，国内油价调整窗口即将开启", "summary": "受国际地缘政治及OPEC+减产影响，近期国际原油价格呈现震荡走势。下一轮国内成品油调价窗口将于下周开启，业内预计或将小幅上调。", "source": "财经日报", "category": "财经"},
    {"title": "广西加油站促销活动增多，车主可关注优惠信息", "summary": "随着市场竞争加剧，广西多地加油站推出会员日折扣、满减优惠等活动，部分站点92号汽油优惠幅度达0.3元/升。", "source": "本地资讯", "category": "生活"},
    {"title": "新能源汽车销量持续增长，对传统燃油需求产生影响", "summary": "据中汽协数据，本月新能源汽车渗透率再创新高，长期来看将对成品油消费结构产生深远影响。", "source": "汽车之家", "category": "汽车"},
    {"title": "发改委：密切关注国际油价变化，保障国内市场供应", "summary": "国家发改委表示，将继续完善成品油价格机制，确保国内成品油市场稳定供应，维护消费者利益。", "source": "新华网", "category": "政策"},
    {"title": "OPEC+维持减产协议，国际油价获支撑", "summary": "OPEC+最新会议决定维持现有减产规模不变，布伦特原油价格在80美元/桶附近获得支撑。", "source": "路透社", "category": "国际"},
    {"title": "广西高速公路服务区加油站完成升级改造", "summary": "全区28对高速公路服务区加油站完成智慧化改造，支持无感支付和新能源充电服务。", "source": "广西交通", "category": "基建"},
    {"title": "专家预测：下月油价或将迎来年内第三次上调", "summary": "多位能源分析师指出，在国际油价走强和人民币汇率波动的背景下，下月成品油零售价大概率上调。", "source": "能源观察", "category": "分析"},
    {"title": "广西多地开展成品油市场专项整治行动", "summary": "为维护市场秩序，南宁、柳州等地市场监管部门开展成品油质量抽检和价格巡查，打击违规经营行为。", "source": "广西日报", "category": "监管"},
]

def collect_news() -> List[Dict[str, Any]]:
    """收集新闻（模拟数据 + 尝试RSS）"""
    news = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 模拟新闻（保底）
    for i, template in enumerate(NEWS_TEMPLATES[:5]):
        news.append({
            "title": template["title"],
            "summary": template["summary"],
            "url": f"https://example.com/news/{today}/{i+1}",
            "source": template["source"],
            "category": template["category"],
            "published_at": f"{today} {random.randint(6,22):02d}:{random.randint(0,59):02d}",
            "relevance_score": round(random.uniform(0.6, 0.95), 2),
        })
    
    # 尝试从RSS获取真实新闻
    try:
        import feedparser
        rss_feeds = [
            {"url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=20&page=1&r=0.1&callback=", "name": "新浪财经"},
            {"url": "https://www.cls.cn/rss", "name": "财联社"},
        ]
        for feed_info in rss_feeds:
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries[:3]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))[:200]
                    link = entry.get("link", "")
                    oil_keywords = ["油", "能源", "汽油", "柴油", "原油", "OPEC"]
                    if any(kw in title for kw in oil_keywords):
                        news.append({
                            "title": title,
                            "summary": summary,
                            "url": link,
                            "source": feed_info["name"],
                            "category": "财经",
                            "published_at": today,
                            "relevance_score": 0.8,
                        })
            except Exception:
                continue
    except ImportError:
        pass
    
    return news[:10]  # 最多返回10条

def save_news(articles: List[Dict[str, Any]]):
    """保存新闻到数据库"""
    with get_db() as conn:
        for a in articles:
            conn.execute("""
                INSERT OR IGNORE INTO news_articles (title, summary, url, source, category, published_at, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (a["title"], a["summary"], a["url"], a["source"], a["category"], a["published_at"], a["relevance_score"]))

# ============================================================
# 图表生成
# ============================================================
def generate_trend_chart_html(days: int = 30) -> str:
    """生成油价趋势折线图HTML"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    with get_db() as conn:
        rows = conn.execute("""
            SELECT date, 
                   AVG(gasoline_92) as avg_92, 
                   AVG(gasoline_95) as avg_95, 
                   AVG(diesel_0) as avg_diesel
            FROM oil_prices 
            WHERE date >= date('now', ? || ' days')
            GROUP BY date ORDER BY date
        """, (f"-{days}",)).fetchall()
    
    if not rows:
        return "<h2>暂无数据生成趋势图</h2>"
    
    dates = [r["date"] for r in rows]
    avg_92 = [r["avg_92"] for r in rows]
    avg_95 = [r["avg_95"] for r in rows]
    avg_diesel = [r["avg_diesel"] for r in rows]
    
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(x=dates, y=avg_92, mode='lines+markers', name='92号汽油', line=dict(color='#FF6B6B', width=2)))
    fig.add_trace(go.Scatter(x=dates, y=avg_95, mode='lines+markers', name='95号汽油', line=dict(color='#4ECDC4', width=2)))
    fig.add_trace(go.Scatter(x=dates, y=avg_diesel, mode='lines+markers', name='0号柴油', line=dict(color='#45B7D1', width=2)))
    
    fig.update_layout(
        title=dict(text='📈 广西油价趋势图（最近{}天）'.format(days), font=dict(size=20)),
        xaxis_title='日期',
        yaxis_title='价格（元/升）',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def generate_regional_chart_html() -> str:
    """生成各地区油价对比柱状图HTML"""
    import plotly.graph_objects as go
    
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT region, gasoline_92, gasoline_95, diesel_0 
            FROM oil_prices WHERE date = ? ORDER BY gasoline_92 DESC
        """, (today,)).fetchall()
    
    if not rows:
        return "<h2>暂无今日数据生成对比图</h2>"
    
    regions = [r["region"] for r in rows]
    p92 = [r["gasoline_92"] for r in rows]
    p95 = [r["gasoline_95"] for r in rows]
    p0  = [r["diesel_0"] for r in rows]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='92号汽油', x=regions, y=p92, marker_color='#FF6B6B'))
    fig.add_trace(go.Bar(name='95号汽油', x=regions, y=p95, marker_color='#4ECDC4'))
    fig.add_trace(go.Bar(name='0号柴油', x=regions, y=p0, marker_color='#45B7D1'))
    
    fig.update_layout(
        title=dict(text='⛽ 广西各地今日油价对比', font=dict(size=20)),
        xaxis_title='地区',
        yaxis_title='价格（元/升）',
        barmode='group',
        template='plotly_white',
        height=500,
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def generate_calendar_chart_html() -> str:
    """生成日历热力图HTML"""
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    
    with get_db() as conn:
        rows = conn.execute("""
            SELECT date, AVG(gasoline_92) as avg_price 
            FROM oil_prices 
            WHERE date >= date('now', '-90 days')
            GROUP BY date ORDER BY date
        """).fetchall()
    
    if not rows:
        return "<h2>暂无数据生成日历图</h2>"
    
    # 构建日历数据
    df = pd.DataFrame(rows, columns=["date", "avg_price"])
    df["date"] = pd.to_datetime(df["date"])
    df["weekday"] = df["date"].dt.weekday  # 0=Monday
    df["week"] = (df["date"] - df["date"].min()).dt.days // 7
    
    # 创建热力图
    fig = go.Figure(data=go.Heatmap(
        z=df["avg_price"].values.reshape(-1, 1),
        x=df["date"].dt.strftime("%m-%d").values,
        y=["92号汽油"],
        colorscale='RdYlGn_r',  # 红=高价，绿=低价
        text=df["avg_price"].round(2).astype(str) + "元",
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate='%{x}<br>价格: %{z:.2f}元/升<extra></extra>',
        showscale=True,
        colorbar=dict(title="价格(元)")
    ))
    
    fig.update_layout(
        title=dict(text='🗓️ 油价日历热力图（颜色越红=价格越高）', font=dict(size=20)),
        xaxis_title='日期',
        height=300,
        template='plotly_white',
        yaxis=dict(showticklabels=True),
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

# ============================================================
# AI分析
# ============================================================
def analyze_and_recommend() -> Dict[str, Any]:
    """分析油价并给出加油推荐"""
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    
    with get_db() as conn:
        # 今日均价
        today_row = conn.execute("""
            SELECT AVG(gasoline_92) as avg_92, AVG(gasoline_95) as avg_95, AVG(diesel_0) as avg_diesel
            FROM oil_prices WHERE date = ?
        """, (today,)).fetchone()
        
        # 昨日均价
        yesterday_row = conn.execute("""
            SELECT AVG(gasoline_92) as avg_92
            FROM oil_prices WHERE date = ?
        """, (yesterday,)).fetchone()
        
        # 一周前均价
        week_row = conn.execute("""
            SELECT AVG(gasoline_92) as avg_92
            FROM oil_prices WHERE date <= ?
            ORDER BY date DESC LIMIT 1
        """, (week_ago,)).fetchone()
        
        # 最近7天趋势
        trend_rows = conn.execute("""
            SELECT date, AVG(gasoline_92) as avg_92 
            FROM oil_prices WHERE date >= date('now', '-7 days')
            GROUP BY date ORDER BY date
        """).fetchall()
    
    if not today_row or not today_row["avg_92"]:
        return {
            "analysis_date": today,
            "summary": "数据不足，无法分析",
            "recommendation": "请等待数据收集完成后查看分析结果",
            "confidence": 0.0,
        }
    
    avg_92 = today_row["avg_92"]
    avg_95 = today_row["avg_95"]
    avg_diesel = today_row["avg_diesel"]
    
    # 计算变化
    daily_change = 0
    weekly_change = 0
    if yesterday_row and yesterday_row["avg_92"]:
        daily_change = avg_92 - yesterday_row["avg_92"]
    if week_row and week_row["avg_92"]:
        weekly_change = avg_92 - week_row["avg_92"]
    
    # 趋势判断
    if len(trend_rows) >= 3:
        recent_prices = [r["avg_92"] for r in trend_rows[-3:]]
        if recent_prices[-1] > recent_prices[0]:
            trend = "上涨"
        elif recent_prices[-1] < recent_prices[0]:
            trend = "下跌"
        else:
            trend = "平稳"
    else:
        trend = "数据不足"
    
    # 获取相关新闻（用于分析）
    news_context = ""
    with get_db() as conn:
        news_rows = conn.execute(
            "SELECT title FROM news_articles ORDER BY collected_at DESC LIMIT 5"
        ).fetchall()
        if news_rows:
            news_context = "；".join([r["title"][:30] for r in news_rows[:3]])
    
    # 生成推荐（结合新闻）
    news_boost = 0
    if news_context:
        if any(kw in news_context for kw in ["上涨", "上调", "涨", "突破"]):
            news_boost = 0.1
        elif any(kw in news_context for kw in ["下跌", "下调", "降", "回落"]):
            news_boost = -0.1
    
    if trend == "上涨" and (weekly_change > 0.05 or news_boost > 0):
        recommendation = "⛽ 建议今天就去加油！油价处于上涨趋势，提前加油可以节省开支。"
        confidence = min(0.95, 0.85 + news_boost)
    elif trend == "上涨" and weekly_change > 0:
        recommendation = "📈 油价小幅上涨中，如果油箱不多了建议这两天加满。"
        confidence = 0.75
    elif trend == "下跌" and weekly_change < -0.05:
        recommendation = "💰 油价正在下跌，如果不是急用可以再等等，预计还能降。"
        confidence = 0.80
    elif trend == "下跌":
        recommendation = "📉 油价小幅回落，不急的话可以观望几天。"
        confidence = 0.70
    else:
        recommendation = "✅ 油价平稳，按需加油即可，不用特意等待。"
        confidence = 0.65
    
    # 构建分析结果
    trend_summary = ""
    if trend_rows:
        prices = [r["avg_92"] for r in trend_rows]
        trend_summary = f"近7天92号汽油均价从{prices[0]:.2f}元涨跌至{prices[-1]:.2f}元，" if len(prices) >= 2 else ""
    
    news_summary = f"近期新闻：{news_context}。" if news_context else ""
    
    summary = (
        f"今日广西92号汽油均价{avg_92:.2f}元/升，"
        f"95号汽油均价{avg_95:.2f}元/升，"
        f"0号柴油均价{avg_diesel:.2f}元/升。"
        f"{'较昨日' + ('上涨' if daily_change > 0 else '下跌') + f'{abs(daily_change):.2f}元' if abs(daily_change) > 0.001 else '与昨日持平'}。"
        f"{trend_summary}"
        f"整体趋势：{trend}。"
        f"{news_summary}"
    )
    
    result = {
        "analysis_date": today,
        "summary": summary,
        "trend": trend,
        "daily_change": round(daily_change, 3),
        "weekly_change": round(weekly_change, 3),
        "today_avg_prices": {
            "gasoline_92": round(avg_92, 2),
            "gasoline_95": round(avg_95, 2),
            "diesel_0": round(avg_diesel, 2),
        },
        "recommendation": recommendation,
        "confidence": confidence,
    }
    
    # 保存分析结果
    with get_db() as conn:
        conn.execute("""
            INSERT INTO analysis_results (analysis_date, analysis_type, summary, recommendation, confidence_score, raw_data)
            VALUES (?, 'daily', ?, ?, ?, ?)
        """, (today, summary, recommendation, confidence, json.dumps(result, ensure_ascii=False)))
    
    return result

# ============================================================
# 定时任务
# ============================================================
def daily_task():
    """每日定时任务：收集真实油价 + 真实新闻 + AI分析"""
    logger.info("⏰ 执行每日定时任务（真实数据源）...")
    try:
        from app.real_data_fetcher import collect_all
        result = collect_all()
        
        if result.get("oil_prices"):
            logger.info(f"✅ 真实油价: 92号={result['oil_prices']['gasoline_92']}  95号={result['oil_prices']['gasoline_95']}")
        logger.info(f"✅ 历史数据: {result.get('history_count', 0)}条")
        logger.info(f"✅ 真实新闻: {result.get('news_count', 0)}条")
        
        # AI分析
        analysis = analyze_and_recommend()
        logger.info(f"✅ 分析完成：{analysis['recommendation'][:50]}...")
        
    except Exception as e:
        logger.error(f"❌ 每日任务执行失败: {e}")
        # 备用方案
        try:
            prices = collect_oil_prices()
            save_oil_prices(prices)
            news = collect_news()
            save_news(news)
            analyze_and_recommend()
        except Exception as e2:
            logger.error(f"❌ 备用方案也失败: {e2}")

def start_scheduler():
    """启动定时任务调度器"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        scheduler = BackgroundScheduler()
        # 每天早上8点和晚上8点各执行一次
        scheduler.add_job(daily_task, 'cron', hour=8, minute=0, id='morning_task')
        scheduler.add_job(daily_task, 'cron', hour=20, minute=0, id='evening_task')
        scheduler.start()
        logger.info("📅 定时任务调度器已启动（每天08:00和20:00执行）")
        return scheduler
    except ImportError:
        logger.warning("⚠️ apscheduler未安装，定时任务不可用")
        return None

# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(
    title="广西油价监控分析系统",
    version="2.0.0",
    description="每日收集广西各地油价，AI智能分析，推荐加油时机"
)

@app.on_event("startup")
async def startup():
    """应用启动"""
    logger.info(f"🚀 启动 {settings.app_name} v2.0.0")
    init_db()
    seed_historical_data(30)  # 生成30天历史数据
    # 启动时执行一次
    daily_task()
    # 启动定时任务
    start_scheduler()

# ----- 根路径 -----

@app.get("/", response_class=HTMLResponse)
async def root():
    """Web UI界面"""
    return HTMLResponse(content=INDEX_HTML)

@app.get("/api")
async def api_root():
    """API根路径"""
    return {
        "app": settings.app_name,
        "version": "2.0.0",
        "status": "running",
        "features": ["油价收集", "趋势图表", "新闻资讯", "AI分析", "加油推荐"],
        "endpoints": {
            "健康检查": "/health",
            "今日油价": "/api/oil-prices/today",
            "历史油价": "/api/oil-prices/history",
            "油价趋势图": "/api/charts/trend",
            "地区对比图": "/api/charts/regional",
            "日历热力图": "/api/charts/calendar",
            "今日新闻": "/api/news/today",
            "AI分析推荐": "/api/analysis/today",
            "手动触发收集": "/api/collect",
            "API文档": "/docs",
        }
    }

# ============================================================
# HTML UI 界面
# ============================================================
INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>广西油价监控分析系统</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI','Microsoft YaHei',sans-serif;background:#f0f2f5;min-height:100vh;color:#333}
.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:28px 0;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.15)}
.header h1{font-size:2rem;margin-bottom:6px}
.header p{opacity:.85;font-size:.95rem}
.container{max-width:1100px;margin:20px auto;padding:0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px;margin-bottom:18px}
.card{background:#fff;border-radius:14px;padding:22px;box-shadow:0 2px 12px rgba(0,0,0,.06)}
.card h2{font-size:1.15rem;color:#667eea;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.card h2 .icon{font-size:1.3rem}
.badge{display:inline-block;padding:4px 14px;border-radius:12px;font-size:.82rem;font-weight:600}
.badge-green{background:#d4edda;color:#155724}
.badge-red{background:#f8d7da;color:#721c24}
.badge-blue{background:#cce5ff;color:#004085}
.price-table{width:100%;border-collapse:collapse;font-size:.9rem}
.price-table th{background:#f8f9fa;padding:8px 10px;text-align:center;font-weight:600;border-bottom:2px solid #dee2e6}
.price-table td{padding:7px 10px;text-align:center;border-bottom:1px solid #eee}
.price-table tr:hover{background:#f5f7ff}
.up{color:#dc3545;font-weight:600}
.down{color:#28a745;font-weight:600}
.flat{color:#6c757d}
.rec-box{background:linear-gradient(135deg,#fff3cd 0%,#ffeaa7 100%);border-radius:12px;padding:20px;margin-top:10px;font-size:1.05rem;line-height:1.6}
.rec-box .rec-text{font-size:1.15rem;font-weight:600;color:#856404;margin-bottom:8px}
.confidence{font-size:.85rem;color:#856404;margin-top:6px}
.news-list{list-style:none}
.news-list li{padding:10px 0;border-bottom:1px solid #f0f0f0}
.news-list li:last-child{border-bottom:none}
.news-list a{color:#333;text-decoration:none;font-weight:500}
.news-list a:hover{color:#667eea}
.news-meta{font-size:.8rem;color:#999;margin-top:3px}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.btn{display:inline-block;padding:9px 20px;border-radius:8px;text-decoration:none;font-size:.9rem;font-weight:500;cursor:pointer;border:none;transition:all .2s}
.btn-primary{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(102,126,234,.4)}
.btn-outline{background:transparent;border:1.5px solid #667eea;color:#667eea}
.btn-outline:hover{background:#667eea;color:#fff}
.stats{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}
.stat-item{flex:1;min-width:100px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center}
.stat-val{font-size:1.5rem;font-weight:700;color:#667eea}
.stat-label{font-size:.8rem;color:#888;margin-top:2px}
.chart-frame{width:100%;min-height:420px;border:none;border-radius:8px;margin-top:10px}
.footer{text-align:center;padding:24px;color:#aaa;font-size:.85rem}
@media(max-width:700px){.grid{grid-template-columns:1fr}.header h1{font-size:1.5rem}}
</style>
</head>
<body>
<div class="header">
  <h1>🛢️ 广西油价监控分析系统</h1>
  <p>每日自动收集油价 · AI智能分析 · 加油时机推荐</p>
</div>
<div class="container">
  <div id="loading" style="text-align:center;padding:60px;color:#888">
    <div style="font-size:2rem;margin-bottom:10px">⏳</div>
    <p>正在加载数据...</p>
  </div>
  <div id="app" style="display:none">
    <!-- 状态栏 -->
    <div class="grid">
      <div class="card">
        <h2><span class="icon">📊</span> 系统状态</h2>
        <div style="margin-bottom:12px">
          <span class="badge badge-green" id="status-badge">运行中</span>
          <span style="margin-left:10px;color:#888;font-size:.85rem">v2.0.0</span>
        </div>
        <div class="stats">
          <div class="stat-item"><div class="stat-val" id="s-records">-</div><div class="stat-label">数据记录</div></div>
          <div class="stat-item"><div class="stat-val" id="s-news">-</div><div class="stat-label">新闻</div></div>
          <div class="stat-item"><div class="stat-val" id="s-analysis">-</div><div class="stat-label">分析</div></div>
        </div>
        <div class="actions">
          <button class="btn btn-primary" onclick="refreshAll()">🔄 刷新数据</button>
          <button class="btn btn-outline" onclick="triggerCollect()">⚡ 手动采集</button>
        </div>
      </div>
      <div class="card">
        <h2><span class="icon">⛽</span> 今日油价</h2>
        <p style="color:#888;font-size:.85rem;margin-bottom:10px">日期：<span id="today-date">-</span></p>
        <div class="stats">
          <div class="stat-item"><div class="stat-val" id="p92">-</div><div class="stat-label">92号汽油</div></div>
          <div class="stat-item"><div class="stat-val" id="p95">-</div><div class="stat-label">95号汽油</div></div>
          <div class="stat-item"><div class="stat-val" id="p0">-</div><div class="stat-label">0号柴油</div></div>
        </div>
        <p style="color:#888;font-size:.82rem;margin-top:10px">广西14个地市均价（元/升）</p>
        <details style="margin-top:10px">
          <summary style="cursor:pointer;color:#667eea;font-size:.9rem">查看各地区详细价格 ▾</summary>
          <table class="price-table" id="price-table" style="margin-top:8px">
            <thead><tr><th>地区</th><th>92号</th><th>95号</th><th>0号柴油</th></tr></thead>
            <tbody id="price-tbody"></tbody>
          </table>
        </details>
      </div>
    </div>
    <!-- 分析 + 推荐 -->
    <div class="grid">
      <div class="card">
        <h2><span class="icon">🤖</span> AI分析推荐</h2>
        <div id="analysis-loading">加载中...</div>
        <div id="analysis-content" style="display:none">
          <p style="color:#555;line-height:1.7" id="analysis-summary"></p>
          <div class="rec-box" style="margin-top:14px">
            <div class="rec-text" id="rec-text"></div>
            <div class="confidence">置信度：<span id="rec-confidence"></span></div>
          </div>
        </div>
      </div>
      <div class="card">
        <h2><span class="icon">📰</span> 今日新闻</h2>
        <ul class="news-list" id="news-list"><li>加载中...</li></ul>
        <div class="actions">
          <a class="btn btn-outline" href="/api/news/today" target="_blank">查看全部</a>
        </div>
      </div>
    </div>
    <!-- 图表 -->
    <div class="grid">
      <div class="card" style="grid-column:1/-1">
        <h2><span class="icon">📈</span> 油价趋势图</h2>
        <iframe class="chart-frame" src="/api/charts/trend?days=30" id="trend-frame"></iframe>
      </div>
    </div>
    <div class="grid">
      <div class="card">
        <h2><span class="icon">📊</span> 各地区对比</h2>
        <iframe class="chart-frame" src="/api/charts/regional" style="min-height:380px"></iframe>
      </div>
      <div class="card">
        <h2><span class="icon">🗓️</span> 日历热力图</h2>
        <iframe class="chart-frame" src="/api/charts/calendar" style="min-height:300px"></iframe>
      </div>
    </div>
  </div>
  <div class="footer">广西油价监控分析系统 v2.0.0 · 数据仅供参考</div>
</div>
<script>
const API='';
async function fetchJSON(url){const r=await fetch(API+url);return r.json()}
function $(id){return document.getElementById(id)}
async function refreshAll(){
  try{
    const [stats,prices,analysis,news]=await Promise.all([
      fetchJSON('/api/stats'),
      fetchJSON('/api/oil-prices/today'),
      fetchJSON('/api/analysis/today'),
      fetchJSON('/api/news/today')
    ]);
    // stats
    $('s-records').textContent=stats.oil_price_records||0;
    $('s-news').textContent=stats.news_articles||0;
    $('s-analysis').textContent=stats.analysis_results||0;
    // prices
    $('today-date').textContent=prices.date;
    if(prices.average_prices){
      $('p92').textContent=prices.average_prices.gasoline_92?.toFixed(2)||'-';
      $('p95').textContent=prices.average_prices.gasoline_95?.toFixed(2)||'-';
      $('p0').textContent=prices.average_prices.diesel_0?.toFixed(2)||'-';
    }
    // price table - 按92号从小到大排序
    const tbody=$('price-tbody');tbody.innerHTML='';
    if(prices.prices){
      const sorted=[...prices.prices].sort((a,b)=>(a.gasoline_92||0)-(b.gasoline_92||0));
      sorted.forEach(p=>{
        const tr=document.createElement('tr');
        tr.innerHTML=`<td>${p.region}</td><td>${p.gasoline_92?.toFixed(2)}</td><td>${p.gasoline_95?.toFixed(2)}</td><td>${p.diesel_0?.toFixed(2)}</td>`;
        tbody.appendChild(tr);
      });
    }
    // analysis
    $('analysis-loading').style.display='none';
    $('analysis-content').style.display='block';
    $('analysis-summary').textContent=analysis.summary||analysis.raw_data?.summary||'暂无分析';
    $('rec-text').textContent=analysis.recommendation||analysis.raw_data?.recommendation||'';
    const conf=analysis.confidence_score||analysis.raw_data?.confidence||0;
    $('rec-confidence').textContent=(conf*100).toFixed(0)+'%';
    // news
    const nl=$('news-list');nl.innerHTML='';
    if(news.news&&news.news.length){
      news.news.forEach(n=>{
        const li=document.createElement('li');
        li.innerHTML=`<a href="${n.url}" target="_blank">${n.title}</a><div class="news-meta">${n.source} · ${n.published_at}</div>`;
        nl.appendChild(li);
      });
    }else{nl.innerHTML='<li style="color:#999">暂无新闻</li>';}
    // show
    $('loading').style.display='none';
    $('app').style.display='block';
  }catch(e){
    console.error(e);
    $('loading').innerHTML='<p style="color:red">加载失败，请刷新重试</p>';
  }
}
async function triggerCollect(){
  const btn=event.target;btn.disabled=true;btn.textContent='采集中...';
  await fetch(API+'/api/collect',{method:'POST'});
  btn.textContent='✅ 完成';setTimeout(()=>{btn.textContent='⚡ 手动采集';btn.disabled=false},2000);
  refreshAll();
}
document.addEventListener('DOMContentLoaded',refreshAll);
</script>
</body>
</html>"""

@app.get("/health")
async def health():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM oil_prices").fetchone()[0]
        latest = conn.execute("SELECT MAX(date) FROM oil_prices").fetchone()[0]
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "2.0.0",
        "total_records": count,
        "latest_date": latest,
    }

# ----- 油价API -----

@app.get("/api/oil-prices/today")
async def get_today_prices():
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM oil_prices WHERE date = ? ORDER BY gasoline_92 ASC", (today,)
        ).fetchall()
    
    if not rows:
        return {"date": today, "message": "今日暂无数据，请稍后重试或手动触发收集", "prices": []}
    
    prices = [dict(r) for r in rows]
    avg_92 = sum(p["gasoline_92"] for p in prices) / len(prices)
    avg_95 = sum(p["gasoline_95"] for p in prices) / len(prices)
    avg_diesel = sum(p["diesel_0"] for p in prices) / len(prices)
    
    return {
        "date": today,
        "average_prices": {"gasoline_92": round(avg_92, 2), "gasoline_95": round(avg_95, 2), "diesel_0": round(avg_diesel, 2)},
        "regions_count": len(prices),
        "prices": prices,
    }

@app.get("/api/oil-prices/history")
async def get_history_prices(
    days: int = Query(30, ge=1, le=365),
    region: Optional[str] = None,
):
    with get_db() as conn:
        if region:
            rows = conn.execute(
                "SELECT * FROM oil_prices WHERE region = ? AND date >= date('now', ? || ' days') ORDER BY date",
                (region, f"-{days}")
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT date, AVG(gasoline_92) as gasoline_92, AVG(gasoline_95) as gasoline_95, AVG(diesel_0) as diesel_0 "
                "FROM oil_prices WHERE date >= date('now', ? || ' days') GROUP BY date ORDER BY date",
                (f"-{days}",)
            ).fetchall()
    
    return {"days": days, "region": region, "records": len(rows), "prices": [dict(r) for r in rows]}

# ----- 图表API -----

@app.get("/api/charts/trend", response_class=HTMLResponse)
async def chart_trend(days: int = Query(30, ge=7, le=365)):
    return generate_trend_chart_html(days)

@app.get("/api/charts/regional", response_class=HTMLResponse)
async def chart_regional():
    return generate_regional_chart_html()

@app.get("/api/charts/calendar", response_class=HTMLResponse)
async def chart_calendar():
    return generate_calendar_chart_html()

# ----- 新闻API -----

@app.get("/api/news/today")
async def get_today_news():
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM news_articles WHERE published_at >= ? ORDER BY relevance_score DESC LIMIT 15",
            (today,)
        ).fetchall()
    
    if not rows:
        # 使用真实数据采集器
        try:
            from app.real_data_fetcher import fetch_all_news, save_news
            articles = fetch_all_news()
            if articles:
                save_news(articles)
        except Exception:
            # 备用
            articles = collect_news()
            save_news(articles)
        
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM news_articles WHERE published_at >= ? ORDER BY relevance_score DESC LIMIT 15",
                (today,)
            ).fetchall()
    
    return {"date": today, "count": len(rows), "news": [dict(r) for r in rows]}

# ----- AI分析API -----

@app.get("/api/analysis/today")
async def get_today_analysis():
    today = date.today().isoformat()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM analysis_results WHERE analysis_date = ? ORDER BY created_at DESC LIMIT 1",
            (today,)
        ).fetchone()
    
    if not row:
        # 没有就执行一次分析
        result = analyze_and_recommend()
        return result
    
    data = dict(row)
    if data.get("raw_data"):
        data["raw_data"] = json.loads(data["raw_data"])
    return data

# ----- 手动触发 -----

@app.post("/api/collect")
async def trigger_collection():
    daily_task()
    return {"success": True, "message": "数据收集和分析完成，请查看各API获取结果"}

# ----- 统计信息 -----

@app.get("/api/stats")
async def get_stats():
    with get_db() as conn:
        total_prices = conn.execute("SELECT COUNT(*) FROM oil_prices").fetchone()[0]
        total_news = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
        total_analysis = conn.execute("SELECT COUNT(*) FROM analysis_results").fetchone()[0]
        latest_date = conn.execute("SELECT MAX(date) FROM oil_prices").fetchone()[0]
        date_range = conn.execute("SELECT MIN(date), MAX(date) FROM oil_prices").fetchone()
    
    return {
        "oil_price_records": total_prices,
        "news_articles": total_news,
        "analysis_results": total_analysis,
        "latest_date": latest_date,
        "date_range": {"from": date_range[0], "to": date_range[1]} if date_range[0] else None,
    }

# ============================================================
# 启动入口
# ============================================================
if __name__ == "__main__":
    uvicorn.run(
        "app.main_full:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
