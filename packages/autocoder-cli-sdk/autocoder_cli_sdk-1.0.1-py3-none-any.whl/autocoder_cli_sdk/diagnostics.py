"""
AutoCoder CLI SDK 诊断工具

提供诊断功能来帮助用户排查问题和检查环境配置。
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from .client import SDK_AVAILABLE, AutoCoderClient


def run_diagnostics(verbose: bool = False) -> Dict[str, Any]:
    """
    运行完整的诊断检查

    Args:
        verbose: 是否输出详细信息

    Returns:
        诊断结果字典
    """
    results = {
        "environment": check_environment(),
        "dependencies": check_dependencies(),
        "autocoder": check_autocoder(),
        "sdk": check_sdk_functionality(),
    }

    if verbose:
        print_diagnostics(results)

    return results


def check_environment() -> Dict[str, Any]:
    """检查Python环境"""
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": sys.platform,
        "cwd": str(Path.cwd()),
    }


def check_dependencies() -> Dict[str, Any]:
    """检查依赖包"""
    deps = {}

    required_packages = ["pydantic", "psutil"]
    optional_packages = ["autocoder"]

    for package in required_packages:
        try:
            __import__(package)
            deps[package] = {"available": True, "required": True}
        except ImportError:
            deps[package] = {"available": False, "required": True}

    for package in optional_packages:
        try:
            __import__(package)
            deps[package] = {"available": True, "required": False}
        except ImportError:
            deps[package] = {"available": False, "required": False}

    return deps


def check_autocoder() -> Dict[str, Any]:
    """检查auto-coder.run命令"""
    result = {
        "command_exists": False,
        "command_works": False,
        "version": "unknown",
        "path": None,
    }

    try:
        # 直接运行 auto-coder.run --help 来检测命令是否存在（超时600秒）
        help_result = subprocess.run(
            ["auto-coder.run", "--help"],
            capture_output=True,
            text=True,
            timeout=600,
        )

        if help_result.returncode == 0:
            result["command_exists"] = True
            result["command_works"] = True

            # 获取命令路径
            try:
                which_result = subprocess.run(
                    ["which", "auto-coder.run"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if which_result.returncode == 0:
                    result["path"] = which_result.stdout.strip()
            except Exception:
                pass

            # 获取版本
            try:
                version_result = subprocess.run(
                    ["auto-coder.run", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if version_result.returncode == 0:
                    result["version"] = version_result.stdout.strip()
            except Exception:
                pass

    except Exception as e:
        result["error"] = str(e)

    return result


def check_sdk_functionality() -> Dict[str, Any]:
    """检查SDK功能"""
    result = {
        "sdk_available": SDK_AVAILABLE,
        "client_creation": False,
        "basic_methods": {},
    }

    try:
        # 尝试创建客户端
        client = AutoCoderClient()
        result["client_creation"] = True

        # 测试基本方法
        methods_to_test = {
            "get_version": lambda: client.get_version(),
            "is_running": lambda: client.is_running(),
            "abort": lambda: client.abort(),
            "check_availability": lambda: client.check_availability(),
        }

        for method_name, method_func in methods_to_test.items():
            try:
                method_result = method_func()
                result["basic_methods"][method_name] = {
                    "works": True,
                    "result": str(method_result)[:100],  # 限制长度
                }
            except Exception as e:
                result["basic_methods"][method_name] = {
                    "works": False,
                    "error": str(e),
                }

    except Exception as e:
        result["client_creation_error"] = str(e)

    return result


def print_diagnostics(results: Dict[str, Any]) -> None:
    """打印诊断结果"""
    print("🔍 AutoCoder CLI SDK 诊断报告")
    print("=" * 50)

    # 环境信息
    env = results["environment"]
    print("\n📋 环境信息:")
    print(f"   Python版本: {env['python_version']}")
    print(f"   平台: {env['platform']}")
    print(f"   工作目录: {env['cwd']}")

    # 依赖检查
    deps = results["dependencies"]
    print("\n📦 依赖检查:")
    for package, info in deps.items():
        status = "✅" if info["available"] else "❌"
        required = "(必需)" if info["required"] else "(可选)"
        print(f"   {status} {package} {required}")

    # AutoCoder命令检查
    autocoder = results["autocoder"]
    print("\n🛠️  AutoCoder命令:")
    print(f"   命令存在: {'✅' if autocoder['command_exists'] else '❌'}")
    print(f"   命令工作: {'✅' if autocoder['command_works'] else '❌'}")
    print(f"   版本: {autocoder['version']}")
    if autocoder.get("path"):
        print(f"   路径: {autocoder['path']}")
    if autocoder.get("error"):
        print(f"   错误: {autocoder['error']}")

    # SDK功能检查
    sdk = results["sdk"]
    print("\n🐍 SDK功能:")
    print(f"   内部SDK可用: {'✅' if sdk['sdk_available'] else '❌'}")
    print(f"   客户端创建: {'✅' if sdk['client_creation'] else '❌'}")

    if sdk.get("client_creation_error"):
        print(f"   创建错误: {sdk['client_creation_error']}")

    if sdk["basic_methods"]:
        print("   基础方法:")
        for method, info in sdk["basic_methods"].items():
            status = "✅" if info["works"] else "❌"
            print(f"     {status} {method}")
            if not info["works"]:
                print(f"       错误: {info['error']}")

    print("\n" + "=" * 50)


def get_recommendations(results: Dict[str, Any]) -> List[str]:
    """根据诊断结果提供建议"""
    recommendations = []

    # 检查必需依赖
    deps = results["dependencies"]
    for package, info in deps.items():
        if info["required"] and not info["available"]:
            recommendations.append(
                f"安装缺失的必需依赖: pip install {package}"
            )

    # 检查AutoCoder命令
    autocoder = results["autocoder"]
    if not autocoder["command_exists"]:
        recommendations.append(
            "auto-coder.run 命令不存在，请安装AutoCoder或确保命令在PATH中"
        )
    elif not autocoder["command_works"]:
        recommendations.append(
            "auto-coder.run 命令存在但无法正常工作，请检查安装"
        )

    # 检查SDK功能
    sdk = results["sdk"]
    if not sdk["client_creation"]:
        recommendations.append("SDK客户端创建失败，请检查环境配置和依赖安装")

    if not recommendations:
        recommendations.append("✅ 所有检查都通过，SDK应该可以正常工作")

    return recommendations


if __name__ == "__main__":
    """运行诊断工具"""
    results = run_diagnostics(verbose=True)

    print("\n💡 建议:")
    recommendations = get_recommendations(results)
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
