"""
图表生成器
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os

from app.config_simple import settings
from app.database.models import OilPrice
from app.database import get_session

logger = logging.getLogger(__name__)


class ChartGenerator:
    """图表生成器"""
    
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        self.colors = {
            'gasoline_92': '#FF6B6B',
            'gasoline_95': '#4ECDC4',
            'diesel_0': '#45B7D1',
            'region_avg': '#96CEB4'
        }
    
    async def generate_trend_chart(self, days: int = 30) -> Optional[str]:
        """生成油价趋势图"""
        logger.info(f"生成最近{days}天油价趋势图")
        
        try:
            # 获取数据
            start_date = date.today() - timedelta(days=days)
            
            async with get_session() as session:
                # 获取近期油价数据
                from sqlalchemy import select, func
                
                stmt = select(OilPrice).where(
                    OilPrice.date >= start_date
                ).order_by(OilPrice.date)
                
                result = await session.execute(stmt)
                prices = result.scalars().all()
            
            if not prices:
                logger.warning("无足够数据生成趋势图")
                return None
            
            # 转换为DataFrame
            data = []
            for price in prices:
                data.append({
                    'date': price.date,
                    'region': price.region,
                    'gasoline_92': price.gasoline_92,
                    'gasoline_95': price.gasoline_95,
                    'diesel_0': price.diesel_0
                })
            
            df = pd.DataFrame(data)
            
            # 计算每日平均价格
            daily_avg = df.groupby('date').agg({
                'gasoline_92': 'mean',
                'gasoline_95': 'mean',
                'diesel_0': 'mean'
            }).reset_index()
            
            # 创建Plotly图表
            fig = go.Figure()
            
            # 添加各油品趋势线
            fig.add_trace(go.Scatter(
                x=daily_avg['date'],
                y=daily_avg['gasoline_92'],
                mode='lines+markers',
                name='92号汽油',
                line=dict(color=self.colors['gasoline_92'], width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=daily_avg['date'],
                y=daily_avg['gasoline_95'],
                mode='lines+markers',
                name='95号汽油',
                line=dict(color=self.colors['gasoline_95'], width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=daily_avg['date'],
                y=daily_avg['diesel_0'],
                mode='lines+markers',
                name='0号柴油',
                line=dict(color=self.colors['diesel_0'], width=3),
                marker=dict(size=8)
            ))
            
            # 更新布局
            fig.update_layout(
                title=f'广西油价趋势图（最近{days}天）',
                xaxis_title='日期',
                yaxis_title='价格（元/升）',
                template=settings.chart_theme,
                width=settings.chart_width,
                height=settings.chart_height,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # 添加网格和样式
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='LightGray',
                tickangle=45
            )
            
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='LightGray'
            )
            
            # 保存图表
            filename = f"trend_chart_{date.today()}.html"
            filepath = os.path.join(settings.charts_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"趋势图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"生成趋势图失败: {e}")
            return None
    
    async def generate_calendar_heatmap(self, year: int = None, month: int = None) -> Optional[str]:
        """生成日历热力图"""
        logger.info("生成油价日历热力图")
        
        try:
            if year is None:
                year = date.today().year
            if month is None:
                month = date.today().month
            
            # 获取当月数据
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            async with get_session() as session:
                from sqlalchemy import select, func
                
                stmt = select(OilPrice).where(
                    OilPrice.date >= start_date,
                    OilPrice.date <= end_date
                )
                
                result = await session.execute(stmt)
                prices = result.scalars().all()
            
            if not prices:
                logger.warning("无足够数据生成日历热力图")
                return None
            
            # 准备数据
            data = []
            for price in prices:
                data.append({
                    'date': price.date,
                    'gasoline_92': price.gasoline_92,
                    'day': price.date.day,
                    'weekday': price.date.weekday()  # 0=周一, 6=周日
                })
            
            df = pd.DataFrame(data)
            
            # 按日期分组（去重）
            daily_prices = df.groupby('date').agg({
                'gasoline_92': 'mean',
                'day': 'first',
                'weekday': 'first'
            }).reset_index()
            
            # 创建日历数据
            calendar_data = []
            for _, row in daily_prices.iterrows():
                calendar_data.append({
                    'day': row['day'],
                    'weekday': row['weekday'],
                    'price': row['gasoline_92'],
                    'date_str': row['date'].strftime('%Y-%m-%d')
                })
            
            # 创建热力图数据矩阵
            days_in_month = (end_date - start_date).days + 1
            heatmap_data = np.full((7, 5), np.nan)  # 7天 x 最多5周
            
            for item in calendar_data:
                week_num = (item['day'] - 1) // 7
                heatmap_data[item['weekday'], week_num] = item['price']
            
            # 创建热力图
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=['第1周', '第2周', '第3周', '第4周', '第5周'],
                y=['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                colorscale='RdYlGn_r',  # 红色高，绿色低
                hoverongaps=False,
                colorbar=dict(title="92号汽油价格（元/升）"),
                text=[[f"{v:.2f}" if not np.isnan(v) else "" for v in row] for row in heatmap_data],
                texttemplate="%{text}",
                textfont={"size": 12}
            ))
            
            # 更新布局
            month_name = f"{year}年{month}月"
            fig.update_layout(
                title=f'{month_name}广西92号汽油价格日历热力图',
                template=settings.chart_theme,
                width=settings.chart_width,
                height=settings.chart_height,
                xaxis_nticks=5,
                yaxis_nticks=7
            )
            
            # 保存图表
            filename = f"calendar_heatmap_{year}_{month:02d}.html"
            filepath = os.path.join(settings.charts_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"日历热力图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"生成日历热力图失败: {e}")
            return None
    
    async def generate_regional_comparison_chart(self) -> Optional[str]:
        """生成地区油价对比图"""
        logger.info("生成地区油价对比图")
        
        try:
            today = date.today()
            
            async with get_session() as session:
                from sqlalchemy import select
                
                stmt = select(OilPrice).where(OilPrice.date == today)
                result = await session.execute(stmt)
                prices = result.scalars().all()
            
            if not prices:
                logger.warning("今日无油价数据")
                return None
            
            # 准备数据
            regions = []
            prices_92 = []
            prices_95 = []
            prices_diesel = []
            
            for price in prices:
                regions.append(price.region)
                prices_92.append(price.gasoline_92)
                prices_95.append(price.gasoline_95)
                prices_diesel.append(price.diesel_0)
            
            # 创建分组柱状图
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='92号汽油',
                x=regions,
                y=prices_92,
                marker_color=self.colors['gasoline_92']
            ))
            
            fig.add_trace(go.Bar(
                name='95号汽油',
                x=regions,
                y=prices_95,
                marker_color=self.colors['gasoline_95']
            ))
            
            fig.add_trace(go.Bar(
                name='0号柴油',
                x=regions,
                y=prices_diesel,
                marker_color=self.colors['diesel_0']
            ))
            
            # 更新布局
            fig.update_layout(
                title=f'{today.strftime("%Y年%m月%d日")}广西各地区油价对比',
                xaxis_title='地区',
                yaxis_title='价格（元/升）',
                template=settings.chart_theme,
                width=settings.chart_width,
                height=settings.chart_height,
                barmode='group',
                xaxis_tickangle=-45
            )
            
            # 保存图表
            filename = f"regional_comparison_{today}.html"
            filepath = os.path.join(settings.charts_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"地区对比图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"生成地区对比图失败: {e}")
            return None
    
    async def generate_price_distribution_chart(self) -> Optional[str]:
        """生成价格分布图"""
        logger.info("生成价格分布图")
        
        try:
            today = date.today()
            
            async with get_session() as session:
                from sqlalchemy import select
                
                stmt = select(OilPrice).where(OilPrice.date == today)
                result = await session.execute(stmt)
                prices = result.scalars().all()
            
            if not prices:
                logger.warning("今日无油价数据")
                return None
            
            # 提取价格数据
            prices_92 = [p.gasoline_92 for p in prices]
            prices_95 = [p.gasoline_95 for p in prices]
            prices_diesel = [p.diesel_0 for p in prices]
            
            # 创建箱线图
            fig = go.Figure()
            
            fig.add_trace(go.Box(
                y=prices_92,
                name='92号汽油',
                marker_color=self.colors['gasoline_92'],
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8
            ))
            
            fig.add_trace(go.Box(
                y=prices_95,
                name='95号汽油',
                marker_color=self.colors['gasoline_95'],
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8
            ))
            
            fig.add_trace(go.Box(
                y=prices_diesel,
                name='0号柴油',
                marker_color=self.colors['diesel_0'],
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8
            ))
            
            # 更新布局
            fig.update_layout(
                title=f'{today.strftime("%Y年%m月%d日")}广西油价分布',
                yaxis_title='价格（元/升）',
                template=settings.chart_theme,
                width=settings.chart_width,
                height=settings.chart_height,
                showlegend=True
            )
            
            # 保存图表
            filename = f"price_distribution_{today}.html"
            filepath = os.path.join(settings.charts_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"价格分布图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"生成价格分布图失败: {e}")
            return None
    
    def generate_matplotlib_chart(self, data: pd.DataFrame, chart_type: str = "line") -> Optional[str]:
        """使用Matplotlib生成静态图表（PNG格式）"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            if chart_type == "line":
                if 'gasoline_92' in data.columns:
                    ax.plot(data['date'], data['gasoline_92'], 
                           label='92号汽油', color=self.colors['gasoline_92'], linewidth=2)
                if 'gasoline_95' in data.columns:
                    ax.plot(data['date'], data['gasoline_95'], 
                           label='95号汽油', color=self.colors['gasoline_95'], linewidth=2)
                
                ax.set_xlabel('日期')
                ax.set_ylabel('价格（元/升）')
                ax.set_title('广西油价趋势图')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # 旋转x轴标签
                plt.xticks(rotation=45)
            
            elif chart_type == "bar":
                # 柱状图逻辑
                pass
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图片
            filename = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(settings.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"静态图表已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"生成Matplotlib图表失败: {e}")
            return None
    
    async def get_available_charts(self) -> List[Dict[str, Any]]:
        """获取可用的图表列表"""
        charts = []
        
        if os.path.exists(settings.charts_dir):
            for filename in os.listdir(settings.charts_dir):
                if filename.endswith('.html') or filename.endswith('.png'):
                    filepath = os.path.join(settings.charts_dir, filename)
                    stat = os.stat(filepath)
                    
                    charts.append({
                        'name': filename,
                        'path': filepath,
                        'type': 'html' if filename.endswith('.html') else 'image',
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        return sorted(charts, key=lambda x: x['created'], reverse=True)


# 创建图表生成器实例
chart_generator = ChartGenerator()