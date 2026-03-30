"""
油价数据API路由
"""
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.database.models import OilPrice
from app.collectors.real_oil_price_collector import real_collector

router = APIRouter()


@router.get("/today")
async def get_today_prices(
    session: AsyncSession = Depends(get_session)
):
    """获取今日油价数据"""
    try:
        today = date.today()
        
        stmt = select(OilPrice).where(
            OilPrice.date == today
        ).order_by(OilPrice.region)
        
        result = await session.execute(stmt)
        prices = result.scalars().all()
        
        if not prices:
            return {
                "date": today.isoformat(),
                "message": "今日暂无油价数据",
                "prices": [],
                "count": 0
            }
        
        # 计算平均价格
        avg_92 = sum(p.gasoline_92 for p in prices) / len(prices)
        avg_95 = sum(p.gasoline_95 for p in prices) / len(prices)
        avg_diesel = sum(p.diesel_0 for p in prices) / len(prices)
        
        return {
            "date": today.isoformat(),
            "average_prices": {
                "gasoline_92": round(avg_92, 2),
                "gasoline_95": round(avg_95, 2),
                "diesel_0": round(avg_diesel, 2)
            },
            "regions_count": len(prices),
            "prices": [
                {
                    "region": p.region,
                    "gasoline_92": p.gasoline_92,
                    "gasoline_95": p.gasoline_95,
                    "diesel_0": p.diesel_0,
                    "source": p.source,
                    "collected_at": p.collected_at.isoformat() if p.collected_at else None
                }
                for p in prices
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取今日油价失败: {str(e)}")


@router.get("/history")
async def get_history_prices(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    region: Optional[str] = Query(None, description="地区名称"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    session: AsyncSession = Depends(get_session)
):
    """获取历史油价数据"""
    try:
        # 设置默认日期范围（最近30天）
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 构建查询
        stmt = select(OilPrice).where(
            OilPrice.date >= start_date,
            OilPrice.date <= end_date
        )
        
        if region:
            stmt = stmt.where(OilPrice.region == region)
        
        stmt = stmt.order_by(desc(OilPrice.date), OilPrice.region).limit(limit)
        
        result = await session.execute(stmt)
        prices = result.scalars().all()
        
        # 按日期分组
        prices_by_date = {}
        for price in prices:
            date_str = price.date.isoformat()
            if date_str not in prices_by_date:
                prices_by_date[date_str] = []
            prices_by_date[date_str].append({
                "region": price.region,
                "gasoline_92": price.gasoline_92,
                "gasoline_95": price.gasoline_95,
                "diesel_0": price.diesel_0,
                "source": price.source
            })
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "region": region,
            "total_records": len(prices),
            "dates_count": len(prices_by_date),
            "prices_by_date": prices_by_date
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史油价失败: {str(e)}")


@router.get("/regions")
async def get_regions_list(
    session: AsyncSession = Depends(get_session)
):
    """获取所有地区列表"""
    try:
        stmt = select(OilPrice.region).distinct().order_by(OilPrice.region)
        result = await session.execute(stmt)
        regions = [row[0] for row in result.fetchall()]
        
        return {
            "regions": regions,
            "count": len(regions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地区列表失败: {str(e)}")


@router.get("/region/{region_name}")
async def get_region_prices(
    region_name: str,
    days: int = Query(30, ge=1, le=365, description="天数"),
    session: AsyncSession = Depends(get_session)
):
    """获取特定地区的油价历史"""
    try:
        start_date = date.today() - timedelta(days=days)
        
        stmt = select(OilPrice).where(
            OilPrice.region == region_name,
            OilPrice.date >= start_date
        ).order_by(OilPrice.date)
        
        result = await session.execute(stmt)
        prices = result.scalars().all()
        
        if not prices:
            raise HTTPException(
                status_code=404,
                detail=f"未找到地区 '{region_name}' 的油价数据"
            )
        
        # 计算价格变化
        price_changes = []
        for i in range(1, len(prices)):
            prev = prices[i-1]
            curr = prices[i]
            
            change_92 = curr.gasoline_92 - prev.gasoline_92
            change_95 = curr.gasoline_95 - prev.gasoline_95
            change_diesel = curr.diesel_0 - prev.diesel_0
            
            price_changes.append({
                "date": curr.date.isoformat(),
                "changes": {
                    "gasoline_92": {
                        "value": change_92,
                        "percent": (change_92 / prev.gasoline_92 * 100) if prev.gasoline_92 > 0 else 0
                    },
                    "gasoline_95": {
                        "value": change_95,
                        "percent": (change_95 / prev.gasoline_95 * 100) if prev.gasoline_95 > 0 else 0
                    },
                    "diesel_0": {
                        "value": change_diesel,
                        "percent": (change_diesel / prev.diesel_0 * 100) if prev.diesel_0 > 0 else 0
                    }
                }
            })
        
        return {
            "region": region_name,
            "days": days,
            "total_records": len(prices),
            "prices": [
                {
                    "date": p.date.isoformat(),
                    "gasoline_92": p.gasoline_92,
                    "gasoline_95": p.gasoline_95,
                    "diesel_0": p.diesel_0,
                    "source": p.source
                }
                for p in prices
            ],
            "price_changes": price_changes[-10:] if price_changes else []  # 返回最近10次变化
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地区油价失败: {str(e)}")


@router.get("/stats")
async def get_price_statistics(
    session: AsyncSession = Depends(get_session)
):
    """获取油价统计信息"""
    try:
        # 获取最新价格
        stmt = select(OilPrice).order_by(desc(OilPrice.date)).limit(1)
        result = await session.execute(stmt)
        latest = result.scalar()
        
        if not latest:
            return {
                "message": "暂无油价数据",
                "stats": {}
            }
        
        # 计算各油品价格范围
        stmt_92 = select(
            func.min(OilPrice.gasoline_92).label("min"),
            func.max(OilPrice.gasoline_92).label("max"),
            func.avg(OilPrice.gasoline_92).label("avg")
        ).where(OilPrice.date == latest.date)
        
        stmt_95 = select(
            func.min(OilPrice.gasoline_95).label("min"),
            func.max(OilPrice.gasoline_95).label("max"),
            func.avg(OilPrice.gasoline_95).label("avg")
        ).where(OilPrice.date == latest.date)
        
        stmt_diesel = select(
            func.min(OilPrice.diesel_0).label("min"),
            func.max(OilPrice.diesel_0).label("max"),
            func.avg(OilPrice.diesel_0).label("avg")
        ).where(OilPrice.date == latest.date)
        
        result_92 = await session.execute(stmt_92)
        result_95 = await session.execute(stmt_95)
        result_diesel = await session.execute(stmt_diesel)
        
        stats_92 = result_92.fetchone()
        stats_95 = result_95.fetchone()
        stats_diesel = result_diesel.fetchone()
        
        # 获取地区数量
        stmt_regions = select(func.count(func.distinct(OilPrice.region))).where(
            OilPrice.date == latest.date
        )
        result_regions = await session.execute(stmt_regions)
        regions_count = result_regions.scalar() or 0
        
        return {
            "date": latest.date.isoformat(),
            "regions_count": regions_count,
            "statistics": {
                "gasoline_92": {
                    "min": round(stats_92.min, 2) if stats_92.min else 0,
                    "max": round(stats_92.max, 2) if stats_92.max else 0,
                    "average": round(stats_92.avg, 2) if stats_92.avg else 0,
                    "range": round((stats_92.max - stats_92.min), 2) if stats_92.max and stats_92.min else 0
                },
                "gasoline_95": {
                    "min": round(stats_95.min, 2) if stats_95.min else 0,
                    "max": round(stats_95.max, 2) if stats_95.max else 0,
                    "average": round(stats_95.avg, 2) if stats_95.avg else 0,
                    "range": round((stats_95.max - stats_95.min), 2) if stats_95.max and stats_95.min else 0
                },
                "diesel_0": {
                    "min": round(stats_diesel.min, 2) if stats_diesel.min else 0,
                    "max": round(stats_diesel.max, 2) if stats_diesel.max else 0,
                    "average": round(stats_diesel.avg, 2) if stats_diesel.avg else 0,
                    "range": round((stats_diesel.max - stats_diesel.min), 2) if stats_diesel.max and stats_diesel.min else 0
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/collect")
async def trigger_collection():
    """手动触发油价数据收集"""
    try:
        # 使用真实数据收集器
        prices = await real_collector.collect_all_regions_real()
        
        return {
            "success": True,
            "message": f"成功收集 {len(prices)} 条油价数据",
            "collected_at": date.today().isoformat(),
            "regions": [p.region for p in prices] if prices else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据收集失败: {str(e)}")


@router.get("/export")
async def export_prices(
    format: str = Query("csv", regex="^(csv|json)$"),
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session)
):
    """导出油价数据"""
    try:
        start_date = date.today() - timedelta(days=days)
        
        stmt = select(OilPrice).where(
            OilPrice.date >= start_date
        ).order_by(OilPrice.date, OilPrice.region)
        
        result = await session.execute(stmt)
        prices = result.scalars().all()
        
        if not prices:
            raise HTTPException(status_code=404, detail="指定时间段内无油价数据")
        
        # 使用收集器的导出功能
        if format == "csv":
            content = real_collector.export_data(prices, "csv")
            media_type = "text/csv"
            filename = f"oil_prices_{start_date}_{date.today()}.csv"
        else:
            content = real_collector.export_data(prices, "json")
            media_type = "application/json"
            filename = f"oil_prices_{start_date}_{date.today()}.json"
        
        return {
            "filename": filename,
            "content": content,
            "format": format,
            "records": len(prices),
            "date_range": f"{start_date} 至 {date.today()}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")


@router.get("/compare")
async def compare_prices(
    date1: date = Query(..., description="第一个日期"),
    date2: date = Query(..., description="第二个日期"),
    session: AsyncSession = Depends(get_session)
):
    """比较两个日期的油价"""
    try:
        # 获取第一个日期的数据
        stmt1 = select(OilPrice).where(OilPrice.date == date1)
        result1 = await session.execute(stmt1)
        prices1 = {p.region: p for p in result1.scalars().all()}
        
        # 获取第二个日期的数据
        stmt2 = select(OilPrice).where(OilPrice.date == date2)
        result2 = await session.execute(stmt2)
        prices2 = {p.region: p for p in result2.scalars().all()}
        
        # 找出两个日期都有的地区
        common_regions = set(prices1.keys()) & set(prices2.keys())
        
        if not common_regions:
            raise HTTPException(
                status_code=404,
                detail=f"日期 {date1} 和 {date2} 没有共同的地区数据"
            )
        
        # 计算比较结果
        comparisons = []
        for region in sorted(common_regions):
            p1 = prices1[region]
            p2 = prices2[region]
            
            comparisons.append({
                "region": region,
                "gasoline_92": {
                    "date1": p1.gasoline_92,
                    "date2": p2.gasoline_92,
                    "change": p2.gasoline_92 - p1.gasoline_92,
                    "percent": ((p2.gasoline_92 - p1.gasoline_92) / p1.gasoline_92 * 100) if p1.gasoline_92 > 0 else 0
                },
                "gasoline_95": {
                    "date1": p1.gasoline_95,
                    "date2": p2.gasoline_95,
                    "change": p2.gasoline_95 - p1.gasoline_95,
                    "percent": ((p2.gasoline_95 - p1.gasoline_95) / p1.gasoline_95 * 100) if p1.gasoline_95 > 0 else 0
                },
                "diesel_0": {
                    "date1": p1.diesel_0,
                    "date2": p2.diesel_0,
                    "change": p2.diesel_0 - p1.diesel_0,
                    "percent": ((p2.diesel_0 - p1.diesel_0) / p1.diesel_0 * 100) if p1.diesel_0 > 0 else 0
                }
            })
        
        # 计算总体变化
        total_changes = {
            "gasoline_92": {
                "average_change": sum(c["gasoline_92"]["change"] for c in comparisons) / len(comparisons),
                "regions_up": sum(1 for c in comparisons if c["gasoline_92"]["change"] > 0),
                "regions_down": sum(1 for c in comparisons if c["gasoline_92"]["change"] < 0),
                "regions_unchanged": sum(1 for c in comparisons if c["gasoline_92"]["change"] == 0)
            },
            "gasoline_95": {
                "average_change": sum(c["gasoline_95"]["change"] for c in comparisons) / len(comparisons),
                "regions_up": sum(1 for c in comparisons if c["gasoline_95"]["change"] > 0),
                "regions_down": sum(1 for c in comparisons if c["gasoline_95"]["change"] < 0),
                "regions_unchanged": sum(1 for c in comparisons if c["gasoline_95"]["change"] == 0)
            },
            "diesel_0": {
                "average_change": sum(c["diesel_0"]["change"] for c in comparisons) / len(comparisons),
                "regions_up": sum(1 for c in comparisons if c["diesel_0"]["change"] > 0),
                "regions_down": sum(1 for c in comparisons if c["diesel_0"]["change"] < 0),
                "regions_unchanged": sum(1 for c in comparisons if c["diesel_0"]["change"] == 0)
            }
        }
        
        # 判断总体趋势
        avg_change_92 = total_changes["gasoline_92"]["average_change"]
        if avg_change_92 > 0.01:
            overall_trend = "上涨"
        elif avg_change_92 < -0.01:
            overall_trend = "下跌"
        else:
            overall_trend = "持平"
        
        return {
            "date1": date1.isoformat(),
            "date2": date2.isoformat(),
            "common_regions": len(common_regions),
            "comparisons": comparisons,
            "summary": total_changes,
            "overall_trend": overall_trend,
            "trend_description": f"从{date1}到{date2}，广西油价总体{overall_trend}，92号汽油平均{('上涨' if avg_change_92 > 0 else '下跌' if avg_change_92 < 0 else '持平')}{abs(avg_change_92):.2f}元/升"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"比较油价失败: {str(e)}")


@router.get("/sources")
async def get_data_sources():
    """获取数据源信息"""
    try:
        from app.config_simple import settings
        
        sources = []
        
        for source in settings.oil_price_sources:
            if source.get("enabled", True):
                sources.append({
                    "name": source["name"],
                    "type": source["type"],
                    "url": source["url"],
                    "parser": source.get("parser", ""),
                    "region": source.get("region", ""),
                    "status": "可用" if source.get("enabled", True) else "禁用"
                })
        
        return {
            "total_sources": len(sources),
            "sources": sources,
            "last_updated": date.today().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源信息失败: {str(e)}")
            "days": days,
            "total_records": len(prices),
            "prices": [
                {
                    "date": p.date.isoformat(),
                    "gasoline_92": p.gasoline_92,
                    "gasoline_95": p.gasoline_95,
                    "diesel_0": p.diesel_0,
                    "source": p.source
                }
                for p in prices
            ],
            "price_changes": price_changes[-10:] if price_changes else []  # 返回最近10次变化
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地区油价失败: {str(e)}")


@router.get("/stats")
async def get_price_statistics(
    session: AsyncSession = Depends(get_session)
):
    """获取油价统计信息"""
    try:
        # 获取最新价格
        stmt = select(OilPrice).order_by(desc(OilPrice.date)).limit(1)
        result = await session.execute(stmt)
        latest = result.scalar()
        
        if not latest:
            return {
                "message": "暂无油价数据",
                "stats": {}
            }
        
        # 计算各油品价格范围
        stmt_92 = select(
            func.min(OilPrice.gasoline_92).label("min"),
            func.max(OilPrice.gasoline_92).label("max"),
            func.avg(OilPrice.gasoline_92).label("avg")
        ).where(OilPrice.date == latest.date)
        
        stmt_95 = select(
            func.min(OilPrice.gasoline_95).label("min"),
            func.max(OilPrice.gasoline_95).label("max"),
            func.avg(OilPrice.gasoline_95).label("avg")
        ).where(OilPrice.date == latest.date)
        
        stmt_diesel = select(
            func.min(OilPrice.diesel_0).label("min"),
            func.max(OilPrice.diesel_0).label("max"),
            func.avg(OilPrice.diesel_0).label("avg")
        ).where(OilPrice.date == latest.date)
        
        result_92 = await session.execute(stmt_92)
        result_95 = await session.execute(stmt_95)
        result_diesel = await session.execute(stmt_diesel)
        
        stats_92 = result_92.fetchone()
        stats_95 = result_95.fetchone()
        stats_diesel = result_diesel.fetchone()
        
        # 获取地区数量
        stmt_regions = select(func.count(func.distinct(OilPrice.region))).where(
            OilPrice.date == latest.date
        )
        result_regions = await session.execute(stmt_regions)
        regions_count = result_regions.scalar() or 0
        
        return {
            "date": latest.date.isoformat(),
            "regions_count": regions_count,
            "statistics": {
                "gasoline_92": {
                    "min": round(stats_92.min, 2) if stats_92.min else 0,
                    "max": round(stats_92.max, 2) if stats_92.max else 0,
                    "average": round(stats_92.avg, 2) if stats_92.avg else 0,
                    "range": round((stats_92.max - stats_92.min), 2) if stats_92.max and stats_92.min else 0
                },
                "gasoline_95": {
                    "min": round(stats_95.min, 2) if stats_95.min else 0,
                    "max": round(stats_95.max, 2) if stats_95.max else 0,
                    "average": round(stats_95.avg, 2) if stats_95.avg else 0,
                    "range": round((stats_95.max - stats_95.min), 2) if stats_95.max and stats_95.min else 0
                },
                "diesel_0": {
                    "min": round(stats_diesel.min, 2) if stats_diesel.min else 0,
                    "max": round(stats_diesel.max, 2) if stats_diesel.max else 0,
                    "average": round(stats_diesel.avg, 2) if stats_diesel.avg else 0,
                    "range": round((stats_diesel.max - stats_diesel.min), 2) if stats_diesel.max and stats_diesel.min else 0
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/collect")
async def trigger_collection():
    """手动触发油价数据收集"""
    try:
        # 使用真实数据收集器
        prices = await real_collector.collect_all_regions_real()
        
        return {
            "success": True,
            "message": f"成功收集 {len(prices)} 条油价数据",
            "collected_at": date.today().isoformat(),
            "regions": [p.region for p in prices] if prices else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据收集失败: {str(e)}")


@router.get("/export")
async def export_prices(
    format: str = Query("csv", regex="^(csv|json)$"),
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session)
):
    """导出油价数据"""
    try:
        start_date = date.today() - timedelta(days=days)
        
        stmt = select(OilPrice).where(
            OilPrice.date >= start_date
        ).order_by(OilPrice.date, OilPrice.region)
        
        result = await session.execute(stmt)
        prices = result.scalars().all()
        
        if not prices:
            raise HTTPException(status_code=404, detail="指定时间段内无油价数据")
        
        # 使用收集器的导出功能
        if format == "csv":
            content = real_collector.export_data(prices, "csv")
            media_type = "text/csv"
            filename = f"oil_prices_{start_date}_{date.today()}.csv"
        else:
            content = real_collector.export_data(prices, "json")
            media_type = "application/json"
            filename = f"oil_prices_{start_date}_{date.today()}.json"
        
        return {
            "filename": filename,
            "content": content,
            "format": format,
            "records": len(prices),
            "date_range": f"{start_date} 至 {date.today()}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")


@router.get("/compare")
async def compare_prices(
    date1: date = Query(..., description="第一个日期"),
    date2: date = Query(..., description="第二个日期"),
    session: AsyncSession = Depends(get_session)
):
    """比较两个日期的油价"""
    try:
        # 获取第一个日期的数据
        stmt1 = select(OilPrice).where(OilPrice.date == date1)
        result1 = await session.execute(stmt1)
        prices1 = {p.region: p for p in result1.scalars().all()}
        
        # 获取第二个日期的数据
        stmt2 = select(OilPrice).where(OilPrice.date == date2)
        result2 = await session.execute(stmt2)
        prices2 = {p.region: p for p in result2.scalars().all()}
        
        # 找出两个日期都有的地区
        common_regions = set(prices1.keys()) & set(prices2.keys())
        
        if not common_regions:
            raise HTTPException(
                status_code=404,
                detail=f"日期 {date1} 和 {date2} 没有共同的地区数据"
            )
        
        # 计算比较结果
        comparisons = []
        for region in sorted(common_regions):
            p1 = prices1[region]
            p2 = prices2[region]
            
            comparisons.append({
                "region": region,
                "gasoline_92": {
                    "date1": p1.gasoline_92,
                    "date2": p2.gasoline_92,
                    "change": p2.gasoline_92 - p1.gasoline_92,
                    "percent": ((p2.gasoline_92 - p1.gasoline_92) / p1.gasoline_92 * 100) if p1.gasoline_92 > 0 else 0
                },
                "gasoline_95": {
                    "date1": p1.gasoline_95,
                    "date2": p2.gasoline_95,
                    "change": p2.gasoline_95 - p1.gasoline_95,
                    "percent": ((p2.gasoline_95 - p1.gasoline_95) / p1.gasoline_95 * 100) if p1.gasoline_95 > 0 else 0
                },
                "diesel_0": {
                    "date1": p1.diesel_0,
                    "date2": p2.diesel_0,
                    "change": p2.diesel_0 - p1.diesel_0,
                    "percent": ((p2.diesel_0 - p1.diesel_0) / p1.diesel_0 * 100) if p1.diesel_0 > 0 else 0
                }
            })
        
        # 计算总体变化
        total_changes = {
            "gasoline_92": {
                "average_change": sum(c["gasoline_92"]["change"] for c in comparisons) / len(comparisons),
                "regions_up": sum(1 for c in comparisons if c["gasoline_92"]["change"] > 0),
                "regions_down": sum(1 for c in comparisons if c["gasoline_92"]["change"] < 0),
                "regions_unchanged": sum(1 for c in comparisons if c["gasoline_92"]["change"] == 0)
            },
            "gasoline_95": {
                "average_change": sum(c["gasoline_95"]["change"] for c in comparisons) / len(comparisons),
                "regions_up": sum(1 for c in comparisons if c["gasoline_95"]["change"] > 0),
                "regions_down": sum(1 for c in comparisons if c["gasoline_95"]["change"] < 0),
                "regions_unchanged": sum(1 for c in comparisons if c["gasoline_95"]["change"] == 0)
            },
            "diesel_0": {
                "average_change": sum(c["diesel_0"]["change"] for c in comparisons) / len(comparisons),
                "regions_up": sum(1 for c in comparisons if c["diesel_0"]["change"] > 0),
                "regions_down": sum(1 for c in comparisons