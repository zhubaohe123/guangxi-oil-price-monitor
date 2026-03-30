#!/bin/bash

# 广西油价监控分析系统 - Git仓库初始化脚本

set -e

echo "========================================"
echo "广西油价监控分析系统 - GitHub发布准备"
echo "========================================"

# 检查是否在项目目录
if [ ! -f "docker-compose.yml" ]; then
    echo "错误：请在项目根目录运行此脚本"
    exit 1
fi

# 初始化Git仓库
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    echo "Git仓库初始化完成"
else
    echo "Git仓库已存在"
fi

# 添加所有文件
echo "添加文件到Git..."
git add .

# 检查是否有未提交的更改
if git diff --cached --quiet; then
    echo "没有需要提交的更改"
else
    # 提交更改
    echo "提交更改..."
    git commit -m "初始提交: 广西油价监控分析系统 v1.0.0
    
    🎉 功能特性:
    - 🛢️ 多源免费油价数据收集
    - 🤖 AI智能分析和加油推荐
    - 📊 丰富可视化图表
    - 🐳 Docker一键部署
    - 🔧 完整RESTful API
    
    📋 技术栈:
    - FastAPI + SQLAlchemy
    - Plotly可视化
    - DeepSeek AI分析
    - Docker容器化
    
    🌸 特别感谢:
    - 勇太 (Yuta) 的需求启发
    - DeepSeek团队的免费API
    - 所有开源数据源提供者"
    
    echo "提交完成"
fi

# 显示Git状态
echo ""
echo "当前Git状态:"
git status

# 显示远程仓库信息
echo ""
echo "远程仓库配置:"
git remote -v

# 显示分支信息
echo ""
echo "分支信息:"
git branch -a

# 显示提交历史
echo ""
echo "最近提交:"
git log --oneline -5

echo ""
echo "========================================"
echo "GitHub发布指南"
echo "========================================"
echo ""
echo "1. 在GitHub创建新仓库:"
echo "   - 访问 https://github.com/new"
echo "   - 仓库名: guangxi-oil-price-monitor"
echo "   - 描述: 广西油价监控分析系统 - 免费AI油价分析和推荐"
echo "   - 选择公开仓库"
echo "   - 不要初始化README、.gitignore或许可证"
echo ""
echo "2. 添加远程仓库并推送:"
echo "   git remote add origin https://github.com/你的用户名/guangxi-oil-price-monitor.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. 配置GitHub Actions secrets (可选):"
echo "   - DOCKER_USERNAME: Docker Hub用户名"
echo "   - DOCKER_PASSWORD: Docker Hub密码"
echo "   - OPENAI_API_KEY: DeepSeek API密钥 (用于CI测试)"
echo ""
echo "4. 启用GitHub Pages (可选):"
echo "   - 设置 > Pages > 分支: gh-pages"
echo "   - 文件夹: /docs"
echo ""
echo "5. 添加仓库标签:"
echo "   - oil-price"
echo "   - guangxi"
echo "   - docker"
echo "   - fastapi"
echo "   - ai-analysis"
echo "   - chinese"
echo ""
echo "6. 创建第一个Release:"
echo "   - 标签: v1.0.0"
echo "   - 标题: 初始版本发布"
echo "   - 描述: 包含完整功能的广西油价监控分析系统"
echo "   - 上传文件: docker-compose.yml, README.md, QUICK_START.md"
echo ""
echo "========================================"
echo "下一步建议"
echo "========================================"
echo ""
echo "1. 测试部署流程:"
echo "   ./start.sh"
echo "   docker-compose ps"
echo "   curl http://localhost:8000/health"
echo ""
echo "2. 更新配置文件:"
echo "   - 编辑 README.md 中的GitHub链接"
echo "   - 更新 .github/workflows/test.yml 中的Docker用户名"
echo "   - 检查所有配置文件中的占位符"
echo ""
echo "3. 创建演示视频或截图:"
echo "   - API文档界面"
echo "   - 图表展示"
echo "   - Docker部署过程"
echo ""
echo "4. 宣传项目:"
echo "   - 在技术社区分享"
echo "   - 编写技术博客"
echo "   - 在社交媒体宣传"
echo ""
echo "5. 收集用户反馈:"
echo "   - 启用GitHub Discussions"
echo "   - 设置Issue模板"
echo "   - 创建用户调查"
echo ""
echo "========================================"
echo "项目信息"
echo "========================================"
echo ""
echo "项目名称: 广西油价监控分析系统"
echo "版本: 1.0.0"
echo "许可证: MIT"
echo "主要开发者: 六花 (Rikka)"
echo "需求提出: 勇太 (Yuta)"
echo "创建时间: 2026年3月30日"
echo ""
echo "祝你的项目在GitHub上获得成功！ 🌸"
echo "========================================"