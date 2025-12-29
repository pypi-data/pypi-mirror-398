"""
AutoCoder CLI SDK 异步用法示例

演示如何使用SDK进行异步代码生成、流式处理和并发查询。
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加SDK到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from autocoder_cli_sdk import (
    AsyncAutoCoderClient,
    AutoCoderError,
    QueryOptions,
    SDKConfig,
)


async def basic_async_example():
    """基础异步查询示例"""
    print("=== 基础异步查询示例 ===")

    config = SDKConfig(verbose=False)

    async with AsyncAutoCoderClient(config) as client:
        prompt = "创建一个Python函数来验证邮箱地址格式"

        try:
            result = await client.query(prompt)

            if result.is_success:
                print("✅ 异步查询成功！")
                print(f"执行时间: {result.execution_time:.2f}秒")
                print("生成的代码片段:")
                print(
                    result.content[:200] + "..."
                    if len(result.content) > 200
                    else result.content
                )
            else:
                print(f"❌ 异步查询失败: {result.error}")

        except AutoCoderError as e:
            print(f"❌ SDK 错误: {e}")

    print()


async def stream_example():
    """流式处理示例"""
    print("=== 流式处理示例 ===")

    config = SDKConfig()

    async with AsyncAutoCoderClient(config) as client:
        prompt = "创建一个简单的计算器类，包含加减乘除四个方法"

        try:
            print("开始流式查询...")

            content_parts = []

            async for event in client.stream_query(prompt):
                print(f"[{event.event_type}] ", end="")

                if event.event_type == "start":
                    print("查询开始")
                elif event.event_type == "content":
                    content = event.content
                    if content:
                        print(f"接收到内容: {len(content)} 字符")
                        content_parts.append(content)
                elif event.event_type == "end":
                    print("查询完成")
                elif event.event_type == "error":
                    print(
                        f"发生错误: {event.data.get('error', 'Unknown error')}"
                    )
                else:
                    print(f"其他事件: {event.data}")

            if content_parts:
                full_content = "".join(content_parts)
                print(f"\n完整内容 ({len(full_content)} 字符):")
                print(
                    full_content[:300] + "..."
                    if len(full_content) > 300
                    else full_content
                )

        except Exception as e:
            print(f"❌ 流式处理失败: {e}")

    print()


async def concurrent_queries_example():
    """并发查询示例"""
    print("=== 并发查询示例 ===")

    config = SDKConfig(verbose=False)

    async with AsyncAutoCoderClient(config) as client:
        prompts = [
            "创建一个Python函数来生成随机密码",
            "创建一个Python函数来验证密码强度",
            "创建一个Python函数来哈希密码",
        ]

        try:
            print(f"开始并发执行 {len(prompts)} 个查询...")
            start_time = time.time()

            # 并发执行查询，限制最大并发数为2
            results = await client.batch_query(prompts, max_concurrency=2)

            end_time = time.time()
            total_time = end_time - start_time

            print(f"并发查询完成，总用时: {total_time:.2f}秒")

            for i, result in enumerate(results):
                print(f"\n查询 {i+1}:")
                if result.is_success:
                    print(f"  ✅ 成功 (用时: {result.execution_time:.2f}秒)")
                    print(f"  内容长度: {len(result.content)} 字符")
                    print(f"  内容预览: {result.content[:100]}...")
                else:
                    print(f"  ❌ 失败: {result.error}")

        except Exception as e:
            print(f"❌ 并发查询失败: {e}")

    print()


async def session_example():
    """会话管理示例"""
    print("=== 会话管理示例 ===")

    config = SDKConfig(verbose=False)

    async with AsyncAutoCoderClient(config) as client:
        try:
            # 使用会话上下文管理器进行多轮对话
            async with client.session() as session:
                print("开始会话...")

                # 第一轮对话
                result1 = await session.query(
                    "创建一个User类，包含name和email属性"
                )
                if result1.is_success:
                    print("✅ 第一轮对话成功")
                    print(f"   内容长度: {len(result1.content)} 字符")
                else:
                    print(f"❌ 第一轮对话失败: {result1.error}")
                    return

                # 第二轮对话（基于上一轮的上下文）
                result2 = await session.query(
                    "为这个User类添加一个验证邮箱格式的方法"
                )
                if result2.is_success:
                    print("✅ 第二轮对话成功")
                    print(f"   内容长度: {len(result2.content)} 字符")
                else:
                    print(f"❌ 第二轮对话失败: {result2.error}")
                    return

                # 第三轮对话
                result3 = await session.query("为User类添加单元测试")
                if result3.is_success:
                    print("✅ 第三轮对话成功")
                    print(f"   内容长度: {len(result3.content)} 字符")

                    # 显示最终结果的一部分
                    print("\n最终代码预览:")
                    print(
                        result3.content[:400] + "..."
                        if len(result3.content) > 400
                        else result3.content
                    )
                else:
                    print(f"❌ 第三轮对话失败: {result3.error}")

        except Exception as e:
            print(f"❌ 会话示例失败: {e}")

    print()


async def advanced_options_example():
    """高级选项示例"""
    print("=== 高级选项示例 ===")

    config = SDKConfig(
        default_max_turns=10,
        default_permission_mode="acceptEdits",
        verbose=True,
    )

    async with AsyncAutoCoderClient(config) as client:
        # 使用高级选项
        options = QueryOptions(
            max_turns=15,
            system_prompt="你是一个专业的Python开发专家，请提供高质量、可维护的代码。",
            permission_mode="manual",
            include_rules=False,
            output_format="text",
        )

        prompt = """
        请创建一个完整的Python类来管理任务队列，要求：
        1. 支持添加、删除、获取任务
        2. 支持任务优先级
        3. 线程安全
        4. 包含完整的文档和类型提示
        5. 包含使用示例
        """

        try:
            result = await client.query(prompt, options)

            if result.is_success:
                print("✅ 高级选项查询成功！")
                print(f"执行时间: {result.execution_time:.2f}秒")
                print("\n生成的代码:")
                print(result.content)
            else:
                print(f"❌ 高级选项查询失败: {result.error}")

        except Exception as e:
            print(f"❌ 高级选项示例失败: {e}")

    print()


async def configuration_example():
    """配置管理示例"""
    print("=== 配置管理示例 ===")

    async with AsyncAutoCoderClient() as client:
        try:
            # 获取版本信息
            version = await client.get_version()
            print(f"AutoCoder版本: {version}")

            # 设置配置
            config_dict = {
                "max_turns": "25",
                "permission_mode": "acceptEdits",
            }

            result = await client.configure(config_dict)

            if result.success:
                print("✅ 配置更新成功!")
                print(f"消息: {result.message}")
                if result.applied_configs:
                    print(f"应用的配置: {result.applied_configs}")
            else:
                print(f"❌ 配置更新失败: {result.error}")

        except Exception as e:
            print(f"⚠️  配置示例跳过（可能未安装auto-coder.run）: {e}")

    print()


async def main():
    """主函数，运行所有示例"""
    print("=== AutoCoder CLI SDK 异步用法演示 ===\n")

    # 按顺序运行各个示例
    await basic_async_example()
    await stream_example()
    await concurrent_queries_example()
    await session_example()
    await advanced_options_example()
    await configuration_example()

    print("=== 异步用法演示完成 ===")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
