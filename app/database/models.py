"""
数据库模型定义
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OilPrice(Base):
    """油价数据表"""
    __tablename__ = "oil_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 地区信息
    region = Column(String(50), nullable=False, index=True)  # 地区名称，如"南宁"
    date = Column(Date, nullable=False, index=True)          # 油价日期
    
    # 油价数据（元/升）
    gasoline_92 = Column(Float, nullable=False)  # 92号汽油价格
    gasoline_95 = Column(Float, nullable=False)  # 95号汽油价格
    diesel_0 = Column(Float, nullable=False)     # 0号柴油价格
    
    # 数据来源信息
    source = Column(String(100), nullable=False)            # 数据来源
    collected_at = Column(DateTime, default=datetime.now)   # 收集时间
    
    # 扩展字段
    note = Column(Text, nullable=True)           # 备注
    raw_data = Column(JSON, nullable=True)       # 原始数据
    
    def __repr__(self):
        return f"<OilPrice(region='{self.region}', date='{self.date}', 92号={self.gasoline_92})>"


class NewsArticle(Base):
    """新闻文章表"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 文章信息
    title = Column(String(500), nullable=False, index=True)  # 标题
    summary = Column(Text, nullable=True)                    # 摘要
    url = Column(String(500), nullable=False, unique=True)   # 原文链接
    
    # 来源信息
    source = Column(String(100), nullable=False, index=True)  # 来源网站
    category = Column(String(50), nullable=True)              # 分类
    
    # 时间信息
    published_at = Column(DateTime, nullable=False, index=True)  # 发布时间
    collected_at = Column(DateTime, default=datetime.now)        # 收集时间
    
    # 分析字段
    relevance_score = Column(Float, default=0.5)  # 相关性分数（0-1）
    sentiment_score = Column(Float, nullable=True)  # 情感分析分数（-1到1）
    
    # 内容分析
    keywords = Column(JSON, nullable=True)        # 关键词提取
    entities = Column(JSON, nullable=True)        # 实体识别
    
    # 状态字段
    is_processed = Column(Boolean, default=False)  # 是否已处理
    is_important = Column(Boolean, default=False)  # 是否重要
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:50]}...', source='{self.source}')>"


class AnalysisResult(Base):
    """分析结果表"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 分析信息
    analysis_date = Column(Date, nullable=False, index=True)  # 分析日期
    analysis_type = Column(String(50), nullable=False)        # 分析类型：daily, weekly, monthly
    
    # 分析内容
    summary = Column(Text, nullable=False)                    # 分析摘要
    trend_analysis = Column(Text, nullable=True)              # 趋势分析
    recommendation = Column(Text, nullable=False)             # 加油推荐
    
    # 量化指标
    confidence_score = Column(Float, default=0.0)             # 置信度（0-1）
    price_change_prediction = Column(Float, nullable=True)    # 价格变化预测（%）
    
    # 数据关联
    oil_price_ids = Column(JSON, nullable=True)               # 关联的油价ID列表
    news_article_ids = Column(JSON, nullable=True)            # 关联的新闻ID列表
    
    # 原始数据和分析过程
    raw_data = Column(JSON, nullable=True)                    # 原始分析数据
    analysis_process = Column(Text, nullable=True)            # 分析过程记录
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<AnalysisResult(date='{self.analysis_date}', confidence={self.confidence_score:.2f})>"


class ChartFile(Base):
    """图表文件表"""
    __tablename__ = "chart_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 文件信息
    filename = Column(String(200), nullable=False, unique=True)  # 文件名
    filepath = Column(String(500), nullable=False)               # 文件路径
    file_type = Column(String(20), nullable=False)               # 文件类型：html, png, jpg
    
    # 图表信息
    chart_type = Column(String(50), nullable=False)              # 图表类型：trend, calendar, regional
    title = Column(String(200), nullable=False)                  # 图表标题
    description = Column(Text, nullable=True)                    # 图表描述
    
    # 数据范围
    start_date = Column(Date, nullable=True)                     # 数据开始日期
    end_date = Column(Date, nullable=True)                       # 数据结束日期
    regions = Column(JSON, nullable=True)                        # 包含的地区
    
    # 生成信息
    generated_at = Column(DateTime, default=datetime.now, index=True)
    size_bytes = Column(Integer, nullable=True)                  # 文件大小
    
    # 访问统计
    view_count = Column(Integer, default=0)                      # 查看次数
    last_viewed = Column(DateTime, nullable=True)                # 最后查看时间
    
    def __repr__(self):
        return f"<ChartFile(filename='{self.filename}', type='{self.chart_type}')>"


class UserFeedback(Base):
    """用户反馈表"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(String(100), nullable=True, index=True)     # 用户ID（匿名）
    user_ip = Column(String(50), nullable=True)                  # 用户IP（匿名化）
    
    # 反馈内容
    feedback_type = Column(String(50), nullable=False)           # 反馈类型：accuracy, usefulness, bug, suggestion
    rating = Column(Integer, nullable=True)                      # 评分（1-5）
    comment = Column(Text, nullable=True)                        # 评论
    
    # 关联数据
    analysis_id = Column(Integer, nullable=True, index=True)     # 关联的分析ID
    recommendation_followed = Column(Boolean, nullable=True)     # 是否遵循了推荐
    
    # 结果反馈
    actual_price_change = Column(Float, nullable=True)           # 实际价格变化（如果用户反馈）
    satisfaction_score = Column(Float, nullable=True)            # 满意度分数
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f"<UserFeedback(type='{self.feedback_type}', rating={self.rating})>"


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 日志信息
    level = Column(String(20), nullable=False, index=True)       # 日志级别：INFO, WARNING, ERROR
    module = Column(String(100), nullable=False)                 # 模块名称
    message = Column(Text, nullable=False)                       # 日志消息
    
    # 上下文信息
    task_id = Column(String(100), nullable=True)                 # 任务ID
    data_source = Column(String(100), nullable=True)             # 数据源
    region = Column(String(50), nullable=True)                   # 地区
    
    # 性能指标
    execution_time = Column(Float, nullable=True)                # 执行时间（秒）
    memory_usage = Column(Float, nullable=True)                  # 内存使用（MB）
    
    # 错误信息
    error_type = Column(String(100), nullable=True)              # 错误类型
    error_details = Column(Text, nullable=True)                  # 错误详情
    stack_trace = Column(Text, nullable=True)                    # 堆栈跟踪
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f"<SystemLog(level='{self.level}', module='{self.module}', message='{self.message[:50]}...')>"


class APIConfig(Base):
    """API配置表"""
    __tablename__ = "api_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # API信息
    api_name = Column(String(100), nullable=False, unique=True)  # API名称
    api_type = Column(String(50), nullable=False)                # API类型：oil_price, news, map
    
    # 认证信息
    api_key = Column(String(500), nullable=True)                 # API密钥（加密存储）
    api_secret = Column(String(500), nullable=True)              # API密钥（加密存储）
    access_token = Column(String(500), nullable=True)            # 访问令牌
    
    # 配置信息
    base_url = Column(String(500), nullable=False)               # 基础URL
    endpoint = Column(String(200), nullable=True)                # 端点路径
    parameters = Column(JSON, nullable=True)                     # 参数配置
    
    # 限制信息
    rate_limit = Column(Integer, nullable=True)                  # 速率限制（次/天）
    quota_used = Column(Integer, default=0)                      # 已使用配额
    quota_reset_at = Column(DateTime, nullable=True)             # 配额重置时间
    
    # 状态信息
    is_active = Column(Boolean, default=True)                    # 是否激活
    last_success = Column(DateTime, nullable=True)               # 最后成功时间
    last_error = Column(Text, nullable=True)                     # 最后错误信息
    error_count = Column(Integer, default=0)                     # 错误计数
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<APIConfig(name='{self.api_name}', type='{self.api_type}', active={self.is_active})>"


# 创建所有表的元数据
__all__ = [
    "OilPrice",
    "NewsArticle",
    "AnalysisResult",
    "ChartFile",
    "UserFeedback",
    "SystemLog",
    "APIConfig",
]