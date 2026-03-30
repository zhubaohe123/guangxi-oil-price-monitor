"""
简化油价路由 - 先确保能导入
"""
from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import List, Optional

from app.config_simple import settings
from app.database_sync import get_session
from app.database.models import OilPrice

router = APIRouter(prefix="/api/oil-prices", tags=["oil-prices"])


@router.get("/today")
async def get_today_prices():
    """获取今日油价"""
    try:
        with get_session() as session:
            # 简单返回测试数据
            return {
                "date": date.today().isoformat(),
                "regions": settings.guangxi_regions,
                "status": "数据收集功能正常",
                "note": "这是简化版本，完整功能需要配置数据源"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取油价数据失败: {str(e)}")


@router.get("/health")
async def oil_prices_health():
    """油价模块健康检查"""
    return {
        "status": "healthy",
        "module": "oil-prices",
        "regions_count": len(settings.guangxi_regions)
    }