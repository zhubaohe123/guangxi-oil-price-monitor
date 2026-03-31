"""
带UI界面的主应用
"""
import os
import sys
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.config_simple import settings
    from app.database_sync import init_db
    from app.routers.oil_prices_simple import router as oil_prices_router
except ImportError:
    # 备用导入方式
    import config_simple
    settings = config_simple.settings
    import database_sync
    init_db = database_sync.init_db
    import routers.oil_prices_simple
    oil_prices_router = routers.oil_prices_simple.router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 注册路由
app.include_router(oil_prices_router)

# 创建静态目录（如果不存在）
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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


@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回UI界面"""
    ui_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simple_ui.html")
    if os.path.exists(ui_file):
        with open(ui_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        # 如果UI文件不存在，返回JSON
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "ui": "/ui",
            "docs": "/api/docs",
            "health": "/health",
            "api": "/api/oil-prices/today"
        }


@app.get("/ui", response_class=HTMLResponse)
async def ui_interface():
    """UI界面"""
    ui_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simple_ui.html")
    if os.path.exists(ui_file):
        with open(ui_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>UI界面文件未找到</h1><p>请检查simple_ui.html文件是否存在</p>")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "mode": "no-database",
        "timestamp": "2026-03-30T23:40:00Z"
    }


@app.get("/api")
async def api_root():
    """API根路径"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "health": "/health",
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "oil_prices": "/api/oil-prices/today",
            "ui": "/ui"
        }
    }


if __name__ == "__main__":
    # 直接运行
    uvicorn.run(
        "app.main_with_ui:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )