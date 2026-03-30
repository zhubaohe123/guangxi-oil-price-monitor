#!/bin/bash

echo "广西油价监控系统 - 部署测试"
echo "=============================="

# 清理旧容器
echo "1. 清理旧容器..."
docker ps -a | grep -E "(oil|guangxi)" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null

# 构建镜像
echo "2. 构建Docker镜像..."
docker build -t guangxi-oil-test .

if [ $? -ne 0 ]; then
    echo "❌ Docker构建失败"
    exit 1
fi

echo "✅ Docker构建成功"

# 测试主应用
echo "3. 测试主应用启动..."
docker run -d --name test-main -p 8009:8000 \
  -e OPENAI_API_KEY=test_key \
  guangxi-oil-test \
  sh -c 'cd /app && python -c "import sys; sys.path.insert(0, \"/app\"); from app.main_simple import app; import uvicorn; uvicorn.run(app, host=\"0.0.0.0\", port=8000)"'

sleep 10

# 检查容器状态
echo "4. 检查容器状态..."
if docker ps | grep -q test-main; then
    echo "✅ 主应用容器正在运行"
    
    # 测试健康检查
    echo "5. 测试API..."
    if curl -s http://localhost:8009/health > /dev/null; then
        echo "✅ 健康检查通过"
        
        echo "6. 测试油价API..."
        curl -s http://localhost:8009/api/oil-prices/today | python3 -m json.tool 2>/dev/null || echo "API响应: $(curl -s http://localhost:8009/api/oil-prices/today)"
        
    else
        echo "❌ 健康检查失败"
        docker logs test-main | tail -20
    fi
else
    echo "❌ 主应用容器未运行"
    docker logs test-main | tail -30
fi

# 清理测试容器
echo "7. 清理测试容器..."
docker rm -f test-main 2>/dev/null

echo ""
echo "测试完成！"
echo "如果所有测试通过，可以运行: docker-compose -f docker-compose-minimal.yml up -d"