#!/usr/bin/env python3
"""
开发脚本 - 使用uv运行常见的开发任务
"""

import sys
import subprocess
from pathlib import Path

def run_cmd(cmd):
    """运行命令"""
    print(f"运行: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent)

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/dev.py <命令>")
        print("可用命令:")
        print("  test      - 运行测试")
        print("  lint      - 代码检查")
        print("  format    - 代码格式化")
        print("  build     - 构建包")
        print("  example   - 运行示例")
        return 1
    
    cmd = sys.argv[1]
    
    if cmd == "test":
        return run_cmd(["uv", "run", "pytest", "tests/", "-v"]).returncode
    elif cmd == "lint":
        return run_cmd(["uv", "run", "flake8", "autocoder_cli_sdk/"]).returncode
    elif cmd == "format":
        run_cmd(["uv", "run", "black", "autocoder_cli_sdk/", "tests/", "examples/"])
        return run_cmd(["uv", "run", "isort", "autocoder_cli_sdk/", "tests/", "examples/"]).returncode
    elif cmd == "build":
        return run_cmd(["uv", "build"]).returncode
    elif cmd == "example":
        example_name = sys.argv[2] if len(sys.argv) > 2 else "basic_usage"
        return run_cmd(["uv", "run", "python", f"examples/{example_name}.py"]).returncode
    else:
        print(f"未知命令: {cmd}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
