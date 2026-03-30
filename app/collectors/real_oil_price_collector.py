"""
真实油价数据收集器 - 使用免费数据源
"""
import asyncio
import logging
import re
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import feedparser
import pandas as pd

from app.config import settings
from app.database.models import OilPrice
from app.database import get_session

logger = logging.getLogger(__name__)


class RealOilPriceCollector:
    """真实油价数据收集器 - 使用免费数据源"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        # 地图API配置（免费额度）
        self.amap_key = None  # 需要申请高德地图Web服务API Key
        self.baidu_key = None  # 需要申请百度地图API Key
    
    async def collect_all_regions_real(self) -> List[OilPrice]:
        """使用真实数据源收集所有地区的油价数据"""
        logger.info("开始使用真实数据源收集广西各地油价数据")
        
        oil_prices = []
        successful_sources = 0
        
        # 尝试多个数据源，直到获取足够数据
        for source in settings.oil_price_sources:
            if not source.get("enabled", True):
                continue
            
            try:
                logger.info(f"尝试从 {source['name']} 收集数据")
                
                if source["type"] == "website":
                    prices = await self.collect_from_website(source)
                elif source["type"] == "api":
                    prices = await self.collect_from_api(source)
                elif source["type"] == "rss":
                    prices = await self.collect_from_rss(source)
                else:
                    continue
                
                if prices:
                    oil_prices.extend(prices)
                    successful_sources += 1
                    logger.info(f"从 {source['name']} 成功收集到 {len(prices)} 条数据")
                    
                    # 如果已经收集到足够数据，可以提前结束
                    if len(oil_prices) >= len(settings.guangxi_regions) * 0.7:  # 收集到70%地区的数据
                        break
                        
            except Exception as e:
                logger.error(f"从 {source['name']} 收集数据失败: {e}")
                continue
        
        # 保存到数据库
        if oil_prices:
            await self.save_to_database(oil_prices)
            logger.info(f"从 {successful_sources} 个数据源成功收集 {len(oil_prices)} 条油价数据")
        else:
            logger.warning("未能从任何数据源收集到油价数据，使用模拟数据")
            oil_prices = await self._get_fallback_data()
        
        return oil_prices
    
    async def collect_from_website(self, source: Dict[str, Any]) -> List[OilPrice]:
        """从网站抓取油价数据"""
        parser = source.get("parser", "")
        url = source["url"]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        if parser == "yiche":
                            return await self._parse_yiche(html, source.get("region", ""))
                        elif parser == "autohome":
                            return await self._parse_autohome(html, source.get("region", ""))
                        elif parser == "youjiawang":
                            return await self._parse_youjiawang(html, source.get("region", ""))
                        elif parser == "government":
                            return await self._parse_government(html, source.get("region", ""))
                        else:
                            return await self._parse_generic(html, source.get("region", ""))
                    else:
                        logger.error(f"请求 {source['name']} 失败: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"从网站 {source['name']} 收集数据异常: {e}")
            return []
    
    async def _parse_yiche(self, html: str, region: str) -> List[OilPrice]:
        """解析易车网油价数据"""
        soup = BeautifulSoup(html, 'html.parser')
        prices = []
        
        try:
            # 易车网油价页面结构
            # 查找包含油价信息的区域
            price_sections = soup.find_all('div', class_=re.compile(r'price|youjia'))
            
            for section in price_sections:
                # 尝试提取地区名称
                region_elem = section.find('span', class_=re.compile(r'city|region'))
                if region_elem:
                    region_name = region_elem.get_text(strip=True)
                    # 检查是否是广西地区
                    if "广西" in region_name or any(city in region_name for city in ["南宁", "柳州", "桂林"]):
                        # 提取油价
                        price_elems = section.find_all('span', class_=re.compile(r'num|price-num'))
                        if len(price_elems) >= 3:
                            try:
                                price_92 = float(price_elems[0].get_text(strip=True))
                                price_95 = float(price_elems[1].get_text(strip=True))
                                price_diesel = float(price_elems[2].get_text(strip=True))
                                
                                prices.append(OilPrice(
                                    region=region_name.replace("广西", "").strip() or "广西",
                                    date=date.today(),
                                    gasoline_92=price_92,
                                    gasoline_95=price_95,
                                    diesel_0=price_diesel,
                                    source="易车网",
                                    collected_at=datetime.now()
                                ))
                            except (ValueError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"解析易车网数据失败: {e}")
        
        return prices
    
    async def _parse_autohome(self, html: str, region: str) -> List[OilPrice]:
        """解析汽车之家油价数据"""
        soup = BeautifulSoup(html, 'html.parser')
        prices = []
        
        try:
            # 汽车之家油价页面可能有表格结构
            tables = soup.find_all('table')
            
            for table in tables:
                # 查找包含"广西"或地区名的行
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        region_cell = cells[0].get_text(strip=True)
                        if "广西" in region_cell or any(city in region_cell for city in settings.guangxi_regions):
                            try:
                                price_92 = float(cells[1].get_text(strip=True))
                                price_95 = float(cells[2].get_text(strip=True))
                                price_diesel = float(cells[3].get_text(strip=True))
                                
                                prices.append(OilPrice(
                                    region=region_cell,
                                    date=date.today(),
                                    gasoline_92=price_92,
                                    gasoline_95=price_95,
                                    diesel_0=price_diesel,
                                    source="汽车之家",
                                    collected_at=datetime.now()
                                ))
                            except (ValueError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"解析汽车之家数据失败: {e}")
        
        return prices
    
    async def _parse_youjiawang(self, html: str, region: str) -> List[OilPrice]:
        """解析油价网数据"""
        soup = BeautifulSoup(html, 'html.parser')
        prices = []
        
        try:
            # 油价网可能有更结构化的数据
            # 查找包含价格的div
            price_divs = soup.find_all('div', class_=re.compile(r'oil-price|fuel-price'))
            
            for div in price_divs:
                text = div.get_text(strip=True)
                # 使用正则表达式提取价格
                price_pattern = r'(\d+\.\d+)'
                found_prices = re.findall(price_pattern, text)
                
                if len(found_prices) >= 3:
                    # 尝试提取地区
                    region_match = re.search(r'([南宁柳州桂林梧州北海防城港钦州贵港玉林百色贺州河池来宾崇左])', text)
                    region_name = region_match.group(1) if region_match else "广西"
                    
                    try:
                        prices.append(OilPrice(
                            region=region_name,
                            date=date.today(),
                            gasoline_92=float(found_prices[0]),
                            gasoline_95=float(found_prices[1]),
                            diesel_0=float(found_prices[2]),
                            source="油价网",
                            collected_at=datetime.now()
                        ))
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            logger.error(f"解析油价网数据失败: {e}")
        
        return prices
    
    async def _parse_government(self, html: str, region: str) -> List[OilPrice]:
        """解析政府网站数据"""
        # 政府网站通常有规范的公告格式
        soup = BeautifulSoup(html, 'html.parser')
        prices = []
        
        try:
            # 查找公告或通知
            notices = soup.find_all(['div', 'p'], text=re.compile(r'油价|汽油|柴油|调整'))
            
            for notice in notices:
                text = notice.get_text(strip=True)
                
                # 提取价格信息
                price_pattern = r'(\d+\.\d+)\s*元'
                found_prices = re.findall(price_pattern, text)
                
                if found_prices:
                    # 政府公告通常包含执行日期
                    date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
                    date_match = re.search(date_pattern, text)
                    
                    if date_match:
                        year, month, day = map(int, date_match.groups())
                        price_date = date(year, month, day)
                    else:
                        price_date = date.today()
                    
                    # 尝试确定地区
                    region_name = "广西"
                    for city in settings.guangxi_regions:
                        if city in text:
                            region_name = city
                            break
                    
                    if len(found_prices) >= 3:
                        try:
                            prices.append(OilPrice(
                                region=region_name,
                                date=price_date,
                                gasoline_92=float(found_prices[0]),
                                gasoline_95=float(found_prices[1]),
                                diesel_0=float(found_prices[2]),
                                source="政府网站",
                                collected_at=datetime.now()
                            ))
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            logger.error(f"解析政府网站数据失败: {e}")
        
        return prices
    
    async def _parse_generic(self, html: str, region: str) -> List[OilPrice]:
        """通用解析方法"""
        soup = BeautifulSoup(html, 'html.parser')
        prices = []
        
        # 尝试多种常见的价格显示模式
        price_patterns = [
            r'92[号#]?\s*汽油?\s*[:：]?\s*(\d+\.\d+)',
            r'95[号#]?\s*汽油?\s*[:：]?\s*(\d+\.\d+)',
            r'0[号#]?\s*柴油?\s*[:：]?\s*(\d+\.\d+)',
            r'汽油.*?(\d+\.\d+)',
            r'柴油.*?(\d+\.\d+)'
        ]
        
        all_text = soup.get_text()
        
        # 查找所有价格
        found_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            found_prices.extend(matches)
        
        if found_prices:
            # 去重并排序
            unique_prices = list(set(found_prices))
            numeric_prices = []
            for p in unique_prices:
                try:
                    numeric_prices.append(float(p))
                except ValueError:
                    continue
            
            numeric_prices.sort()
            
            if len(numeric_prices) >= 3:
                # 假设前三个是不同的油价
                prices.append(OilPrice(
                    region=region or "广西",
                    date=date.today(),
                    gasoline_92=numeric_prices[0],
                    gasoline_95=numeric_prices[1],
                    diesel_0=numeric_prices[2],
                    source="通用解析",
                    collected_at=datetime.now()
                ))
        
        return prices
    
    async def collect_from_api(self, source: Dict[str, Any]) -> List[OilPrice]:
        """从API获取油价数据"""
        parser = source.get("parser", "")
        
        if parser == "amap" and self.amap_key:
            return await self._collect_from_amap(source)
        elif parser == "baidu" and self.baidu_key:
            return await self._collect_from_baidu(source)
        elif parser == "baidu_news":
            return await self._collect_news_from_baidu(source)
        else:
            logger.warning(f"API {source['name']} 需要配置API Key")
            return []
    
    async def _collect_from_amap(self, source: Dict[str, Any]) -> List[OilPrice]:
        """从高德地图API获取油价数据"""
        # 高德地图的加油站搜索API可以获取油价
        # 实际实现需要申请高德地图Web服务API Key
        return []
    
    async def _collect_from_baidu(self, source: Dict[str, Any]) -> List[OilPrice]:
        """从百度地图API获取油价数据"""
        # 百度地图的Place API可以搜索加油站
        # 实际实现需要申请百度地图API Key
        return []
    
    async def collect_from_rss(self, source: Dict[str, Any]) -> List[OilPrice]:
        """从RSS源获取油价相关新闻"""
        # RSS主要用于新闻，不是油价数据
        # 这里可以解析新闻中的油价信息
        return []
    
    async def _collect_news_from_baidu(self, source: Dict[str, Any]) -> List[OilPrice]:
        """从百度新闻搜索油价相关新闻"""
        # 百度新闻搜索可以获取油价相关新闻
        # 但不会直接提供油价数据
        return []
    
    async def _get_fallback_data(self) -> List[OilPrice]:
        """获取备用数据（模拟数据）"""
        logger.info("使用模拟数据作为备用")
        
        prices = []
        import random
        
        base_prices = {
            "南宁": {"gasoline_92": 7.85, "gasoline_95": 8.45, "diesel_0": 7.52},
            "柳州": {"gasoline_92": 7.83, "gasoline_95": 8.43, "diesel_0": 7.50},
            "桂林": {"gasoline_92": 7.84, "gasoline_95": 8.44, "diesel_0": 7.51},
            "梧州": {"gasoline_92": 7.82, "gasoline_95": 8.42, "diesel_0": 7.49},
            "北海": {"gasoline_92": 7.86, "gasoline_95": 8.46, "diesel_0": 7.53},
            "防城港": {"gasoline_92": 7.81, "gasoline_95": 8.41, "diesel_0": 7.48},
            "钦州": {"gasoline_92": 7.83, "gasoline_95": 8.43, "diesel_0": 7.50},
            "贵港": {"gasoline_92": 7.82, "gasoline_95": 8.42, "diesel_0": 7.49},
            "玉林": {"gasoline_92": 7.84, "gasoline_95": 8.44, "diesel_0": 7.51},
            "百色": {"gasoline_92": 7.80, "gasoline_95": 8.40, "diesel_0": 7.47},
            "贺州": {"gasoline_92": 7.82, "gasoline_95": 8.42, "diesel_0": 7.49},
            "河池": {"gasoline_92": 7.81, "gasoline_95": 8.41, "diesel_0": 7.48},
            "来宾": {"gasoline_92": 7.83, "gasoline_95": 8.43, "diesel_0": 7.50},
            "崇左": {"gasoline_92": 7.82, "gasoline_95": 8.42, "diesel_0": 7.49},
        }
        
        for region, base_price in base_prices.items():
            # 添加随机波动
            price_92 = base_price["gasoline_92"] + random.uniform(-0.05, 0.05)
            price_95 = base_price["gasoline_95"] + random.uniform(-0.05, 0.05)
            price_diesel = base_price["diesel_0"] + random.uniform(-0.05, 0.05)
            
            prices.append(OilPrice(
                region=region,
                date=date.today(),
                gasoline_92=round(price_92, 2),
                gasoline_95=round(price_95, 2),
                diesel_0=round(price_diesel, 2),
                source="模拟数据（备用）",
                collected_at=datetime.now()
            ))
        
        return prices
    
    async def save_to_database(self, oil_prices: List[OilPrice]):
        """保存油价数据到数据库"""
        try:
            async with get_session() as session:
                for price in oil_prices:
                    # 检查是否已存在当天的数据
                    existing = await session.execute(
                        "SELECT id FROM oil_prices WHERE region = :region AND date = :date",
                        {"region": price.region, "date": price.date}
                    )
                    
                    if not existing.fetchone():
                        session.add(price)
                
                await session.commit()
                logger.info(f"成功保存{len(oil_prices)}条油价数据")
                
        except Exception as e:
            logger.error(f"保存油价数据失败: {e}")
            if 'session' in locals():
                await session.rollback()
    
    async def collect_news(self) -> List[Dict[str, Any]]:
        """收集油价相关新闻"""
        logger.info("开始收集油价相关新闻")
        
        news_items = []
        
        for source in settings.news_sources:
            if not source.get("enabled", True):
                continue
            
            try:
                if source["type"] == "rss":
                    items = await self._collect_from_rss_news(source)
                elif source["type"] == "website":
                    items = await self._collect_from_website_news(source)
                elif source["type"] == "api":
                    items = await self._collect_from_api_news(source)
                else:
                    continue
                
                if items:
                    news_items.extend(items)
                    logger.info(f"从 {source['name']} 收集到 {len(items)} 条新闻")
                    
            except Exception as e:
                logger.error(f"从 {source['name']} 收集新闻失败: {e}")
                continue
        
        logger.info(f"共收集到 {len(news_items)} 条油价相关新闻")
        return news_items
    
    async def _collect_from_rss_news(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从RSS源收集新闻"""
        news_items = []
        
        try:
            feed = feedparser.parse(source["url"])
            
            for entry in feed.entries[:10]:  # 取最新10条
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                # 检查是否与油价相关
                keywords = ["油价", "汽油", "柴油", "石油", "能源", "加油站"]
                if any(keyword in title or keyword in summary for keyword in keywords):
                    news_items.append({
                        "title": title,
                        "summary": summary,
                        "url": link,
                        "source": source["name"],
                        "published_at": published,
                        "category": source.get("category", "新闻")
                    })
        
        except Exception as e:
            logger.error(f"解析RSS源 {source['name']} 失败: {e}")
        
        return news_items
    
    async def _collect_from_website_news(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从网站收集新闻"""
        news_items = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source["url"], headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 查找新闻链接
                        news_links = soup.find_all('a', href=True)
                        
                        for link in news_links[:20]:  # 取前20个链接
                            text = link.get_text(strip=True)
                            href = link['href']
                            
                            # 检查是否是新闻链接
                            if len(text) > 10 and any(keyword in text.lower() for keyword in ["油价", "汽油", "柴油"]):
                                # 确保是完整URL
                                if not href.startswith('http'):
                                    href = source["url"] + href if href.startswith('/') else href
                                
                                news_items.append({
                                    "title": text,
                                    "summary": text[:100] + "..." if len(text) > 100 else text,
                                    "url": href,
                                    "source": source["name"],
                                    "published_at": datetime.now().strftime("%Y-%m-%d"),
                                    "category": source.get("category", "新闻")
                                })
        
        except Exception as e:
            logger.error(f"从网站 {source['name']} 收集新闻失败: {e}")
        
        return news_items
    
    async def _collect_from_api_news(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从API收集新闻"""
        # 百度新闻搜索API实现
        return []
    
    def export_data(self, oil_prices: List[OilPrice], format: str = "csv") -> str:
        """导出数据"""
        if format == "csv":
            return self._export_to_csv(oil_prices)
        elif format == "json":
            return self._export_to_json(oil_prices)
        else:
            return ""
    
    def _export_to_csv(self, oil_prices: List[OilPrice]) -> str:
        """导出为CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(["地区", "日期", "92号汽油", "95号汽油", "0号柴油", "数据源", "收集时间"])
        
        # 写入数据
        for price in oil_prices:
            writer.writerow([
                price.region,
                price.date.strftime("%Y-%m-%d"),
                price.gasoline_92,
                price.gasoline_95,
                price.diesel_0,
                price.source,
                price.collected_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        return output.getvalue()
    
    def _export_to_json(self, oil_prices: List[OilPrice]) -> str:
        """导出为JSON"""
        data = []
        for price in oil_prices:
            data.append({
                "region": price.region,
                "date": price.date.strftime("%Y-%m-%d"),
                "gasoline_92": price.gasoline_92,
                "gasoline_95": price.gasoline_95,
                "diesel_0": price.diesel_0,
                "source": price.source,
                "collected_at": price.collected_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return json.dumps(data, ensure_ascii=False, indent=2)


# 创建收集器实例
real_collector = RealOilPriceCollector()