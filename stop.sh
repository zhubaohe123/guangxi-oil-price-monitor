#!/bin/bash

# 停止服务脚本

echo "正在停止广西油价监控分析系统..."

docker-compose down

echo "服务已停止"
echo ""
echo "数据保留在以下目录："
echo "- ./data/ - 数据库和图表文件"
echo "- ./logs/ - 日志文件"
echo "- ./config/ - 配置文件"
echo ""
echo "如需完全清理，可删除以上目录（数据将丢失）"