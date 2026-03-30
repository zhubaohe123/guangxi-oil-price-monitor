"""
新闻收集器 - 专门收集油价相关新闻
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import feedparser
import re

from app.config_simple import settings
from app.database.models import NewsArticle
from app.database import get_session

logger = logging.getLogger(__name__)


class NewsCollector:
    """新闻收集器 - 专门收集油价相关新闻"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        # 油价相关关键词
        self.oil_keywords = [
            "油价", "汽油", "柴油", "石油", "原油", "能源",
            "加油站", "燃油", "成品油", "调价", "发改委",
            "国际油价", "国内油价", "油价调整", "油价上涨", "油价下跌"
        ]
        
        # 广西相关关键词
        self.guangxi_keywords = [
            "广西", "南宁", "柳州", "桂林", "梧州", "北海",
            "防城港", "钦州", "贵港", "玉林", "百色",
            "贺州", "河池", "来宾", "崇左"
        ]
    
    async def collect_all_news(self) -> List[NewsArticle]:
        """收集所有油价相关新闻"""
        logger.info("开始收集油价相关新闻")
        
        news_articles = []
        successful_sources = 0
        
        for source in settings.news_sources:
            if not source.get("enabled", True):
                continue
            
            try:
                logger.info(f"从 {source['name']} 收集新闻")
                
                articles = []
                if source["type"] == "rss":
                    articles = await self._collect_rss_news(source)
                elif source["type"] == "website":
                    articles = await self._collect_website_news(source)
                elif source["type"] == "api":
                    articles = await self._collect_api_news(source)
                
                if articles:
                    # 过滤和去重
                    filtered_articles = self._filter_and_deduplicate(articles)
                    news_articles.extend(filtered_articles)
                    successful_sources += 1
                    
                    logger.info(f"从 {source['name']} 收集到 {len(filtered_articles)} 条新闻")
                    
            except Exception as e:
                logger.error(f"从 {source['name']} 收集新闻失败: {e}")
                continue
        
        # 保存到数据库
        if news_articles:
            await self._save_to_database(news_articles)
        
        logger.info(f"从 {successful_sources} 个数据源成功收集 {len(news_articles)} 条新闻")
        return news_articles
    
    async def _collect_rss_news(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从RSS源收集新闻"""
        articles = []
        
        try:
            feed = feedparser.parse(source["url"])
            
            for entry in feed.entries[:15]:  # 取最新15条
                title = entry.get('title', '').strip()
                summary = entry.get('summary', '').strip() or entry.get('description', '').strip()
                link = entry.get('link', '').strip()
                
                # 获取发布时间
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    from time import mktime
                    published_at = datetime.fromtimestamp(mktime(published))
                else:
                    published_at = datetime.now()
                
                # 检查是否与油价相关
                if self._is_oil_related(title, summary):
                    articles.append({
                        "title": title,
                        "summary": summary[:500] if len(summary) > 500 else summary,
                        "url": link,
                        "source": source["name"],
                        "published_at": published_at,
                        "category": source.get("category", "新闻"),
                        "relevance_score": self._calculate_relevance(title, summary)
                    })
        
        except Exception as e:
            logger.error(f"解析RSS源 {source['name']} 失败: {e}")
        
        return articles
    
    async def _collect_website_news(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从网站收集新闻"""
        articles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source["url"], headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 不同网站的解析策略
                        parser = source.get("parser", "")
                        
                        if parser == "tencent":
                            articles = self._parse_tencent_news(soup, source)
                        elif parser == "eastmoney":
                            articles = self._parse_eastmoney_news(soup, source)
                        elif parser == "hexun":
                            articles = self._parse_hexun_news(soup, source)
                        elif parser == "china5e":
                            articles = self._parse_china5e_news(soup, source)
                        else:
                            articles = self._parse_generic_news(soup, source)
        
        except Exception as e:
            logger.error(f"从网站 {source['name']} 收集新闻失败: {e}")
        
        return articles
    
    def _parse_tencent_news(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析腾讯财经新闻"""
        articles = []
        
        try:
            # 腾讯财经的新闻列表
            news_items = soup.find_all(['div', 'li'], class_=re.compile(r'news|item|list'))
            
            for item in news_items[:20]:  # 取前20个
                title_elem = item.find(['a', 'h3', 'h4'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    # 获取摘要
                    summary_elem = item.find('p', class_=re.compile(r'summary|desc|intro'))
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    # 获取时间
                    time_elem = item.find('span', class_=re.compile(r'time|date'))
                    time_text = time_elem.get_text(strip=True) if time_elem else ""
                    
                    if title and link and self._is_oil_related(title, summary):
                        # 处理链接
                        if link and not link.startswith('http'):
                            link = "https://finance.qq.com" + link if link.startswith('/') else link
                        
                        articles.append({
                            "title": title,
                            "summary": summary[:300] if summary else title[:100],
                            "url": link,
                            "source": source["name"],
                            "published_at": self._parse_time_string(time_text),
                            "category": source.get("category", "财经"),
                            "relevance_score": self._calculate_relevance(title, summary)
                        })
        
        except Exception as e:
            logger.error(f"解析腾讯新闻失败: {e}")
        
        return articles
    
    def _parse_eastmoney_news(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析东方财富网新闻"""
        articles = []
        
        try:
            # 东方财富网的新闻结构
            news_divs = soup.find_all('div', class_=re.compile(r'article|news'))
            
            for div in news_divs[:15]:
                title_elem = div.find(['a', 'h2', 'h3'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    if title and link and any(keyword in title for keyword in self.oil_keywords):
                        # 获取更多信息
                        summary = div.get_text(strip=True)[:200]
                        
                        articles.append({
                            "title": title,
                            "summary": summary,
                            "url": link if link.startswith('http') else "https://www.eastmoney.com" + link,
                            "source": source["name"],
                            "published_at": datetime.now(),
                            "category": source.get("category", "财经"),
                            "relevance_score": self._calculate_relevance(title, summary)
                        })
        
        except Exception as e:
            logger.error(f"解析东方财富新闻失败: {e}")
        
        return articles
    
    def _parse_hexun_news(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析和讯网能源新闻"""
        articles = []
        
        try:
            # 和讯网能源频道
            news_items = soup.find_all(['div', 'li'], class_=re.compile(r'news|list|item'))
            
            for item in news_items[:15]:
                text = item.get_text(strip=True)
                if any(keyword in text for keyword in ["油价", "汽油", "柴油", "石油"]):
                    title_elem = item.find('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        articles.append({
                            "title": title,
                            "summary": text[:200],
                            "url": link if link.startswith('http') else "http://energy.hexun.com" + link,
                            "source": source["name"],
                            "published_at": datetime.now(),
                            "category": source.get("category", "能源"),
                            "relevance_score": self._calculate_relevance(title, text)
                        })
        
        except Exception as e:
            logger.error(f"解析和讯网新闻失败: {e}")
        
        return articles
    
    def _parse_china5e_news(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析中国能源网新闻"""
        articles = []
        
        try:
            # 中国能源网
            news_links = soup.find_all('a', href=re.compile(r'news|article'))
            
            for link in news_links[:20]:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                if title and len(title) > 10 and any(keyword in title for keyword in self.oil_keywords):
                    articles.append({
                        "title": title,
                        "summary": title[:150],
                        "url": href if href.startswith('http') else "http://www.china5e.com" + href,
                        "source": source["name"],
                        "published_at": datetime.now(),
                        "category": source.get("category", "能源"),
                        "relevance_score": self._calculate_relevance(title, "")
                    })
        
        except Exception as e:
            logger.error(f"解析中国能源网新闻失败: {e}")
        
        return articles
    
    def _parse_generic_news(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """通用新闻解析"""
        articles = []
        
        try:
            # 查找所有新闻链接
            all_links = soup.find_all('a')
            
            for link in all_links[:50]:  # 检查前50个链接
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                # 判断是否是新闻链接
                if (len(title) > 15 and len(title) < 200 and 
                    any(keyword in title.lower() for keyword in ["新闻", "报道", "资讯", "快讯"]) and
                    self._is_oil_related(title, "")):
                    
                    # 确保URL完整
                    if href and not href.startswith('http'):
                        base_url = source["url"]
                        if base_url.endswith('/'):
                            base_url = base_url[:-1]
                        if href.startswith('/'):
                            href = base_url + href
                        else:
                            href = base_url + '/' + href
                    
                    articles.append({
                        "title": title,
                        "summary": title[:150],
                        "url": href,
                        "source": source["name"],
                        "published_at": datetime.now(),
                        "category": source.get("category", "新闻"),
                        "relevance_score": self._calculate_relevance(title, "")
                    })
        
        except Exception as e:
            logger.error(f"通用新闻解析失败: {e}")
        
        return articles
    
    async def _collect_api_news(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从API收集新闻"""
        # 百度新闻搜索API（需要申请API Key）
        # 这里提供模拟实现
        return []
    
    def _is_oil_related(self, title: str, content: str) -> bool:
        """判断内容是否与油价相关"""
        text = (title + " " + content).lower()
        
        # 检查是否包含油价关键词
        oil_related = any(keyword in text for keyword in self.oil_keywords)
        
        # 排除不相关的内容
        exclude_keywords = ["食用油", "菜籽油", "花生油", "橄榄油", "豆油"]
        not_related = any(keyword in text for keyword in exclude_keywords)
        
        return oil_related and not not_related
    
    def _calculate_relevance(self, title: str, content: str) -> float:
        """计算新闻相关性分数"""
        text = (title + " " + content).lower()
        score = 0.0
        
        # 基础分数
        for keyword in self.oil_keywords:
            if keyword in text:
                score += 0.5
        
        # 广西相关加分
        for keyword in self.guangxi_keywords:
            if keyword in text:
                score += 0.3
        
        # 限制在0-1之间
        return min(1.0, score / 5.0)
    
    def _parse_time_string(self, time_str: str) -> datetime:
        """解析时间字符串"""
        try:
            # 尝试多种时间格式
            patterns = [
                r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})日?',
                r'(\d{1,2})月(\d{1,2})日',
                r'(\d{1,2})[-/](\d{1,2})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, time_str)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        year, month, day = map(int, groups)
                        return datetime(year, month, day)
                    elif len(groups) == 2:
                        month, day = map(int, groups)
                        year = datetime.now().year
                        return datetime(year, month, day)
        
        except Exception:
            pass
        
        # 默认返回当前时间
        return datetime.now()
    
    def _filter_and_deduplicate(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤和去重新闻"""
        seen_titles = set()
        filtered = []
        
        for article in articles:
            title = article["title"].strip()
            
            # 去重
            if title in seen_titles:
                continue
            
            # 过滤低相关性新闻
            if article.get("relevance_score", 0) < 0.3:
                continue
            
            # 过滤过短的标题
            if len(title) < 10:
                continue
            
            seen_titles.add(title)
            filtered.append(article)
        
        # 按相关性排序
        filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return filtered[:20]  # 返回最多20条
    
    async def _save_to_database(self, articles: List[Dict[str, Any]]):
        """保存新闻到数据库"""
        try:
            news_objects = []
            
            for article in articles:
                news = NewsArticle(
                    title=article["title"],
                    summary=article["summary"],
                    url=article["url"],
                    source=article["source"],
                    category=article["category"],
                    published_at=article["published_at"],
                    relevance_score=article.get("relevance_score", 0.5),
                    collected_at=datetime.now()
                )
                news_objects.append(news)
            
            async with get_session() as session:
                # 批量插入，忽略重复
                for news in news_objects:
                    # 检查是否已存在
                    existing = await session.execute(
                        "SELECT id FROM news_articles WHERE title = :title AND source = :source",
                        {"title": news.title, "source": news.source}
                    )
                    
                    if not existing.fetchone():
                        session.add(news)
                
                await session.commit()
                logger.info(f"成功保存 {len(news_objects)} 条新闻到数据库")
                
        except Exception as e:
            logger.error(f"保存新闻到数据库失败: {e}")
            if 'session' in locals():
                await session.rollback()
    
    async def get_today_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取今日新闻"""
        from sqlalchemy import select, desc
        
        try:
            today = datetime.now().date()
            
            async with get_session() as session:
                stmt = select(NewsArticle).where(
                    NewsArticle.published_at >= today
                ).order_by(
                    desc(NewsArticle.relevance_score),
                    desc(NewsArticle.published_at)
                ).limit(limit)
                
                result = await session.execute(stmt)
                news = result.scalars().all()
                
                return [
                    {
                        "title": n.title,
                        "summary": n.summary,
                        "url": n.url,
                        "source": n.source,
                        "category": n.category,
                        "published_at": n.published_at.strftime("%Y-%m-%d %H:%M"),
                        "relevance_score": n.relevance_score
                    }
                    for n in news
                ]
        
        except Exception as e:
            logger.error(f"获取今日新闻失败: {e}")
            return []
    
    async def search_news(self, keyword: str, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索新闻"""
        from sqlalchemy import select, desc, or_
        from datetime import datetime, timedelta
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            async with get_session() as session:
                stmt = select(NewsArticle).where(
                    NewsArticle.published_at >= start_date,
                    or_(
                        NewsArticle.title.ilike(f"%{keyword}%"),
                        NewsArticle.summary.ilike(f"%{keyword}%")
                    )
                ).order_by(
                    desc(NewsArticle.relevance_score),
                    desc(NewsArticle.published_at)
                ).limit(limit)
                
                result = await session.execute(stmt)
                news = result.scalars().all()
                
                return [
                    {
                        "title": n.title,
                        "summary": n.summary,
                        "url": n.url,
                        "source": n.source,
                        "category": n.category,
                        "published_at": n.published_at.strftime("%Y-%m-%d %H:%M"),
                        "relevance_score": n.relevance_score
                    }
                    for n in news
                ]
        
        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            return []
    
    def export_news(self, articles: List[Dict[str, Any]], format: str = "json") -> str:
        """导出新闻"""
        import json
        
        if format == "json":
            return json.dumps(articles, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow(["标题", "摘要", "来源", "分类", "发布时间", "相关度", "链接"])
            
            # 写入数据
            for article in articles:
                writer.writerow([
                    article["title"],
                    article["summary"][:100] if article["summary"] else "",
                    article["source"],
                    article["category"],
                    article["published_at"],
                    f"{article.get('relevance_score', 0):.2f}",
                    article["url"]
                ])
            
            return output.getvalue()
        else:
            return ""


# 创建新闻收集器实例
news_collector = NewsCollector()