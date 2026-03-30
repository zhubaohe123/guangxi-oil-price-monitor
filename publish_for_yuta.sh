#!/bin/bash

# 专门为勇太准备的GitHub发布脚本

echo "🌸 勇太，我来帮你把项目发布到你的GitHub账号！"
echo "================================================"
echo ""

# 第一步：收集信息
echo "📝 请提供以下信息："
echo ""

# GitHub用户名
read -p "1. 你的GitHub用户名: " github_username
if [ -z "$github_username" ]; then
    echo "❌ 必须提供GitHub用户名"
    exit 1
fi

# 仓库名称（默认使用项目名称）
read -p "2. 仓库名称 [guangxi-oil-price-monitor]: " repo_name
repo_name=${repo_name:-"guangxi-oil-price-monitor"}

# 仓库描述
read -p "3. 仓库描述 [广西油价监控分析系统 - 免费AI油价分析和推荐]: " repo_description
repo_description=${repo_description:-"广西油价监控分析系统 - 免费AI油价分析和推荐"}

# 确认信息
echo ""
echo "✅ 收集到的信息："
echo "   GitHub用户名: $github_username"
echo "   仓库名称: $repo_name"
echo "   仓库描述: $repo_description"
echo ""

read -p "确认以上信息是否正确？(y/N): " confirm_info
if [[ ! $confirm_info =~ ^[Yy]$ ]]; then
    echo "❌ 用户取消操作"
    exit 0
fi

# 第二步：初始化Git
echo ""
echo "🔧 初始化Git仓库..."
cd guangxi-oil-price-monitor

# 设置Git用户信息
git config user.email "${github_username}@users.noreply.github.com"
git config user.name "$github_username"

# 初始化仓库（如果还没初始化）
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git仓库初始化完成"
else
    echo "✅ Git仓库已存在"
fi

# 第三步：添加和提交文件
echo ""
echo "📦 添加文件到Git..."
git add .

echo "💾 提交更改..."
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
- 六花 (Rikka) 的开发实现
- DeepSeek团队的免费API
- 所有开源数据源提供者"

echo "✅ 代码提交完成"

# 第四步：设置远程仓库
echo ""
echo "🌐 设置GitHub远程仓库..."
repo_url="https://github.com/${github_username}/${repo_name}.git"
echo "   仓库URL: $repo_url"

# 检查是否已设置远程仓库
if git remote | grep -q "origin"; then
    git remote set-url origin "$repo_url"
    echo "✅ 更新远程仓库URL"
else
    git remote add origin "$repo_url"
    echo "✅ 添加远程仓库"
fi

# 第五步：重命名分支
echo ""
echo "🌿 配置分支..."
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    git branch -M main
    echo "✅ 分支重命名为 main"
else
    echo "✅ 当前分支已经是 main"
fi

# 第六步：推送到GitHub
echo ""
echo "🚀 准备推送到GitHub..."
echo ""
echo "⚠️  注意："
echo "   1. 确保你在GitHub上已经创建了仓库 '$repo_name'"
echo "   2. 仓库应该是公开的"
echo "   3. 不要初始化README、.gitignore或许可证"
echo ""
read -p "是否已经在GitHub创建了仓库？(y/N): " repo_created

if [[ ! $repo_created =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 请在GitHub上创建仓库："
    echo "   1. 访问 https://github.com/new"
    echo "   2. 仓库名: $repo_name"
    echo "   3. 描述: $repo_description"
    echo "   4. 选择公开仓库"
    echo "   5. 不要初始化README、.gitignore或许可证"
    echo "   6. 点击创建仓库"
    echo ""
    read -p "创建完成后按回车键继续..." dummy
fi

echo ""
echo "📤 推送到GitHub..."
if git push -u origin main; then
    echo "🎉 代码推送成功！"
else
    echo ""
    echo "❌ 推送失败，可能的原因："
    echo "   1. 仓库不存在或URL错误"
    echo "   2. 没有推送权限"
    echo "   3. 网络连接问题"
    echo ""
    echo "💡 解决方案："
    echo "   1. 确认仓库URL: $repo_url"
    echo "   2. 确认仓库已创建且为公开"
    echo "   3. 检查GitHub账号权限"
    exit 1
fi

# 第七步：创建版本标签
echo ""
echo "🏷️ 创建版本标签..."
read -p "是否创建版本标签 v1.0.0？(y/N): " create_tag

if [[ $create_tag =~ ^[Yy]$ ]]; then
    git tag -a v1.0.0 -m "初始版本发布

版本 1.0.0 - 广西油价监控分析系统

主要功能：
- 多源免费油价数据收集
- AI智能分析和加油推荐
- 丰富的可视化图表
- Docker一键部署
- 完整的RESTful API

技术栈：
- FastAPI + SQLAlchemy
- Plotly可视化
- DeepSeek AI分析
- Docker容器化

开发者：六花 (Rikka)
需求提出：勇太 (Yuta)"

    git push origin v1.0.0
    echo "✅ 版本标签 v1.0.0 创建并推送成功"
fi

# 第八步：显示成功信息
echo ""
echo "========================================"
echo "🎉 发布成功！"
echo "========================================"
echo ""
echo "✅ 项目已成功发布到你的GitHub账号！"
echo ""
echo "📊 项目信息："
echo "   仓库地址: https://github.com/${github_username}/${repo_name}"
echo "   你的账号: $github_username"
echo "   项目名称: $repo_name"
echo "   版本: 1.0.0"
echo ""
echo "🚀 接下来你可以："
echo ""
echo "1. 访问仓库页面："
echo "   https://github.com/${github_username}/${repo_name}"
echo ""
echo "2. 配置仓库设置："
echo "   - 添加仓库描述: '$repo_description'"
echo "   - 设置主题标签: oil-price, guangxi, docker, fastapi, ai-analysis"
echo "   - 添加项目徽章（可选）"
echo ""
echo "3. 测试项目部署："
echo "   chmod +x start.sh"
echo "   ./start.sh"
echo "   # 访问 http://localhost:8000/docs"
echo ""
echo "4. 分享项目："
echo "   - 在技术社区分享"
echo "   - 邀请朋友Star"
echo "   - 收集用户反馈"
echo ""
echo "5. 后续维护："
echo "   - 及时回复Issue"
echo "   - 定期更新依赖"
echo "   - 添加新功能"
echo ""
echo "🌸 特别说明："
echo "   这个项目是由六花 (Rikka) 为你开发的"
echo "   你是项目的所有者和维护者"
echo "   感谢你提出这个有趣的需求！"
echo ""
echo "========================================"
echo "祝你开源愉快！ 🌸"
echo "========================================"

# 第九步：打开仓库页面
echo ""
read -p "是否在浏览器中打开GitHub仓库页面？(y/N): " open_browser

if [[ $open_browser =~ ^[Yy]$ ]]; then
    repo_url="https://github.com/${github_username}/${repo_name}"
    if command -v xdg-open &> /dev/null; then
        xdg-open "$repo_url"
    elif command -v open &> /dev/null; then
        open "$repo_url"
    else
        echo "🌐 请手动访问: $repo_url"
    fi
fi

echo ""
echo "✅ 发布流程完成！"