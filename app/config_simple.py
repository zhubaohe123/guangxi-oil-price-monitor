"""
简化配置文件 - 避免pydantic依赖问题
"""
import os
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Settings:
    """应用配置"""
    
    # 应用设置
    app_name: str = "广西油价监控分析系统"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API设置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # 数据库设置
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/oil_prices.db")
    
    # AI设置
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    openai_model: str = "deepseek-chat"
    
    # Redis设置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # 数据收集设置
    collection_schedule: str = "0 8 * * *"  # 每天8点收集
    analysis_schedule: str = "0 9 * * *"    # 每天9点分析
    
    # 广西地区列表
    guangxi_regions: List[str] = field(default_factory=lambda: [
        "南宁", "柳州", "桂林", "梧州", "北海",
        "防城港", "钦州", "贵港", "玉林", "百色",
        "贺州", "河池", "来宾", "崇左"
    ])
    
    # 油价数据源（免费）
    oil_price_sources: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "name": "易车网油价查询",
            "url": "https://car.yiche.com/youjia/",
            "type": "website",
            "enabled": True,
            "parser": "yiche",
            "region": "广西"
        },
        {
            "name": "汽车之家油价",
            "url": "https://jiage.autohome.com.cn/youjia/",
            "type": "website",
            "enabled": True,
            "parser": "autohome",
            "region": "广西"
        },
        {
            "name": "油价网",
            "url": "https://www.youjiawang.com/",
            "type": "website",
            "enabled": True,
            "parser": "youjiawang",
            "region": "广西"
        },
        {
            "name": "广西发改委官网",
            "url": "http://fgw.gxzf.gov.cn/",
            "type": "website",
            "enabled": True,
            "parser": "guangxi_gov",
            "region": "广西"
        }
    ])
    
    # 新闻数据源
    news_sources: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "name": "新华社能源RSS",
            "url": "http://www.xinhuanet.com/energy/news_energy.xml",
            "type": "rss",
            "enabled": True,
            "category": "能源"
        },
        {
            "name": "人民日报经济版RSS",
            "url": "http://www.people.com.cn/rss/finance.xml",
            "type": "rss",
            "enabled": True,
            "category": "经济"
        },
        {
            "name": "新浪财经RSS",
            "url": "http://rss.sina.com.cn/finance/finance.xml",
            "type": "rss",
            "enabled": True,
            "category": "财经"
        },
        {
            "name": "腾讯财经RSS",
            "url": "http://rss.qq.com/finance.xml",
            "type": "rss",
            "enabled": True,
            "category": "财经"
        }
    ])
    
    # 日志设置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # 文件路径
    data_dir: str = "data"
    charts_dir: str = "data/charts"
    logs_dir: str = "logs"
    
    @property
    def is_debug(self) -> bool:
        """是否调试模式"""
        return self.debug or os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
    
    @property
    def has_openai_key(self) -> bool:
        """是否有OpenAI API密钥"""
        return bool(self.openai_api_key)


# 全局配置实例
settings = Settings()