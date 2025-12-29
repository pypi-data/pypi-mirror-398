"""
AutoCoder CLI SDK 基础用法示例

演示如何使用SDK进行基本的代码生成和配置操作。
"""

import os
import sys
from pathlib import Path

# 添加SDK到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from autocoder_cli_sdk import (
    AutoCoderClient,
    AutoCoderError,
    QueryOptions,
    SDKConfig,
)


def main():
    """主函数，演示基础用法"""

    print("=== AutoCoder CLI SDK 基础用法演示 ===\n")

    # 1. 创建客户端实例
    print("1. 创建客户端...")
    config = SDKConfig(
        verbose=True, default_output_format="text"
    )  # 启用详细输出
    client = AutoCoderClient(config)

    # 2. 获取版本信息
    print("2. 获取版本信息...")
    version = client.get_version()
    print(f"   AutoCoder 版本: {version}\n")

    # 3. 执行简单的代码生成查询
    print("3. 执行代码生成查询...")

    prompt = """
    请创建一个Python函数，用于计算斐波那契数列的第n项。
    要求:
    1. 函数名为 fibonacci
    2. 参数为 n (整数)
    3. 返回第n项的值
    4. 包含适当的错误处理
    5. 添加文档字符串和示例
    """

    try:
        options = QueryOptions(output_format="text")
        lines = []

        for line in client.query(prompt, options):
            lines.append(line)

        if lines:
            print("   ✅ 查询成功！")
            print("   生成的代码:")
            print("   " + "=" * 50)
            for line in lines:
                print("   " + line)
            print("   " + "=" * 50 + "\n")
        else:
            print("   ❌ 查询失败: 无输出内容\n")

    except AutoCoderError as e:
        print(f"   ❌ SDK 错误: {e}\n")
    except Exception as e:
        print(f"   ❌ 未知错误: {e}\n")

    # 4. 使用自定义选项
    print("4. 使用自定义选项...")

    custom_options = QueryOptions(
        max_turns=5,  # 限制最大轮数
        output_format="text",
        verbose=False,  # 关闭详细输出
        permission_mode="acceptEdits",  # 自动接受编辑
    )

    simple_prompt = "创建一个简单的Hello World Python函数"

    try:
        lines = []
        for line in client.query(simple_prompt, custom_options):
            lines.append(line)

        if lines:
            print("   ✅ 自定义选项查询成功！")
            content = "\n".join(lines)
            print(
                "   内容摘要:",
                content[:100] + "..." if len(content) > 100 else content,
            )
        else:
            print("   ❌ 自定义选项查询失败: 无输出内容")

    except Exception as e:
        print(f"   ❌ 错误: {e}")

    print("\n5. 配置管理...")

    # 5. 配置操作示例
    try:
        # 查看当前配置（如果支持的话）
        config_result = client.configure({})
        if not config_result.success:
            print("   配置查看失败，尝试设置新配置...")

        # 设置配置
        config_result = client.configure(
            {"max_turns": "20", "permission_mode": "manual"}
        )

        if config_result.success:
            print("   ✅ 配置设置成功！")
            print(f"   消息: {config_result.message}")
            print(f"   应用的配置: {config_result.applied_configs}")
        else:
            print(f"   ❌ 配置设置失败: {config_result.error}")

    except Exception as e:
        print(f"   ⚠️  配置操作跳过（可能未安装auto-coder.run）: {e}")

    print("\n=== 基础用法演示完成 ===")


if __name__ == "__main__":
    main()
