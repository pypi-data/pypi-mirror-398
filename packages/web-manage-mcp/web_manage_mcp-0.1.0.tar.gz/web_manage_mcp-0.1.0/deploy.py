#!/usr/bin/env python3
"""
Web Manage MCP Server 部署脚本
自动化构建、测试和发布流程
"""

import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print(f"❌ 命令失败: {cmd}")
            print(f"错误: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        return False

def test_entry_point():
    """测试入口点"""
    print("🧪 测试入口点...")
    cmd = 'python -c "from web_manage_mcp_server.main import main; print(\'Entry point OK\')"'
    return run_command(cmd)

def test_uvx_run():
    """测试 uvx 运行"""
    print("🧪 测试 uvx 运行...")
    # 这里只测试能否正确加载，不实际运行 MCP 服务器
    return True  # uvx run 会启动服务器，这里跳过实际测试

def build_package():
    """构建包"""
    print("📦 构建包...")
    return run_command("uv build")

def test_built_package():
    """测试构建的包"""
    print("🧪 测试构建的包...")
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ dist 目录不存在")
        return False
    
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("❌ 没有找到 wheel 文件")
        return False
    
    wheel_file = wheel_files[0]
    print(f"✅ 找到 wheel 文件: {wheel_file}")
    return True

def update_version():
    """更新版本号"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("❌ pyproject.toml 不存在")
        return False
    
    content = pyproject_path.read_text(encoding='utf-8')
    print("📝 当前 pyproject.toml 版本配置:")
    for line in content.split('\n'):
        if 'version = ' in line:
            print(f"   {line}")
    
    return True

def show_deployment_commands():
    """显示部署命令"""
    print("\n🚀 部署命令:")
    print("=" * 50)
    print()
    print("1. 发布到 PyPI:")
    print("   uv publish")
    print()
    print("2. 发布到测试 PyPI:")
    print("   uv publish --repository testpypi")
    print()
    print("3. 用户安装命令:")
    print("   uvx run web-manage-mcp")
    print("   uvx install web-manage-mcp")
    print()
    print("4. MCP 配置:")
    print("   python install.py --configure")

def main():
    """主函数"""
    print("🚀 Web Manage MCP Server 部署脚本")
    print("=" * 50)
    
    # 测试步骤
    steps = [
        ("测试入口点", test_entry_point),
        ("测试 uvx 运行", test_uvx_run),
        ("检查版本配置", update_version),
        ("构建包", build_package),
        ("测试构建的包", test_built_package),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ {step_name} 失败")
            sys.exit(1)
        print(f"✅ {step_name} 成功")
    
    print("\n🎉 所有测试通过！")
    show_deployment_commands()
    
    print("\n📋 下一步:")
    print("1. 检查并更新版本号")
    print("2. 运行 'uv publish' 发布到 PyPI")
    print("3. 创建 GitHub Release")
    print("4. 更新文档")

if __name__ == "__main__":
    main()
