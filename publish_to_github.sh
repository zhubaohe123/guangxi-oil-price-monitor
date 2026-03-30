#!/bin/bash

# 广西油价监控分析系统 - GitHub一键发布脚本

set -e

echo "========================================"
echo "广西油价监控分析系统 - GitHub发布"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在项目目录
if [ ! -f "docker-compose.yml" ]; then
    print_error "请在项目根目录运行此脚本"
    exit 1
fi

# 步骤1：检查Git状态
print_message "步骤1：检查Git状态..."
if [ ! -d ".git" ]; then
    print_message "初始化Git仓库..."
    git init
    print_success "Git仓库初始化完成"
else
    print_message "Git仓库已存在"
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    print_message "检测到未提交的更改"
    
    # 添加所有文件
    git add .
    
    # 提交更改
    git commit -m "发布准备: 广西油价监控分析系统 v1.0.0
    
    🎉 发布版本 1.0.0
    - 完整的多源数据收集功能
    - AI智能分析和加油推荐
    - 丰富的可视化图表
    - Docker一键部署
    - 完整的API文档
    
    📦 包含文件:
    - 完整的应用代码
    - Docker配置和部署文件
    - 详细的使用文档
    - GitHub Actions工作流
    - 贡献指南和许可证
    
    🌸 特别感谢:
    - 勇太 (Yuta) 的需求启发
    - DeepSeek团队的免费API
    - 所有开源贡献者"
    
    print_success "更改已提交"
else
    print_message "没有未提交的更改"
fi

# 步骤2：显示当前状态
print_message "步骤2：显示当前状态..."
echo ""
echo "当前分支: $(git branch --show-current)"
echo "提交数量: $(git rev-list --count HEAD)"
echo "最后提交: $(git log -1 --oneline)"
echo ""

# 步骤3：设置远程仓库
print_message "步骤3：设置远程仓库..."
read -p "请输入GitHub仓库URL（例如：https://github.com/你的用户名/guangxi-oil-price-monitor.git）: " repo_url

if [ -z "$repo_url" ]; then
    print_error "必须提供仓库URL"
    exit 1
fi

# 检查是否已设置远程仓库
if git remote | grep -q "origin"; then
    print_message "远程仓库已设置，更新URL..."
    git remote set-url origin "$repo_url"
else
    print_message "添加远程仓库..."
    git remote add origin "$repo_url"
fi

print_success "远程仓库设置完成: $repo_url"

# 步骤4：重命名分支（如果需要）
print_message "步骤4：配置分支..."
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    print_message "重命名分支为 main..."
    git branch -M main
fi

# 步骤5：推送到GitHub
print_message "步骤5：推送到GitHub..."
echo ""
print_warning "即将推送到GitHub，这会将所有代码上传到远程仓库"
read -p "是否继续？(y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_message "用户取消操作"
    exit 0
fi

print_message "推送代码到GitHub..."
if git push -u origin main; then
    print_success "代码推送成功！"
else
    print_error "代码推送失败"
    print_message "请检查："
    print_message "1. 网络连接"
    print_message "2. 仓库URL是否正确"
    print_message "3. 是否有推送权限"
    exit 1
fi

# 步骤6：创建版本标签
print_message "步骤6：创建版本标签..."
read -p "是否创建版本标签 v1.0.0？(y/N): " tag_confirm

if [[ $tag_confirm =~ ^[Yy]$ ]]; then
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
    - Docker容器化"
    
    git push origin v1.0.0
    print_success "版本标签 v1.0.0 创建并推送成功"
fi

# 步骤7：显示最终状态
print_message "步骤7：显示最终状态..."
echo ""
echo "========================================"
echo "发布完成！"
echo "========================================"
echo ""
echo "✅ 代码已成功推送到GitHub"
echo "✅ 仓库URL: $repo_url"
echo "✅ 分支: main"
if [[ $tag_confirm =~ ^[Yy]$ ]]; then
    echo "✅ 版本标签: v1.0.0"
fi
echo ""
echo "接下来你可以："
echo ""
echo "1. 访问GitHub仓库页面："
echo "   $repo_url"
echo ""
echo "2. 配置仓库设置："
echo "   - 添加仓库描述"
echo "   - 设置主题标签"
echo "   - 启用GitHub Pages"
echo "   - 配置分支保护规则"
echo ""
echo "3. 创建GitHub Release："
echo "   - 访问仓库的Releases页面"
echo "   - 点击 'Draft a new release'"
echo "   - 选择标签 v1.0.0"
echo "   - 编写发布说明"
echo "   - 上传相关文件"
echo ""
echo "4. 宣传项目："
echo "   - 在README中添加徽章"
echo "   - 在技术社区分享"
echo "   - 编写技术博客"
echo "   - 在社交媒体宣传"
echo ""
echo "5. 收集反馈："
echo "   - 启用GitHub Discussions"
echo "   - 设置Issue模板"
echo "   - 邀请用户测试"
echo "   - 收集使用案例"
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
echo "创建时间: $(date '+%Y年%m月%d日 %H:%M:%S')"
echo ""
echo "祝你的开源项目获得成功！ 🌸"
echo "========================================"

# 步骤8：打开GitHub仓库（可选）
read -p "是否在浏览器中打开GitHub仓库页面？(y/N): " open_browser

if [[ $open_browser =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "$repo_url"
    elif command -v open &> /dev/null; then
        open "$repo_url"
    else
        print_message "无法自动打开浏览器，请手动访问：$repo_url"
    fi
fi

print_success "发布流程完成！"