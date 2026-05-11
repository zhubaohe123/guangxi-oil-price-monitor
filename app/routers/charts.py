"""
图表可视化API路由 - 占位模块
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def charts_index():
    """图表接口"""
    return {"message": "图表可视化接口 - 待实现"}


@router.get("/trend")
async def get_trend_chart():
    """获取趋势图表"""
    return {"message": "趋势图表 - 待实现", "data": None}
