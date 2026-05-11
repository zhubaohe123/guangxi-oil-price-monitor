# 🐛 Bug 修复计划 - 广西油价监控分析系统

> 生成时间：2026-05-11
> 基于代码审查发现的问题

---

## 一、问题总览

| 优先级 | 数量 | 说明 |
|--------|------|------|
| P0 紧急 | 4 | 程序无法启动或核心功能崩溃 |
| P1 重要 | 4 | 逻辑错误、功能缺陷 |
| P2 一般 | 3 | 代码质量问题 |

---

## 二、修复计划

### 🔴 P0 - 紧急修复（不修程序跑不起来）

#### BUG-001：异步/同步 Session 混用
- **文件：** oil_price_collector.py, news_collector.py, ai_analyzer.py, chart_generator.py
- **原因：** `database_sync.py` 导出同步 `Session`，但调用方全用 `await session.xxx()`
- **修复方案：** 统一为异步架构，创建 `database.py` 异步模块
  - 新建 `app/database/async_session.py`（使用 aiosqlite）
  - 修改 `get_session()` 返回 AsyncSession
  - 所有 `await session.execute()` / `await session.commit()` 保持不变
  - 删除 `database_sync.py`（或改为兼容层）
- **涉及文件：** 5 个
- **预计耗时：** 1 小时

#### BUG-002：main.py 路由导入缺失
- **文件：** app/main.py
- **原因：** 路由导入被注释掉，但下面仍在使用
- **修复方案：**
  ```python
  # 取消注释：
  from app.routers import oil_prices, analysis, charts, news
  ```
  - 如果 analysis/charts/news 路由文件不存在，需要创建占位文件
- **涉及文件：** 1-4 个
- **预计耗时：** 30 分钟

#### BUG-003：oil_prices.py 路由重复定义
- **文件：** app/routers/oil_prices.py
- **原因：** 文件后半部分重复粘贴了相同代码
- **修复方案：** 删除重复的路由函数定义，只保留一份
- **涉及文件：** 1 个
- **预计耗时：** 15 分钟

#### BUG-004：oil_prices.py 死代码
- **文件：** app/routers/oil_prices.py
- **原因：** `get_data_sources()` 中 return 后还有大量代码
- **修复方案：** 删除 return 之后的 unreachable code，或将其移到独立函数
- **涉及文件：** 1 个
- **预计耗时：** 10 分钟

---

### 🟡 P1 - 重要修复（逻辑错误）

#### BUG-005：config.py dataclass 误用 pydantic Field
- **文件：** app/config.py
- **原因：** `@dataclass` 中使用了 `Field(..., env="...")`
- **修复方案：**
  - 方案A：改用 pydantic `BaseSettings`（推荐）
  - 方案B：改用 `os.getenv()` 写法（与 config_simple.py 一致）
- **涉及文件：** 1 个
- **预计耗时：** 20 分钟

#### BUG-006：scheduler.py 定时任务为空壳
- **文件：** app/scheduler.py
- **原因：** `collect_oil_prices()` 和 `analyze_prices()` 只打印日志
- **修复方案：**
  ```python
  def collect_oil_prices():
      from app.collectors.oil_price_collector import collector
      import asyncio
      asyncio.run(collector.collect_all_regions())
  
  def analyze_prices():
      from app.analyzers.ai_analyzer import analyzer
      import asyncio
      asyncio.run(analyzer.analyze_daily_prices())
  ```
  - 或改用 `AsyncIOScheduler` 替代 `BackgroundScheduler`
- **涉及文件：** 1 个
- **预计耗时：** 30 分钟

#### BUG-007：health_check 硬编码时间戳
- **文件：** app/main.py
- **原因：** `"timestamp": "2026-03-30T14:44:00Z"` 写死
- **修复方案：**
  ```python
  from datetime import datetime, timezone
  "timestamp": datetime.now(timezone.utc).isoformat()
  ```
- **涉及文件：** 1 个
- **预计耗时：** 5 分钟

#### BUG-008：真实爬虫未实现
- **文件：** app/collectors/oil_price_collector.py
- **原因：** `collect_from_website()` 只有占位代码
- **修复方案：** 实现至少一个数据源（如易车网）的解析逻辑
- **涉及文件：** 1 个
- **预计耗时：** 1-2 小时

---

### 🟢 P2 - 一般修复（代码质量）

#### BUG-009：news_collector.py 异常处理隐患
- **文件：** app/collectors/news_collector.py
- **原因：** `if 'session' in locals()` 可能引用未初始化的 session
- **修复方案：** 用 try/finally 确保 session 正确关闭

#### BUG-010：缺少 .env.example 完整内容
- **文件：** .env.example
- **修复方案：** 补充所有必需环境变量的示例值

#### BUG-011：main.py lifespan 中 init_db 调用方式
- **文件：** app/main.py
- **原因：** `await init_db()` 但 init_db 是同步函数
- **修复方案：** 去掉 await 或改为异步版本

---

## 三、修复顺序

```
Phase 1（基础架构）：
  ├── BUG-001：统一异步/同步架构
  ├── BUG-002：修复路由导入
  └── BUG-003 + BUG-004：清理 oil_prices.py

Phase 2（功能修复）：
  ├── BUG-005：修复配置类
  ├── BUG-006：让定时任务真正工作
  └── BUG-007：修复健康检查

Phase 3（增强）：
  ├── BUG-008：实现真实爬虫
  ├── BUG-009：改善异常处理
  └── BUG-010：完善文档
```

---

## 四、修复后验证

1. `python -m app.main` 能正常启动
2. `GET /health` 返回实时时间戳
3. `GET /docs` 能看到完整 API 文档
4. `POST /api/oil-prices/collect` 能收集模拟数据
5. 定时任务能正确触发
6. 无 import 错误

---

## 五、注意事项

- 修复前建议先创建 git 分支：`git checkout -b fix/bug-fixes`
- BUG-008（真实爬虫）工作量较大，可以后续单独迭代
- 建议引入 `pytest` 做基础测试
