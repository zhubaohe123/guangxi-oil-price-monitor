"""
油价数据收集器
"""
import asyncio
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd

from app.config_simple import settings
from app.database.models import OilPrice
from app.database import get_session

logger = logging.getLogger(__name__)


class OilPriceCollector:
    """油价数据收集器"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def collect_all_regions(self) -> List[OilPrice]:
        """收集所有地区的油价数据"""
        logger.info("开始收集广西各地油价数据")
        
        oil_prices = []
        tasks = []
        
        for region in settings.guangxi_regions:
            task = asyncio.create_task(self.collect_region_price(region))
            tasks.append(task)
        
        # 并发收集所有地区数据
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for region, result in zip(settings.guangxi_regions, results):
            if isinstance(result, Exception):
                logger.error(f"收集{region}油价数据失败: {result}")
            elif result:
                oil_prices.append(result)
                logger.info(f"成功收集{region}油价数据")
        
        # 保存到数据库
        if oil_prices:
            await self.save_to_database(oil_prices)
        
        logger.info(f"油价数据收集完成，共收集{len(oil_prices)}个地区的数据")
        return oil_prices
    
    async def collect_region_price(self, region: str) -> Optional[OilPrice]:
        """收集单个地区的油价数据"""
        try:
            # 这里实现具体的数据收集逻辑
            # 实际项目中需要根据不同的数据源实现
            
            # 模拟数据（实际项目需要从网站抓取）
            price_data = await self._simulate_collection(region)
            
            if price_data:
                return OilPrice(
                    region=region,
                    date=date.today(),
                    gasoline_92=price_data.get("gasoline_92", 0),
                    gasoline_95=price_data.get("gasoline_95", 0),
                    diesel_0=price_data.get("diesel_0", 0),
                    source=price_data.get("source", "模拟数据"),
                    collected_at=datetime.now()
                )
            
        except Exception as e:
            logger.error(f"收集{region}油价数据异常: {e}")
            return None
    
    async def _simulate_collection(self, region: str) -> Dict[str, Any]:
        """模拟数据收集（实际项目需要替换为真实数据源）"""
        # 模拟不同地区的油价（元/升）
        base_prices = {
            "南宁": {"gasoline_92": 7.85, "gasoline_95": 8.45, "diesel_0": 7.52},
            "柳州": {"gasoline_92": 7.83, "gasoline_95": 8.43, "diesel_0": 7.50},
            "桂林": {"gasoline_92": 7.84, "gasoline_95": 8.44, "diesel_0": 7.51},
            "梧州": {"gasoline_92": 7.82, "gasoline_95": 8.42, "diesel_0": 7.49},
            "北海": {"gasoline_92": 7.86, "gasoline_95": 8.46, "diesel_0": 7.53},
        }
        
        # 添加随机波动
        import random
        if region in base_prices:
            prices = base_prices[region].copy()
            # 添加±0.05的随机波动
            for key in prices:
                prices[key] += random.uniform(-0.05, 0.05)
                prices[key] = round(prices[key], 2)
            prices["source"] = "模拟数据源"
            return prices
        
        # 默认价格
        return {
            "gasoline_92": round(7.80 + random.uniform(-0.1, 0.1), 2),
            "gasoline_95": round(8.40 + random.uniform(-0.1, 0.1), 2),
            "diesel_0": round(7.48 + random.uniform(-0.1, 0.1), 2),
            "source": "模拟数据源"
        }
    
    async def collect_from_website(self, url: str) -> Optional[Dict[str, Any]]:
        """从网站抓取油价数据"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 这里需要根据具体网站结构解析
                        # 示例：查找包含油价的表格或元素
                        price_elements = soup.find_all(class_="price")
                        
                        # 实际解析逻辑...
                        return None
                    else:
                        logger.error(f"请求失败: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"网站数据收集失败: {e}")
            return None
    
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
            await session.rollback()
    
    def export_to_csv(self, oil_prices: List[OilPrice], filename: str = None):
        """导出油价数据到CSV"""
        if not filename:
            filename = f"oil_prices_{date.today()}.csv"
        
        filepath = f"{settings.data_dir}/{filename}"
        
        # 转换为DataFrame
        data = []
        for price in oil_prices:
            data.append({
                "地区": price.region,
                "日期": price.date,
                "92号汽油": price.gasoline_92,
                "95号汽油": price.gasoline_95,
                "0号柴油": price.diesel_0,
                "数据源": price.source,
                "收集时间": price.collected_at
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"油价数据已导出到: {filepath}")
        
        return filepath


# 创建收集器实例
collector = OilPriceCollector()