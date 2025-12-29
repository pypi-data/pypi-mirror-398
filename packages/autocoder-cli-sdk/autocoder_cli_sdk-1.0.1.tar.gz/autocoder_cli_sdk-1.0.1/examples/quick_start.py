"""
AutoCoder CLI SDK 快速开始示例

展示最简单和最常用的用法。
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autocoder_cli_sdk import (
    AsyncAutoCoderClient,
    AutoCoderClient,
    AutoCoderError,
    QueryOptions,
)


def sync_examples():
    """同步用法示例"""
    print("=== 同步用法 ===")

    client = AutoCoderClient()

    # 1. 最简单的用法
    print("1. 快速查询（便利方法）")
    try:
        result = client.quick_query("创建一个简单的hello函数", verbose=False)
        print(f"   ✅ 生成了 {len(result)} 字符的代码")
    except Exception as e:
        print(f"   ❌ 失败: {e}")

    # 2. Generator用法（文本格式）
    print("\n2. Generator接口（文本格式）")
    try:
        line_count = 0
        for line in client.query(
            "创建一个计算器函数", QueryOptions(output_format="text")
        ):
            line_count += 1
            if line_count <= 3:  # 只显示前3行
                print(f"   第{line_count}行: {line}")
            elif line_count == 4:
                print("   ...")
            if line_count > 10:  # 限制输出
                break
        print(f"   ✅ 共生成 {line_count} 行")
    except Exception as e:
        print(f"   ❌ 失败: {e}")

    # 3. JSON格式（便利方法）
    print("\n3. JSON格式查询")
    try:
        result = client.json_query("创建一个简单函数")
        print(f"   ✅ 事件数: {result.summary.total_events}")
        if result.has_errors:
            print(f"   ⚠️  有错误: {result.error_messages[0]}")
        else:
            final_result = result.final_result
            if final_result:
                print(f"   ✅ 结果长度: {len(final_result)} 字符")
    except Exception as e:
        print(f"   ❌ 失败: {e}")


async def async_examples():
    """异步用法示例"""
    print("\n=== 异步用法 ===")

    async with AsyncAutoCoderClient() as client:
        # 1. 异步便利方法
        print("1. 异步快速查询")
        try:
            result = await client.quick_query("创建一个排序函数")
            print(f"   ✅ 异步生成了 {len(result)} 字符的代码")
        except Exception as e:
            print(f"   ❌ 失败: {e}")

        # 2. 异步JSON查询
        print("\n2. 异步JSON查询")
        try:
            result = await client.json_query("创建一个简单类")
            print(f"   ✅ 异步事件数: {result.summary.total_events}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")

        # 3. 批量查询
        print("\n3. 批量查询")
        try:
            prompts = ["创建函数A", "创建函数B"]
            results = await client.batch_query(prompts, max_concurrency=2)
            print(f"   ✅ 批量查询完成，结果数: {len(results)}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")


def session_example():
    """会话示例"""
    print("\n=== 会话管理 ===")

    client = AutoCoderClient()

    try:
        with client.session() as session:
            # 第一轮
            result1 = session.quick_query("创建一个User类")
            print(f"   ✅ 第一轮: {len(result1)} 字符")

            # 第二轮（基于上下文）
            result2 = session.quick_query("为User类添加验证方法")
            print(f"   ✅ 第二轮: {len(result2)} 字符")

    except Exception as e:
        print(f"   ❌ 会话失败: {e}")


def main():
    """主函数"""
    print("🚀 AutoCoder CLI SDK 快速开始示例\n")

    # 检查基础功能
    try:
        client = AutoCoderClient()
        print(f"✅ SDK 初始化成功")
        print(f"✅ 版本: {client.get_version()}")
        print(f"✅ 运行状态: {client.is_running()}")
    except AutoCoderError as e:
        print(f"❌ SDK 初始化失败: {e}")
        print("💡 提示: 请确保已安装 auto-coder 或在正确的环境中运行")
        return

    # 运行示例
    sync_examples()
    asyncio.run(async_examples())
    session_example()

    print("\n🎉 快速开始示例完成！")


if __name__ == "__main__":
    main()
