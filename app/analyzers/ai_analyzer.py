"""
AI油价分析器
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import openai
from sqlalchemy import select, desc

from app.config import settings
from app.database.models import OilPrice, NewsArticle, AnalysisResult
from app.database import get_session

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI油价分析器"""
    
    def __init__(self):
        # 配置OpenAI客户端
        self.client = openai.OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        
    async def analyze_daily_prices(self) -> Optional[AnalysisResult]:
        """分析当日油价数据"""
        logger.info("开始AI分析当日油价")
        
        try:
            # 获取当日油价数据
            today = date.today()
            async with get_session() as session:
                # 获取当日所有地区油价
                stmt = select(OilPrice).where(OilPrice.date == today)
                result = await session.execute(stmt)
                today_prices = result.scalars().all()
                
                if not today_prices:
                    logger.warning("当日无油价数据可供分析")
                    return None
                
                # 获取近期油价趋势（最近7天）
                week_ago = today - timedelta(days=7)
                stmt = select(OilPrice).where(
                    OilPrice.date >= week_ago
                ).order_by(OilPrice.date, OilPrice.region)
                result = await session.execute(stmt)
                recent_prices = result.scalars().all()
                
                # 获取相关新闻
                stmt = select(NewsArticle).where(
                    NewsArticle.published_at >= week_ago
                ).order_by(desc(NewsArticle.published_at)).limit(10)
                result = await session.execute(stmt)
                recent_news = result.scalars().all()
            
            # 准备分析数据
            analysis_data = self._prepare_analysis_data(
                today_prices, recent_prices, recent_news
            )
            
            # 调用AI进行分析
            analysis_result = await self._call_ai_analysis(analysis_data)
            
            # 保存分析结果
            analysis_record = AnalysisResult(
                analysis_date=today,
                analysis_type="daily",
                summary=analysis_result.get("summary", ""),
                trend_analysis=analysis_result.get("trend_analysis", ""),
                recommendation=analysis_result.get("recommendation", ""),
                confidence_score=analysis_result.get("confidence_score", 0.0),
                raw_data=analysis_data,
                created_at=datetime.now()
            )
            
            async with get_session() as session:
                session.add(analysis_record)
                await session.commit()
            
            logger.info("AI分析完成")
            return analysis_record
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return None
    
    def _prepare_analysis_data(self, today_prices: List[OilPrice], 
                              recent_prices: List[OilPrice],
                              recent_news: List[NewsArticle]) -> Dict[str, Any]:
        """准备分析数据"""
        
        # 计算今日平均价格
        avg_92 = sum(p.gasoline_92 for p in today_prices) / len(today_prices)
        avg_95 = sum(p.gasoline_95 for p in today_prices) / len(today_prices)
        avg_diesel = sum(p.diesel_0 for p in today_prices) / len(today_prices)
        
        # 按地区分组
        regions_data = {}
        for price in today_prices:
            regions_data[price.region] = {
                "92号汽油": price.gasoline_92,
                "95号汽油": price.gasoline_95,
                "0号柴油": price.diesel_0
            }
        
        # 计算价格变化
        price_changes = self._calculate_price_changes(recent_prices)
        
        # 准备新闻摘要
        news_summary = []
        for news in recent_news[:5]:  # 取最近5条新闻
            news_summary.append({
                "title": news.title,
                "summary": news.summary[:100] + "..." if len(news.summary) > 100 else news.summary,
                "source": news.source,
                "date": news.published_at.strftime("%Y-%m-%d")
            })
        
        return {
            "analysis_date": date.today().strftime("%Y-%m-%d"),
            "regions_count": len(today_prices),
            "average_prices": {
                "92号汽油": round(avg_92, 2),
                "95号汽油": round(avg_95, 2),
                "0号柴油": round(avg_diesel, 2)
            },
            "regions_data": regions_data,
            "price_changes": price_changes,
            "recent_news": news_summary,
            "analysis_context": "广西地区油价分析与加油推荐"
        }
    
    def _calculate_price_changes(self, recent_prices: List[OilPrice]) -> Dict[str, Any]:
        """计算价格变化"""
        if len(recent_prices) < 2:
            return {}
        
        # 按日期分组
        prices_by_date = {}
        for price in recent_prices:
            date_str = price.date.strftime("%Y-%m-%d")
            if date_str not in prices_by_date:
                prices_by_date[date_str] = []
            prices_by_date[date_str].append(price)
        
        # 计算每日平均价格
        daily_avgs = {}
        for date_str, prices in prices_by_date.items():
            avg_92 = sum(p.gasoline_92 for p in prices) / len(prices)
            avg_95 = sum(p.gasoline_95 for p in prices) / len(prices)
            avg_diesel = sum(p.diesel_0 for p in prices) / len(prices)
            daily_avgs[date_str] = {
                "92号汽油": round(avg_92, 2),
                "95号汽油": round(avg_95, 2),
                "0号柴油": round(avg_diesel, 2)
            }
        
        # 排序日期
        sorted_dates = sorted(daily_avgs.keys())
        
        if len(sorted_dates) >= 2:
            latest = sorted_dates[-1]
            previous = sorted_dates[-2]
            
            latest_prices = daily_avgs[latest]
            previous_prices = daily_avgs[previous]
            
            changes = {}
            for fuel_type in ["92号汽油", "95号汽油", "0号柴油"]:
                change = latest_prices[fuel_type] - previous_prices[fuel_type]
                percent = (change / previous_prices[fuel_type]) * 100 if previous_prices[fuel_type] > 0 else 0
                changes[fuel_type] = {
                    "change": round(change, 2),
                    "percent": round(percent, 2),
                    "direction": "上涨" if change > 0 else "下跌" if change < 0 else "持平"
                }
            
            return {
                "latest_date": latest,
                "previous_date": previous,
                "changes": changes
            }
        
        return {}
    
    async def _call_ai_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用AI进行分析"""
        
        prompt = self._build_analysis_prompt(analysis_data)
        
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的油价分析师，擅长分析油价趋势并提供加油建议。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            
            # 解析AI回复
            return self._parse_ai_response(analysis_text, analysis_data)
            
        except Exception as e:
            logger.error(f"AI调用失败: {e}")
            # 返回默认分析
            return self._get_default_analysis(analysis_data)
    
    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """构建分析提示词"""
        
        prompt = f"""
        请分析以下广西地区油价数据，并提供专业的加油建议：

        分析日期：{data['analysis_date']}
        分析地区数量：{data['regions_count']}个

        今日平均油价（元/升）：
        - 92号汽油：{data['average_prices']['92号汽油']}
        - 95号汽油：{data['average_prices']['95号汽油']}
        - 0号柴油：{data['average_prices']['0号柴油']}

        各地区油价详情：
        {self._format_regions_data(data['regions_data'])}

        价格变化趋势：
        {self._format_price_changes(data.get('price_changes', {}))}

        相关新闻摘要：
        {self._format_news_summary(data['recent_news'])}

        请提供以下分析：
        1. 今日油价总体评价
        2. 价格趋势分析（上涨/下跌/持平）
        3. 各地区价格差异分析
        4. 基于新闻和市场因素的分析
        5. 加油建议：今日是否适合加油？如果适合，推荐加哪种油？何时加最划算？
        6. 未来几天油价预测

        请用中文回复，保持专业但易懂。
        """
        
        return prompt
    
    def _format_regions_data(self, regions_data: Dict[str, Dict]) -> str:
        """格式化地区数据"""
        lines = []
        for region, prices in regions_data.items():
            lines.append(f"- {region}: 92号{ prices['92号汽油']}元, 95号{ prices['95号汽油']}元, 0号柴油{ prices['0号柴油']}元")
        return "\n".join(lines)
    
    def _format_price_changes(self, changes: Dict[str, Any]) -> str:
        """格式化价格变化"""
        if not changes:
            return "无近期价格变化数据"
        
        text = f"最新日期：{changes.get('latest_date', 'N/A')}\n"
        text += f"对比日期：{changes.get('previous_date', 'N/A')}\n"
        
        for fuel_type, change_info in changes.get('changes', {}).items():
            direction = change_info.get('direction', '')
            percent = change_info.get('percent', 0)
            text += f"- {fuel_type}: {direction} {abs(percent)}%\n"
        
        return text
    
    def _format_news_summary(self, news: List[Dict]) -> str:
        """格式化新闻摘要"""
        if not news:
            return "无相关新闻"
        
        lines = []
        for item in news:
            lines.append(f"- {item['date']} {item['source']}: {item['title']} - {item['summary']}")
        return "\n".join(lines)
    
    def _parse_ai_response(self, response: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI回复"""
        # 这里可以添加更复杂的解析逻辑
        # 目前简单返回
        
        return {
            "summary": response[:500] + "..." if len(response) > 500 else response,
            "trend_analysis": "AI分析趋势",
            "recommendation": "基于AI分析的加油建议",
            "confidence_score": 0.85,
            "raw_response": response
        }
    
    def _get_default_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认分析（AI失败时使用）"""
        
        avg_92 = data['average_prices']['92号汽油']
        
        # 简单逻辑判断
        if avg_92 > 7.90:
            recommendation = "油价较高，建议非必要不加油，等待价格回落"
        elif avg_92 < 7.70:
            recommendation = "油价较低，适合加油，建议今日加满"
        else:
            recommendation = "油价适中，可根据需要加油"
        
        return {
            "summary": f"今日广西平均油价：92号{avg_92}元/升，价格处于中等水平。",
            "trend_analysis": "基于近期数据，油价相对稳定。",
            "recommendation": recommendation,
            "confidence_score": 0.6
        }
    
    async def get_today_recommendation(self) -> Dict[str, Any]:
        """获取今日加油推荐"""
        today = date.today()
        
        async with get_session() as session:
            stmt = select(AnalysisResult).where(
                AnalysisResult.analysis_date == today,
                AnalysisResult.analysis_type == "daily"
            ).order_by(desc(AnalysisResult.created_at))
            
            result = await session.execute(stmt)
            latest_analysis = result.scalar()
        
        if latest_analysis:
            return {
                "date": today.strftime("%Y-%m-%d"),
                "summary": latest_analysis.summary,
                "recommendation": latest_analysis.recommendation,
                "confidence": latest_analysis.confidence_score,
                "analysis_time": latest_analysis.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            # 如果没有今日分析，立即进行分析
            analysis = await self.analyze_daily_prices()
            if analysis:
                return {
                    "date": today.strftime("%Y-%m-%d"),
                    "summary": analysis.summary,
                    "recommendation": analysis.recommendation,
                    "confidence": analysis.confidence_score,
                    "analysis_time": analysis.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
        
        return {
            "date": today.strftime("%Y-%m-%d"),
            "summary": "暂无分析数据",
            "recommendation": "请等待系统分析完成",
            "confidence": 0.0,
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# 创建分析器实例
analyzer = AIAnalyzer()