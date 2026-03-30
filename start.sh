#!/bin/bash

# 广西油价监控分析系统启动脚本

set -e

echo "========================================"
echo "广西油价监控分析系统"
echo "========================================"

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    exit 1
fi

# 检查环境文件
if [ ! -f .env ]; then
    echo "警告: .env文件不存在，使用示例配置"
    cp .env.example .env
    echo "请编辑 .env 文件配置API密钥和其他设置"
    read -p "按回车键继续或 Ctrl+C 取消..."
fi

# 创建必要目录
mkdir -p data logs config

# 启动服务
echo "正在启动服务..."
docker-compose up -d

echo ""
echo "服务启动完成！"
echo ""
echo "访问以下地址："
echo "- API文档: http://localhost:8000/docs"
echo "- 健康检查: http://localhost:8000/health"
echo "- 配置文件: ./config/"
echo "- 数据目录: ./data/"
echo "- 日志目录: ./logs/"
echo ""
echo "管理命令："
echo "- 查看日志: docker-compose logs -f"
echo "- 停止服务: docker-compose down"
echo "- 重启服务: docker-compose restart"
echo "- 更新服务: docker-compose pull && docker-compose up -d"
echo ""
echo "首次运行建议："
echo "1. 访问 http://localhost:8000/docs 查看API文档"
echo "2. 检查日志确保服务正常运行: docker-compose logs oil-monitor"
echo "3. 等待定时任务执行数据收集和分析"
echo "========================================"