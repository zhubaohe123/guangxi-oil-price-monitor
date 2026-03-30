"""
数据库模块初始化
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """初始化数据库"""
    logger.info("初始化数据库...")
    
    try:
        # 创建所有表
        async with engine.begin() as conn:
            # 对于SQLite，需要特殊处理
            if "sqlite" in settings.database_url:
                await conn.execute(text("PRAGMA foreign_keys = ON"))
                await conn.execute(text("PRAGMA journal_mode = WAL"))
            
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("数据库表创建完成")
        
        # 创建必要的索引
        await create_indexes()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def create_indexes():
    """创建数据库索引"""
    try:
        async with engine.begin() as conn:
            # 油价表索引
            indexes = [
                # OilPrice表索引
                "CREATE INDEX IF NOT EXISTS idx_oil_prices_region_date ON oil_prices(region, date)",
                "CREATE INDEX IF NOT EXISTS idx_oil_prices_date ON oil_prices(date)",
                "CREATE INDEX IF NOT EXISTS idx_oil_prices_region ON oil_prices(region)",
                
                # NewsArticle表索引
                "CREATE INDEX IF NOT EXISTS idx_news_articles_published ON news_articles(published_at)",
                "CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source)",
                "CREATE INDEX IF NOT EXISTS idx_news_articles_relevance ON news_articles(relevance_score)",
                
                # AnalysisResult表索引
                "CREATE INDEX IF NOT EXISTS idx_analysis_results_date ON analysis_results(analysis_date)",
                "CREATE INDEX IF NOT EXISTS idx_analysis_results_confidence ON analysis_results(confidence_score)",
                
                # ChartFile表索引
                "CREATE INDEX IF NOT EXISTS idx_chart_files_generated ON chart_files(generated_at)",
                "CREATE INDEX IF NOT EXISTS idx_chart_files_type ON chart_files(chart_type)",
                
                # UserFeedback表索引
                "CREATE INDEX IF NOT EXISTS idx_user_feedback_created ON user_feedback(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_user_feedback_analysis ON user_feedback(analysis_id)",
                
                # SystemLog表索引
                "CREATE INDEX IF NOT EXISTS idx_system_logs_created ON system_logs(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level)",
                
                # APIConfig表索引
                "CREATE INDEX IF NOT EXISTS idx_api_configs_name ON api_configs(api_name)",
                "CREATE INDEX IF NOT EXISTS idx_api_configs_active ON api_configs(is_active)",
            ]
            
            for index_sql in indexes:
                try:
                    await conn.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"创建索引失败 {index_sql}: {e}")
        
        logger.info("数据库索引创建完成")
        
    except Exception as e:
        logger.error(f"创建数据库索引失败: {e}")


async def get_session() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """检查数据库连接"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


async def get_database_stats() -> dict:
    """获取数据库统计信息"""
    stats = {}
    
    try:
        async with AsyncSessionLocal() as session:
            # 获取各表记录数
            tables = ["oil_prices", "news_articles", "analysis_results", "chart_files"]
            
            for table in tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[f"{table}_count"] = count
            
            # 获取油价数据时间范围
            result = await session.execute(
                text("SELECT MIN(date), MAX(date) FROM oil_prices")
            )
            min_date, max_date = result.fetchone()
            stats["oil_price_date_range"] = {
                "min": min_date.isoformat() if min_date else None,
                "max": max_date.isoformat() if max_date else None,
                "days": (max_date - min_date).days if min_date and max_date else 0
            }
            
            # 获取数据库大小（SQLite）
            if "sqlite" in settings.database_url:
                result = await session.execute(
                    text("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                )
                db_size = result.scalar()
                stats["database_size_bytes"] = db_size
            
            logger.info(f"数据库统计: {stats}")
            return stats
            
    except Exception as e:
        logger.error(f"获取数据库统计失败: {e}")
        return {}


async def cleanup_old_data(days_to_keep: int = 90):
    """清理旧数据"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import delete
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        async with AsyncSessionLocal() as session:
            # 清理旧油价数据
            stmt = delete(OilPrice).where(OilPrice.date < cutoff_date.date())
            result = await session.execute(stmt)
            oil_deleted = result.rowcount
            
            # 清理旧新闻
            stmt = delete(NewsArticle).where(NewsArticle.published_at < cutoff_date)
            result = await session.execute(stmt)
            news_deleted = result.rowcount
            
            # 清理旧图表文件记录（实际文件需要另外清理）
            stmt = delete(ChartFile).where(ChartFile.generated_at < cutoff_date)
            result = await session.execute(stmt)
            chart_deleted = result.rowcount
            
            await session.commit()
            
            logger.info(f"数据清理完成: 油价{oil_deleted}条, 新闻{news_deleted}条, 图表{chart_deleted}条")
            
            return {
                "oil_prices_deleted": oil_deleted,
                "news_deleted": news_deleted,
                "charts_deleted": chart_deleted,
                "cutoff_date": cutoff_date.isoformat()
            }
            
    except Exception as e:
        logger.error(f"清理旧数据失败: {e}")
        if 'session' in locals():
            await session.rollback()
        return {}


async def backup_database(backup_path: str = None):
    """备份数据库"""
    import shutil
    import os
    from datetime import datetime
    
    try:
        if backup_path is None:
            backup_dir = "data/backups"
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{backup_dir}/oil_monitor_backup_{timestamp}.db"
        
        # 对于SQLite，直接复制文件
        if "sqlite" in settings.database_url:
            db_path = settings.database_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                logger.info(f"数据库已备份到: {backup_path}")
                return backup_path
            else:
                logger.error(f"数据库文件不存在: {db_path}")
                return None
        else:
            # 对于其他数据库，需要导出逻辑
            logger.warning(f"数据库备份功能仅支持SQLite: {settings.database_url}")
            return None
            
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        return None