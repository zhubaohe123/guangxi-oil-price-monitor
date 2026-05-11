"""
新闻资讯API路由 - 占位模块
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def news_index():
    """新闻资讯接口"""
    return {"message": "新闻资讯接口 - 待实现"}


@router.get("/latest")
async def get_latest_news():
    """获取最新新闻"""
    return {"message": "最新新闻 - 待实现", "data": []}
