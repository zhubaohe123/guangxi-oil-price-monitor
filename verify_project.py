#!/usr/bin/env python3
"""
项目结构验证脚本
检查所有必要文件是否就绪
"""
import os
import sys
from pathlib import Path

# 必需的文件列表
REQUIRED_FILES = [
    # 根目录文件
    "README.md",
    "QUICK_START.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "LICENSE",
    ".gitignore",
    "docker-compose.yml",
    "Dockerfile",
    "requirements.txt",
    ".env.example",
    "start.sh",
    "stop.sh",
    
    # 应用目录
    "app/main.py",
    "app/config.py",
    "app/database/__init__.py",
    "app/database/models.py",
    "app/collectors/real_oil_price_collector.py",
    "app/collectors/news_collector.py",
    "app/analyzers/ai_analyzer.py",
    "app/visualizers/chart_generator.py",
    "app/routers/oil_prices.py",
    
    # GitHub配置
    ".github/workflows/test.yml",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
]

# 建议的文件列表
RECOMMENDED_FILES = [
    "docker-compose.prod.yml",
    "init_git.sh",
    "publish_to_github.sh",
    "PUBLISH_CHECKLIST.md",
    "verify_project.py",
]

def check_file_exists(filepath):
    """检查文件是否存在"""
    path = Path(filepath)
    if path.exists():
        return True, path.stat().st_size
    return False, 0

def main():
    print("🔍 广西油价监控分析系统 - 项目结构验证")
    print("=" * 50)
    
    # 检查当前目录
    current_dir = Path.cwd()
    print(f"当前目录: {current_dir}")
    print()
    
    # 检查必需文件
    print("📋 检查必需文件:")
    print("-" * 30)
    
    missing_files = []
    existing_files = []
    
    for filepath in REQUIRED_FILES:
        exists, size = check_file_exists(filepath)
        if exists:
            status = "✅"
            existing_files.append((filepath, size))
        else:
            status = "❌"
            missing_files.append(filepath)
        
        print(f"{status} {filepath}")
    
    print()
    
    # 检查建议文件
    print("📋 检查建议文件:")
    print("-" * 30)
    
    for filepath in RECOMMENDED_FILES:
        exists, size = check_file_exists(filepath)
        status = "✅" if exists else "⚠️ "
        print(f"{status} {filepath}")
    
    print()
    
    # 显示统计信息
    total_required = len(REQUIRED_FILES)
    total_existing = len(existing_files)
    total_missing = len(missing_files)
    
    print("📊 统计信息:")
    print(f"必需文件总数: {total_required}")
    print(f"已存在文件: {total_existing}")
    print(f"缺失文件: {total_missing}")
    
    if total_missing > 0:
        print()
        print("❌ 缺失的必需文件:")
        for filepath in missing_files:
            print(f"  - {filepath}")
    
    # 计算文件总大小
    total_size = sum(size for _, size in existing_files)
    print()
    print(f"📦 项目总大小: {total_size / 1024:.2f} KB")
    
    # 检查Docker配置
    print()
    print("🐳 检查Docker配置:")
    print("-" * 30)
    
    docker_files = ["Dockerfile", "docker-compose.yml", "requirements.txt"]
    for filepath in docker_files:
        exists, size = check_file_exists(filepath)
        if exists:
            # 检查文件内容
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    print(f"✅ {filepath}: {lines} 行, {size} 字节")
            except Exception as e:
                print(f"❌ {filepath}: 读取失败 - {e}")
        else:
            print(f"❌ {filepath}: 文件缺失")
    
    # 检查Python依赖
    print()
    print("🐍 检查Python依赖:")
    print("-" * 30)
    
    if check_file_exists("requirements.txt")[0]:
        try:
            with open("requirements.txt", 'r', encoding='utf-8') as f:
                dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                print(f"✅ requirements.txt: {len(dependencies)} 个依赖")
                print("   主要依赖:")
                for dep in dependencies[:10]:  # 显示前10个
                    print(f"    - {dep}")
                if len(dependencies) > 10:
                    print(f"    ... 还有 {len(dependencies) - 10} 个依赖")
        except Exception as e:
            print(f"❌ 读取requirements.txt失败: {e}")
    else:
        print("❌ requirements.txt: 文件缺失")
    
    # 检查应用结构
    print()
    print("🏗️ 检查应用结构:")
    print("-" * 30)
    
    app_dirs = ["app", "app/database", "app/collectors", "app/analyzers", "app/visualizers", "app/routers"]
    for dirpath in app_dirs:
        path = Path(dirpath)
        if path.exists() and path.is_dir():
            # 统计Python文件
            py_files = list(path.glob("*.py"))
            print(f"✅ {dirpath}/: {len(py_files)} 个Python文件")
        else:
            print(f"❌ {dirpath}/: 目录缺失")
    
    # 总体评估
    print()
    print("📈 总体评估:")
    print("=" * 50)
    
    completion_rate = (total_existing / total_required) * 100
    
    if completion_rate == 100:
        print("🎉 完美！所有必需文件都已就绪")
        print("   项目已准备好发布到GitHub")
    elif completion_rate >= 90:
        print("👍 很好！项目基本就绪")
        print(f"   完成度: {completion_rate:.1f}%")
        print("   建议补充缺失文件后再发布")
    elif completion_rate >= 70:
        print("⚠️ 项目结构基本完整")
        print(f"   完成度: {completion_rate:.1f}%")
        print("   需要补充重要文件")
    else:
        print("❌ 项目结构不完整")
        print(f"   完成度: {completion_rate:.1f}%")
        print("   需要补充大量文件")
    
    print()
    print("🚀 下一步建议:")
    print("-" * 30)
    
    if missing_files:
        print("1. 补充缺失的必需文件")
        for filepath in missing_files[:5]:  # 只显示前5个
            print(f"   - 创建 {filepath}")
        if len(missing_files) > 5:
            print(f"   ... 还有 {len(missing_files) - 5} 个文件")
    
    print("2. 运行测试验证功能")
    print("   python verify_project.py")
    
    print("3. 使用发布脚本上传到GitHub")
    print("   chmod +x publish_to_github.sh")
    print("   ./publish_to_github.sh")
    
    print()
    print("🌸 项目信息:")
    print(f"   名称: 广西油价监控分析系统")
    print(f"   版本: 1.0.0")
    print(f"   许可证: MIT")
    print(f"   验证时间: {os.popen('date').read().strip()}")
    
    return 0 if completion_rate >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())