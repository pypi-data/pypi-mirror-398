"""
简化发布脚本 - 直接使用命令行上传
"""

import os
import subprocess
import sys

def main():
    """直接发布到 PyPI"""
    print("🚀 发布 data-wise-location-mcp-server 到 PyPI")
    print("=" * 50)
    
    # 检查 dist 目录
    if not os.path.exists("dist"):
        print("❌ dist 目录不存在，请先运行: python -m build")
        sys.exit(1)
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
    
    # 直接设置 token
    token = "pypi-AgEIcHlwaS5vcmcCJDdhNzZiNDEzLTQ4YWItNDJmMi1hMThjLWNkMjJkNDM2ZWRkOQACKlszLCI4NTJlMDBiMi1mNTBhLTQ3OTQtYTBmZS02NTNjNzViY2Y3NzciXQAABiD2DGMTWUI9G0vhPdQy-KghtEA1Y9ejoGBsBi3GSmzqtA"
    env['TWINE_USERNAME'] = '__token__'
    env['TWINE_PASSWORD'] = token
    
    print("📦 开始上传...")
    
    # 直接使用 twine 上传
    cmd = ["python", "-m", "twine", "upload", "dist/*"]
    
    try:
        result = subprocess.run(cmd, env=env)
        if result.returncode == 0:
            print("\n🎉 发布成功!")
            print("📦 安装命令: pip install data-wise-location-mcp-server")
            print("🚀 运行命令: data-wise-location-mcp-server")
            print("🔧 uvx 使用: uvx data-wise-location-mcp-server")
        else:
            print("\n❌ 发布失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发布异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
