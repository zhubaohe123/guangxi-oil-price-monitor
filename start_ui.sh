#!/bin/bash

# 广西油价监控系统 - 带UI界面启动脚本

echo "🌸 广西油价监控系统 - 带UI界面启动"
echo "======================================"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查是否已有容器在运行
if docker ps | grep -q "guangxi-oil-monitor-ui"; then
    echo "⚠️  检测到已有UI容器在运行，正在停止..."
    docker-compose -f docker-compose-with-ui.yml down
    sleep 2
fi

# 检查是否已有API容器在运行（端口8010）
if docker ps | grep -q "guangxi-oil-monitor"; then
    echo "ℹ️  检测到已有API容器在运行（端口8010）"
    echo "    UI应用将使用端口8011，两者可以共存"
fi

# 启动带UI的应用
echo "🚀 启动带UI界面的油价监控系统..."
docker-compose -f docker-compose-with-ui.yml up -d

# 等待应用启动
echo "⏳ 等待应用启动（约10秒）..."
sleep 10

# 检查应用状态
echo "🔍 检查应用状态..."
if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "✅ 应用启动成功！"
    echo ""
    echo "🌐 访问地址："
    echo "   UI界面：     http://localhost:8011/"
    echo "   API文档：    http://localhost:8011/api/docs"
    echo "   健康检查：   http://localhost:8011/health"
    echo "   今日油价API：http://localhost:8011/api/oil-prices/today"
    echo ""
    echo "🌍 公网访问（使用你的域名）："
    echo "   http://zbhly.icu:8011/"
    echo ""
    echo "📋 容器状态："
    docker ps | grep oil-monitor
else
    echo "❌ 应用启动失败，请检查日志："
    docker-compose -f docker-compose-with-ui.yml logs --tail=20
fi

echo ""
echo "🛠️  常用命令："
echo "   查看日志：docker-compose -f docker-compose-with-ui.yml logs -f"
echo "   停止应用：docker-compose -f docker-compose-with-ui.yml down"
echo "   重启应用：docker-compose -f docker-compose-with-ui.yml restart"