"""
简化主应用 - 先确保能启动
"""
import logging
from fastapi import FastAPI
import uvicorn

from app.config_simple import settings
from app.database_sync import init_db
from app.routers.oil_prices_simple import router as oil_prices_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

# 注册路由
app.include_router(oil_prices_router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    
    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        # 继续启动，数据库可能已经存在


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
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


@app.get("/docs")
async def get_docs():
    """API文档重定向"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    # 直接运行
    uvicorn.run(
        "app.main_simple:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )