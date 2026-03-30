# 部署指南

## 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd guangxi-oil-price-monitor

# 安装Docker和Docker Compose
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install docker.io docker-compose

# CentOS/RHEL:
sudo yum install docker docker-compose
```

### 2. 配置设置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

需要配置的关键项：
- `OPENAI_API_KEY`: OpenAI兼容API密钥（如DeepSeek）
- `OPENAI_BASE_URL`: API基础URL
- 其他配置按需修改

### 3. 启动服务
```bash
# 赋予执行权限
chmod +x start.sh stop.sh

# 启动服务
./start.sh
```

### 4. 验证部署
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f oil-monitor

# 访问健康检查
curl http://localhost:8000/health
```

## 数据源配置

### 免费油价数据源
1. **政府网站**：
   - 广西发改委官网
   - 各地市发改委网站

2. **第三方平台**：
   - 油价网 (youjiawang.com)
   - 易车网油价频道
   - 汽车之家油价查询

3. **API接口**：
   - 高德地图油价API
   - 百度地图油价查询

### 新闻数据源
1. **RSS订阅**：
   - 新华社能源频道
   - 人民日报经济版
   - 新浪财经RSS

2. **网站爬取**：
   - 腾讯财经
   - 网易财经
   - 东方财富网

## 定时任务配置

系统包含以下定时任务：

### 数据收集任务
- **时间**: 每天8:00 AM
- **任务**: 收集广西各地油价数据
- **配置**: `COLLECTION_SCHEDULE=0 8 * * *`

### AI分析任务
- **时间**: 每天9:00 AM
- **任务**: 分析油价趋势并提供推荐
- **配置**: `ANALYSIS_SCHEDULE=0 9 * * *`

### 图表生成任务
- **时间**: 每天10:00 AM
- **任务**: 生成可视化图表
- **配置**: 代码中硬编码

## API接口

### 主要端点
- `GET /` - 应用信息
- `GET /health` - 健康检查
- `GET /docs` - API文档（Swagger UI）

### 油价数据
- `GET /api/oil-prices/today` - 今日油价
- `GET /api/oil-prices/history` - 历史数据
- `POST /api/oil-prices/collect` - 手动触发收集

### 分析推荐
- `GET /api/analysis/today` - 今日分析推荐
- `GET /api/analysis/history` - 历史分析

### 图表可视化
- `GET /api/charts/trend` - 趋势图
- `GET /api/charts/calendar` - 日历热力图
- `GET /api/charts/regional` - 地区对比图

### 新闻资讯
- `GET /api/news/latest` - 最新新闻
- `GET /api/news/search` - 搜索新闻

## 数据存储

### 数据库
- **主数据库**: SQLite (默认) 或 PostgreSQL
- **位置**: `./data/oil_prices.db`
- **备份**: 自动每日备份到 `./data/backups/`

### 图表文件
- **格式**: HTML (交互式) 和 PNG (静态)
- **位置**: `./data/charts/`
- **保留**: 最近30天的图表

### 日志文件
- **位置**: `./logs/`
- **轮转**: 每天轮转，保留7天

## 监控和维护

### 健康检查
```bash
# 手动检查
curl http://localhost:8000/health

# 监控脚本
./monitor.sh
```

### 日志查看
```bash
# 实时日志
docker-compose logs -f

# 特定服务日志
docker-compose logs oil-monitor
docker-compose logs scheduler

# 查看历史日志
tail -f logs/app.log
```

### 数据备份
```bash
# 手动备份
./backup.sh

# 自动备份配置在docker-compose.yml中
```

### 故障排除

#### 常见问题
1. **服务启动失败**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8000
   
   # 查看详细错误
   docker-compose logs --tail=100 oil-monitor
   ```

2. **数据收集失败**
   - 检查网络连接
   - 验证数据源URL是否可访问
   - 查看收集器日志

3. **AI分析失败**
   - 检查API密钥配置
   - 验证API服务可用性
   - 查看分析器日志

#### 性能优化
1. **数据库优化**
   ```sql
   -- 创建索引
   CREATE INDEX idx_oil_prices_date ON oil_prices(date);
   CREATE INDEX idx_oil_prices_region ON oil_prices(region);
   ```

2. **缓存配置**
   - Redis缓存热门查询
   - 图表结果缓存24小时

## 扩展功能

### 通知渠道
1. **飞书机器人**
   - 配置飞书App ID和Secret
   - 设置Webhook接收地址

2. **邮件通知**
   - 配置SMTP服务器
   - 设置收件人邮箱

3. **微信推送**
   - 集成Server酱
   - 企业微信机器人

### 数据分析增强
1. **机器学习预测**
   - 使用历史数据训练预测模型
   - 实现油价趋势预测

2. **多维度分析**
   - 结合宏观经济数据
   - 关联国际油价变化

### 可视化增强
1. **移动端适配**
   - 响应式图表设计
   - PWA应用支持

2. **实时仪表板**
   - WebSocket实时更新
   - 交互式数据探索

## 安全考虑

### 访问控制
- API密钥加密存储
- 敏感配置环境变量管理
- 请求频率限制

### 数据安全
- 数据库加密
- 传输数据HTTPS
- 定期安全审计

### 隐私保护
- 不收集用户个人信息
- 匿名化处理数据
- 符合GDPR要求

## 贡献指南

### 开发环境
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black app/
flake8 app/
```

### 提交规范
- 遵循Conventional Commits
- 编写单元测试
- 更新相关文档

## 许可证
MIT License - 详见LICENSE文件