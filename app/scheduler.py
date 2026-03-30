"""
简化调度器 - 定时任务
"""
import logging
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config_simple import settings

logger = logging.getLogger(__name__)


def collect_oil_prices():
    """收集油价数据"""
    logger.info(f"[{datetime.now()}] 开始收集油价数据...")
    # 这里可以调用数据收集器
    logger.info(f"[{datetime.now()}] 油价数据收集完成")


def analyze_prices():
    """分析油价数据"""
    logger.info(f"[{datetime.now()}] 开始分析油价数据...")
    # 这里可以调用AI分析器
    logger.info(f"[{datetime.now()}] 油价数据分析完成")


def init_scheduler():
    """初始化调度器"""
    logger.info("初始化任务调度器...")
    
    scheduler = BackgroundScheduler()
    
    # 添加定时任务
    try:
        # 每天8点收集数据
        scheduler.add_job(
            collect_oil_prices,
            CronTrigger(hour=8, minute=0),
            id='collect_oil_prices',
            name='收集油价数据',
            replace_existing=True
        )
        
        # 每天9点分析数据
        scheduler.add_job(
            analyze_prices,
            CronTrigger(hour=9, minute=0),
            id='analyze_prices',
            name='分析油价数据',
            replace_existing=True
        )
        
        logger.info("定时任务配置完成")
        logger.info(f"数据收集时间: 每天 {settings.collection_schedule}")
        logger.info(f"数据分析时间: 每天 {settings.analysis_schedule}")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"配置定时任务失败: {e}")
        return None


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化调度器
    scheduler = init_scheduler()
    
    if scheduler:
        try:
            scheduler.start()
            logger.info("任务调度器启动成功")
            
            # 保持程序运行
            while True:
                time.sleep(60)
                
        except (KeyboardInterrupt, SystemExit):
            logger.info("停止任务调度器...")
            scheduler.shutdown()
        except Exception as e:
            logger.error(f"调度器运行异常: {e}")
            scheduler.shutdown()
    else:
        logger.error("调度器初始化失败")