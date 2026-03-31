#!/bin/bash

echo "调试广西油价监控应用"
echo "======================"

# 清理旧容器
echo "1. 清理旧容器..."
docker rm -f guangxi-oil-monitor-debug 2>/dev/null

# 构建镜像
echo "2. 构建镜像..."
docker build -t guangxi-oil-debug .

# 运行容器并查看日志
echo "3. 启动应用并查看日志..."
docker run --name guangxi-oil-monitor-debug \
  -p 8020:8000 \
  -e OPENAI_API_KEY=test_key \
  -e LOG_LEVEL=DEBUG \
  guangxi-oil-debug \
  sh -c 'cd /app && python -c "
import sys
sys.path.insert(0, \"/app\")
print(\"Python路径:\", sys.path)

try:
    print(\"尝试导入配置...\")
    from app.config_simple import settings
    print(f\"✅ 配置导入成功: {settings.app_name}\")
except Exception as e:
    print(f\"❌ 配置导入失败: {e}\")
    import traceback
    traceback.print_exc()

try:
    print(\"尝试导入主应用...\")
    from app.main_simple import app
    print(\"✅ 主应用导入成功\")
    
    import uvicorn
    print(\"启动uvicorn...\")
    uvicorn.run(app, host=\"0.0.0.0\", port=8000, log_level=\"debug\")
    
except Exception as e:
    print(f\"❌ 应用启动失败: {e}\")
    import traceback
    traceback.print_exc()
    print(\"等待60秒以便查看日志...\")
    import time
    time.sleep(60)
"'

# 查看日志
echo "4. 查看应用日志..."
docker logs -f guangxi-oil-monitor-debug