"""
同步数据库模块 - 避免异步驱动问题
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from app.config_simple import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

# 创建同步引擎（使用普通SQLite）
sync_database_url = settings.database_url.replace("sqlite+aiosqlite://", "sqlite://")
engine = create_engine(
    sync_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"check_same_thread": False}  # SQLite需要这个
)

# 创建同步会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """初始化数据库（同步版本）"""
    logger.info("初始化数据库（同步版本）...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
        
        # 创建必要的索引
        create_indexes()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def create_indexes():
    """创建数据库索引（同步版本）"""
    try:
        with engine.begin() as conn:
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
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"创建索引失败 {index_sql}: {e}")
        
        logger.info("数据库索引创建完成")
        
    except Exception as e:
        logger.error(f"创建数据库索引失败: {e}")


@contextmanager
def get_session() -> Session:
    """获取数据库会话（同步版本）"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection() -> bool:
    """检查数据库连接（同步版本）"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False