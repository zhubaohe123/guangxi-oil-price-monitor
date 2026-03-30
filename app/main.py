"""
主应用入口
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.database import init_db, get_session
from app.routers import oil_prices, analysis, charts, news
from app.scheduler import init_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    
    # 初始化数据库
    await init_db()
    logger.info("数据库初始化完成")
    
    # 初始化调度器
    scheduler = init_scheduler()
    scheduler.start()
    logger.info("任务调度器启动完成")
    
    yield
    
    # 关闭时
    scheduler.shutdown()
    logger.info("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(oil_prices.router, prefix="/api/oil-prices", tags=["油价数据"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["分析推荐"])
app.include_router(charts.router, prefix="/api/charts", tags=["图表可视化"])
app.include_router(news.router, prefix="/api/news", tags=["新闻资讯"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        async with get_session() as session:
            await session.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2026-03-30T14:44:00Z"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务不可用")


@app.get("/api/regions")
async def get_regions():
    """获取广西地区列表"""
    return {
        "regions": settings.guangxi_regions,
        "count": len(settings.guangxi_regions)
    }


@app.get("/api/config")
async def get_config():
    """获取应用配置（不含敏感信息）"""
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "guangxi_regions": settings.guangxi_regions,
        "collection_schedule": settings.collection_schedule,
        "analysis_schedule": settings.analysis_schedule,
        "chart_theme": settings.chart_theme
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )