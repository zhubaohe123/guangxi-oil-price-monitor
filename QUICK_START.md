# 广西油价监控分析系统 - 快速开始指南

## 🌟 项目简介
一个完全免费的Docker应用，每天自动收集广西各地油价，进行AI分析，生成可视化图表，并提供加油推荐。

## 🚀 5分钟快速部署

### 步骤1：环境准备
```bash
# 确保已安装Docker和Docker Compose
docker --version
docker-compose --version

# 如果没有安装，使用以下命令（Ubuntu/Debian）：
sudo apt-get update
sudo apt-get install docker.io docker-compose
```

### 步骤2：下载项目
```bash
# 克隆项目或下载ZIP
git clone <项目地址>
cd guangxi-oil-price-monitor
```

### 步骤3：配置API密钥
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件，设置DeepSeek API密钥
nano .env
```

在 `.env` 文件中设置：
```bash
# OpenAI兼容API配置（使用DeepSeek）
OPENAI_API_KEY=sk-your-deepseek-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com/v1

# 其他配置保持默认即可
```

### 步骤4：启动服务
```bash
# 一键启动
chmod +x start.sh
./start.sh
```

### 步骤5：验证部署
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f oil-monitor

# 访问健康检查
curl http://localhost:8000/health
```

## 📊 免费数据源配置

### 已配置的免费数据源

#### 1. 油价数据源
- **易车网油价查询** - 实时油价信息
- **汽车之家油价** - 各地区油价对比
- **油价网** - 专业油价数据
- **广西发改委官网** - 官方调价信息

#### 2. 新闻数据源
- **新华社能源RSS** - 能源政策新闻
- **人民日报经济版RSS** - 经济动态
- **新浪财经RSS** - 财经资讯
- **腾讯财经** - 市场分析

### 数据收集策略
- **智能多源采集**：同时从多个数据源收集，提高成功率
- **自动降级机制**：如果免费源失败，使用模拟数据保证服务可用
- **去重过滤**：自动过滤重复和低质量数据

## 🤖 AI分析功能

### 分析内容
1. **今日油价评价** - 总体价格水平分析
2. **趋势分析** - 上涨/下跌趋势判断
3. **地区差异** - 各地区价格对比
4. **市场因素** - 结合新闻分析影响因素
5. **加油推荐** - 智能推荐是否加油

### 加油推荐逻辑
- **价格较低时**：推荐加油，建议加满
- **价格较高时**：建议等待，非必要不加油
- **价格适中时**：根据需求决定

## 📈 可视化图表

### 自动生成的图表
1. **油价趋势图** - 最近30天价格变化
2. **日历热力图** - 月度价格分布
3. **地区对比图** - 各地区价格对比
4. **价格分布图** - 价格统计分布

### 访问图表
- 趋势图：`http://localhost:8000/api/charts/trend`
- 日历图：`http://localhost:8000/api/charts/calendar`
- 地区对比：`http://localhost:8000/api/charts/regional`

## ⏰ 定时任务

### 自动执行时间
- **08:00 AM** - 收集油价数据
- **09:00 AM** - AI分析油价趋势
- **10:00 AM** - 生成可视化图表

### 手动触发
```bash
# 手动收集数据
curl -X POST http://localhost:8000/api/oil-prices/collect

# 获取今日推荐
curl http://localhost:8000/api/analysis/today
```

## 🔧 常用API接口

### 基础信息
```bash
# 应用信息
curl http://localhost:8000/

# 健康检查
curl http://localhost:8000/health

# API文档
打开浏览器访问：http://localhost:8000/docs
```

### 油价数据
```bash
# 今日油价
curl http://localhost:8000/api/oil-prices/today

# 历史数据（最近30天）
curl http://localhost:8000/api/oil-prices/history

# 特定地区数据
curl "http://localhost:8000/api/oil-prices/region/南宁?days=7"
```

### 分析推荐
```bash
# 今日加油推荐
curl http://localhost:8000/api/analysis/today

# 历史分析记录
curl http://localhost:8000/api/analysis/history
```

### 新闻资讯
```bash
# 今日油价新闻
curl http://localhost:8000/api/news/today

# 搜索新闻
curl "http://localhost:8000/api/news/search?keyword=油价&days=3"
```

## 🐳 Docker管理命令

### 服务管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f [服务名]
```

### 数据管理
```bash
# 备份数据
docker-compose exec oil-monitor python -c "from app.database import backup_database; import asyncio; asyncio.run(backup_database())"

# 清理旧数据（保留最近90天）
docker-compose exec oil-monitor python -c "from app.database import cleanup_old_data; import asyncio; asyncio.run(cleanup_old_data(90))"
```

## 🔍 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查端口占用
netstat -tulpn | grep :8000

# 查看详细错误日志
docker-compose logs --tail=100 oil-monitor
```

#### 2. 数据收集失败
- 检查网络连接
- 验证数据源网站是否可访问
- 查看收集器日志：`docker-compose logs scheduler`

#### 3. AI分析失败
- 检查API密钥配置
- 验证DeepSeek API服务状态
- 查看分析器日志

### 日志查看
```bash
# 实时查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs oil-monitor
docker-compose logs scheduler

# 查看历史日志文件
tail -f logs/app.log
```

## 📱 使用示例

### 获取今日加油推荐
```bash
curl http://localhost:8000/api/analysis/today | python -m json.tool
```

示例响应：
```json
{
  "date": "2026-03-30",
  "summary": "今日广西平均油价：92号7.85元/升，价格处于中等水平...",
  "recommendation": "油价适中，可根据需要加油，建议选择价格较低的加油站",
  "confidence": 0.85,
  "analysis_time": "2026-03-30 09:15:30"
}
```

### 查看油价趋势图
1. 打开浏览器访问：`http://localhost:8000/api/charts/trend`
2. 下载生成的HTML文件
3. 用浏览器打开查看交互式图表

## 🎯 高级配置

### 自定义数据源
编辑 `app/config.py` 文件，添加或修改数据源：
```python
oil_price_sources = [
    {
        "name": "你的数据源",
        "url": "https://example.com/oil-prices",
        "type": "website",
        "enabled": True,
        "parser": "custom"
    }
]
```

### 调整定时任务
修改 `.env` 文件中的时间配置：
```bash
# 数据收集时间（Cron表达式）
COLLECTION_SCHEDULE=0 8 * * *

# 分析时间
ANALYSIS_SCHEDULE=0 9 * * *
```

### 添加通知渠道
1. **飞书机器人**：配置飞书App ID和Secret
2. **邮件通知**：配置SMTP服务器
3. **微信推送**：集成Server酱

## 📚 学习资源

### 相关技术
- **FastAPI**：现代Python Web框架
- **SQLAlchemy**：Python SQL工具包
- **Plotly**：交互式可视化库
- **Docker**：容器化部署

### 扩展学习
1. 学习如何添加新的数据源
2. 了解如何优化AI分析提示词
3. 探索更多可视化图表类型
4. 学习如何添加用户反馈系统

## 🤝 贡献指南

### 报告问题
1. 查看现有Issue
2. 创建新Issue，描述问题和复现步骤
3. 提供相关日志和配置信息

### 提交改进
1. Fork项目
2. 创建功能分支
3. 提交Pull Request
4. 确保代码通过测试

## 📄 许可证
MIT License - 详见LICENSE文件

## 🌸 特别感谢
感谢勇太（Yuta）的需求启发，让六花（Rikka）能够创建这个有用的工具！

---

**开始使用吧！如果有任何问题，请查看详细文档或提出Issue。**