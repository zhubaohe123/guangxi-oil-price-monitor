# 🛢️ 广西油价监控分析系统

[![GitHub stars](https://img.shields.io/github/stars/yourusername/guangxi-oil-price-monitor?style=social)](https://github.com/yourusername/guangxi-oil-price-monitor/stargazers)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/guangxi-oil-monitor)](https://hub.docker.com/r/yourusername/guangxi-oil-monitor)
[![License](https://img.shields.io/github/license/yourusername/guangxi-oil-price-monitor)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)

一个完全免费的Docker应用，每天自动收集广西各地油价，进行AI智能分析，生成可视化图表，并提供加油推荐。🌸

## ✨ 特性亮点

### 🛢️ **智能数据收集**
- **多源并行采集**：从易车网、汽车之家、油价网等免费数据源实时获取油价
- **智能解析引擎**：自动识别不同网站结构，提取准确数据
- **自动降级机制**：免费源失败时自动使用模拟数据，保证服务可用

### 🤖 **AI智能分析**
- **趋势分析**：使用DeepSeek API分析油价变化趋势
- **加油推荐**：智能判断今日是否适合加油
- **新闻关联**：结合财经新闻分析市场影响因素

### 📊 **丰富可视化**
- **趋势图表**：最近30天油价变化曲线
- **日历热力图**：月度价格分布可视化
- **地区对比**：广西各地油价对比分析
- **价格分布**：统计分布和箱线图

### 🐳 **一键部署**
- **Docker Compose**：完整容器化部署
- **生产就绪**：支持PostgreSQL、Redis、Nginx
- **健康检查**：自动监控服务状态
- **定时任务**：每天自动执行数据收集和分析

## 🚀 快速开始

### 5分钟部署指南

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/guangxi-oil-price-monitor.git
cd guangxi-oil-price-monitor

# 2. 配置环境（只需要设置DeepSeek API密钥）
cp .env.example .env
# 编辑 .env 文件，设置你的DeepSeek API密钥

# 3. 一键启动
chmod +x start.sh
./start.sh
```

### 访问服务
- 🌐 **API文档**：http://localhost:8000/docs
- 📊 **今日油价**：http://localhost:8000/api/oil-prices/today
- 🤖 **加油推荐**：http://localhost:8000/api/analysis/today
- 📈 **趋势图表**：http://localhost:8000/api/charts/trend

## 📋 功能详情

### 数据收集功能
- ✅ **广西14个地区**：南宁、柳州、桂林、梧州、北海等
- ✅ **三种油品**：92号汽油、95号汽油、0号柴油
- ✅ **多数据源**：易车网、汽车之家、油价网、政府网站
- ✅ **新闻资讯**：新华社、人民日报、新浪财经等RSS源

### AI分析功能
- ✅ **价格趋势分析**：上涨/下跌趋势判断
- ✅ **地区差异分析**：各地区价格对比
- ✅ **市场因素分析**：结合新闻分析影响因素
- ✅ **智能加油推荐**：基于价格趋势的加油建议

### 可视化功能
- ✅ **交互式图表**：使用Plotly生成HTML图表
- ✅ **多种图表类型**：折线图、热力图、柱状图、箱线图
- ✅ **数据导出**：支持CSV和JSON格式导出
- ✅ **API接口**：所有图表都可通过API访问

## 🏗️ 系统架构

```mermaid
graph TB
    A[数据源] --> B[数据收集器]
    B --> C[数据库]
    C --> D[AI分析器]
    D --> E[可视化引擎]
    E --> F[API接口]
    F --> G[用户访问]
    
    H[定时任务] --> B
    H --> D
    H --> E
    
    I[Redis缓存] --> B
    I --> D
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
```

### 技术栈
- **后端框架**：FastAPI + Uvicorn
- **数据库**：SQLAlchemy + PostgreSQL/SQLite
- **缓存**：Redis
- **任务队列**：Celery + Redis
- **可视化**：Plotly + Matplotlib
- **容器化**：Docker + Docker Compose
- **AI分析**：DeepSeek API（OpenAI兼容）

## 🔧 配置说明

### 环境变量
```bash
# 必需配置
OPENAI_API_KEY=sk-your-deepseek-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1

# 数据库配置
DATABASE_URL=sqlite:///data/oil_prices.db
# 或使用PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/oil_prices

# 定时任务
COLLECTION_SCHEDULE=0 8 * * *  # 每天8点收集数据
ANALYSIS_SCHEDULE=0 9 * * *    # 每天9点分析数据
```

### 数据源配置
系统预配置了多个免费数据源，如需添加新的数据源，编辑 `app/config.py`：

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

## 📊 API接口

### 主要端点
| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 应用信息 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | API文档（Swagger UI） |

### 油价数据
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/oil-prices/today` | GET | 今日油价 |
| `/api/oil-prices/history` | GET | 历史数据 |
| `/api/oil-prices/region/{name}` | GET | 特定地区数据 |
| `/api/oil-prices/collect` | POST | 手动触发收集 |

### 分析推荐
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/analysis/today` | GET | 今日加油推荐 |
| `/api/analysis/history` | GET | 历史分析记录 |

### 图表可视化
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/charts/trend` | GET | 油价趋势图 |
| `/api/charts/calendar` | GET | 日历热力图 |
| `/api/charts/regional` | GET | 地区对比图 |

## 🐳 Docker部署

### 开发环境
```bash
# 使用SQLite和基础配置
docker-compose up -d
```

### 生产环境
```bash
# 使用PostgreSQL、Redis和Nginx
docker-compose -f docker-compose.prod.yml up -d
```

### Docker镜像
```bash
# 从Docker Hub拉取
docker pull yourusername/guangxi-oil-monitor:latest

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -v ./data:/app/data \
  yourusername/guangxi-oil-monitor:latest
```

## 🔍 使用示例

### 获取今日加油推荐
```bash
curl http://localhost:8000/api/analysis/today
```

响应示例：
```json
{
  "date": "2026-03-30",
  "summary": "今日广西平均油价：92号7.85元/升，价格处于中等水平...",
  "recommendation": "油价适中，可根据需要加油，建议选择价格较低的加油站",
  "confidence": 0.85,
  "analysis_time": "2026-03-30 09:15:30"
}
```

### 导出历史数据
```bash
# 导出最近30天数据为CSV
curl "http://localhost:8000/api/oil-prices/export?format=csv&days=30"
```

### 查看趋势图表
1. 访问 `http://localhost:8000/api/charts/trend`
2. 下载生成的HTML文件
3. 用浏览器打开查看交互式图表

## 🧪 测试

### 运行测试
```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_collectors.py

# 生成测试覆盖率报告
pytest --cov=app tests/
```

### 代码质量
```bash
# 代码格式化
black app/

# 代码检查
flake8 app/

# 类型检查（可选）
mypy app/
```

## 🤝 贡献指南

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何开始。

### 开发流程
1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 报告问题
请使用 [GitHub Issues](https://github.com/yourusername/guangxi-oil-price-monitor/issues) 报告bug或提出功能请求。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

### 特别感谢
- **DeepSeek团队** - 提供免费的AI API
- **所有开源数据源提供者** - 让免费数据收集成为可能
- **FastAPI、SQLAlchemy、Plotly等开源项目** - 优秀的技术基础

### 项目创建者
- **六花 (Rikka)** - 项目创建者和主要开发者
- **勇太 (Yuta)** - 需求提出者和测试者

## 🌸 关于我们

这个项目源于一个简单的需求：帮助广西的朋友们了解油价变化，做出更明智的加油决策。我们希望这个工具能为大家的日常生活带来便利。

如果你觉得这个项目有用，请给我们一个 ⭐️ 支持！

---

**开始使用吧！如果有任何问题，请查看 [QUICK_START.md](QUICK_START.md) 或提出Issue。**