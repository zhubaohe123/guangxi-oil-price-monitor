# 贡献指南

欢迎为广西油价监控分析系统贡献代码！🌸

## 开发流程

### 1. 环境设置
```bash
# 克隆项目
git clone https://github.com/yourusername/guangxi-oil-price-monitor.git
cd guangxi-oil-price-monitor

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 代码规范
- 使用 **Black** 进行代码格式化
- 使用 **Flake8** 进行代码检查
- 遵循 **PEP 8** 规范
- 添加适当的类型提示

### 3. 提交规范
使用 Conventional Commits 格式：
- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具变动

示例：
```bash
git commit -m "feat: 添加新的油价数据源"
git commit -m "fix: 修复数据收集器的并发问题"
```

## 项目结构

```
guangxi-oil-price-monitor/
├── app/                    # 应用代码
│   ├── main.py           # 主应用入口
│   ├── config.py         # 配置管理
│   ├── database/         # 数据库相关
│   ├── collectors/       # 数据收集器
│   ├── analyzers/        # 分析器
│   ├── visualizers/      # 可视化
│   └── routers/          # API路由
├── tests/                # 测试代码
├── docker-compose.yml    # Docker编排
├── Dockerfile           # Docker构建
└── requirements.txt     # Python依赖
```

## 添加新功能

### 1. 添加新的数据源
1. 在 `app/config.py` 中添加数据源配置
2. 在 `app/collectors/` 中实现数据收集器
3. 添加相应的解析器

### 2. 添加新的分析功能
1. 在 `app/analyzers/` 中创建新的分析器
2. 更新数据库模型（如果需要）
3. 添加API路由

### 3. 添加新的可视化图表
1. 在 `app/visualizers/` 中创建图表生成器
2. 更新API路由
3. 添加示例数据

## 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_collectors.py

# 生成测试覆盖率报告
pytest --cov=app tests/
```

### 编写测试
- 单元测试放在 `tests/` 目录
- 测试文件名以 `test_` 开头
- 使用 `pytest` 框架
- 包含正面和负面测试用例

## 文档

### 更新文档
- API文档：更新代码中的docstring
- 用户文档：更新 `README.md` 和 `QUICK_START.md`
- 开发文档：更新 `CONTRIBUTING.md`

### 文档规范
- 使用中文编写（主要用户是中文用户）
- 包含代码示例
- 保持更新

## 问题反馈

### 报告Bug
1. 查看现有Issue，避免重复
2. 创建新Issue，包含：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息

### 功能请求
1. 描述功能需求
2. 说明使用场景
3. 提供参考实现（如果有）

## 代码审查

### 提交Pull Request
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request
5. 等待代码审查

### 审查标准
- 代码符合规范
- 包含适当的测试
- 更新相关文档
- 不破坏现有功能

## 发布流程

### 版本管理
使用语义化版本：
- `MAJOR.MINOR.PATCH`
- 重大更新：`MAJOR+1.0.0`
- 新功能：`MINOR+1.PATCH`
- Bug修复：`PATCH+1`

### 发布步骤
1. 更新版本号
2. 更新CHANGELOG.md
3. 创建Git标签
4. 发布到GitHub

## 行为准则

### 我们的承诺
我们致力于为所有贡献者营造一个开放、友好的环境。

### 我们的标准
- 使用友好和尊重的语言
- 尊重不同的观点和经验
- 接受建设性批评
- 关注社区的最佳利益

### 不可接受的行为
- 使用性暗示语言或图像
- 挑衅、侮辱或贬损性评论
- 公开或私下骚扰
- 发布他人的私人信息

## 联系方式

- 项目维护者：六花 (Rikka)
- 问题反馈：GitHub Issues
- 讨论交流：GitHub Discussions

感谢你的贡献！🌸