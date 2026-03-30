"""
配置文件 - 简化版本，避免pydantic版本冲突
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Settings:
    """应用配置 - 使用dataclass避免pydantic依赖"""
    
    # 应用设置
    app_name: str = "广西油价监控分析系统"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API设置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # 数据库设置
    database_url: str = Field(
        default="sqlite:///data/oil_prices.db",
        env="DATABASE_URL"
    )
    
    # AI设置
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        env="OPENAI_BASE_URL"
    )
    openai_model: str = "deepseek-chat"
    
    # Redis设置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # 数据收集设置
    collection_schedule: str = "0 8 * * *"  # 每天8点收集
    analysis_schedule: str = "0 9 * * *"    # 每天9点分析
    
    # 广西地区列表
    guangxi_regions: List[str] = [
        "南宁", "柳州", "桂林", "梧州", "北海",
        "防城港", "钦州", "贵港", "玉林", "百色",
        "贺州", "河池", "来宾", "崇左"
    ]
    
    # 油价数据源（免费）
    oil_price_sources: List[Dict[str, Any]] = [
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
            "url": "https://www.youjiawang.net/",
            "type": "website",
            "enabled": True,
            "parser": "youjiawang",
            "region": "广西"
        },
        {
            "name": "高德地图油价API",
            "url": "https://restapi.amap.com/v3/place/text",
            "type": "api",
            "enabled": True,
            "parser": "amap",
            "key_required": True,
            "free_tier": True
        },
        {
            "name": "百度地图油价查询",
            "url": "https://api.map.baidu.com/place/v2/search",
            "type": "api",
            "enabled": True,
            "parser": "baidu",
            "key_required": True,
            "free_tier": True
        },
        {
            "name": "广西发改委官网",
            "url": "http://fgw.gxzf.gov.cn/",
            "type": "website",
            "enabled": True,
            "parser": "government",
            "region": "广西"
        },
        {
            "name": "各地市发改委网站",
            "url": "",
            "type": "website",
            "enabled": True,
            "parser": "government_local",
            "region": "广西"
        }
    ]
    
    # 新闻数据源（免费）
    news_sources: List[Dict[str, Any]] = [
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
            "name": "网易财经RSS",
            "url": "http://money.163.com/special/00252G50/money.xml",
            "type": "rss",
            "enabled": True,
            "category": "财经"
        },
        {
            "name": "腾讯财经",
            "url": "https://finance.qq.com/",
            "type": "website",
            "enabled": True,
            "parser": "tencent",
            "category": "财经"
        },
        {
            "name": "东方财富网",
            "url": "https://www.eastmoney.com/",
            "type": "website",
            "enabled": True,
            "parser": "eastmoney",
            "category": "财经"
        },
        {
            "name": "和讯网能源",
            "url": "http://energy.hexun.com/",
            "type": "website",
            "enabled": True,
            "parser": "hexun",
            "category": "能源"
        },
        {
            "name": "中国能源网",
            "url": "http://www.china5e.com/",
            "type": "website",
            "enabled": True,
            "parser": "china5e",
            "category": "能源"
        },
        {
            "name": "国际石油网",
            "url": "http://www.in-en.com/",
            "type": "website",
            "enabled": True,
            "parser": "inen",
            "category": "石油"
        },
        {
            "name": "百度新闻搜索API",
            "url": "https://news.baidu.com/news",
            "type": "api",
            "enabled": True,
            "parser": "baidu_news",
            "keywords": ["油价", "汽油", "柴油", "广西油价"],
            "free_tier": True
        }
    ]
    
    # 可视化设置
    chart_theme: str = "plotly_white"
    chart_width: int = 1200
    chart_height: int = 800
    
    # 文件路径
    data_dir: str = "data"
    logs_dir: str = "logs"
    charts_dir: str = "data/charts"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建配置实例
settings = Settings()

# 创建必要的目录
for directory in [settings.data_dir, settings.logs_dir, settings.charts_dir]:
    os.makedirs(directory, exist_ok=True)