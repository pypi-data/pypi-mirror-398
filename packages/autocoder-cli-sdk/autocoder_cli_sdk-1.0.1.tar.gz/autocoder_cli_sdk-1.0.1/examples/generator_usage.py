"""
AutoCoder CLI SDK Generator用法示例

演示如何使用SDK的新generator接口和pydantic模型，支持abort操作。
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加SDK到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from autocoder_cli_sdk import (
    AsyncAutoCoderClient,
    AutoCoderClient,
    AutoCoderError,
    QueryOptions,
    QueryResponseModel,
    SDKConfig,
    StreamEventModel,
)


def sync_text_generator_example():
    """同步文本格式generator示例"""
    print("=== 同步文本格式Generator示例 ===")

    config = SDKConfig(verbose=False)
    client = AutoCoderClient(config)

    prompt = "创建一个Python函数来计算两个数的最大公约数"
    options = QueryOptions(output_format="text")

    try:
        print("开始生成代码...")

        # 使用generator接口逐行接收输出
        line_count = 0
        for line in client.query(prompt, options):
            print(f"[第{line_count+1}行] {line}")
            line_count += 1

            # 可以在这里检查是否需要中止
            if line_count > 50:  # 防止输出过多
                print("输出行数超过限制，中止操作...")
                client.abort()
                break

        print(f"\n✅ 完成！共接收{line_count}行输出")

    except AutoCoderError as e:
        print(f"❌ SDK 错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

    print()


def sync_json_generator_example():
    """同步JSON格式generator示例"""
    print("=== 同步JSON格式Generator示例 ===")

    config = SDKConfig(verbose=False)
    client = AutoCoderClient(config)

    prompt = "创建一个简单的Python类来表示学生信息"
    options = QueryOptions(output_format="json")

    try:
        print("开始JSON格式查询...")

        # JSON格式返回pydantic模型
        for response_model in client.query(prompt, options):
            if isinstance(response_model, QueryResponseModel):
                print(f"✅ 接收到QueryResponseModel")
                print(f"   事件总数: {response_model.summary.total_events}")
                print(
                    f"   完成事件数: {response_model.summary.completion_events}"
                )
                print(f"   错误事件数: {response_model.summary.error_events}")
                print(f"   是否有错误: {response_model.has_errors}")

                if response_model.has_errors:
                    print("   错误消息:")
                    for error_msg in response_model.error_messages:
                        print(f"     - {error_msg}")
                else:
                    # 获取最终结果
                    final_result = response_model.final_result
                    if final_result:
                        print("   最终结果预览:")
                        preview = (
                            final_result[:200] + "..."
                            if len(final_result) > 200
                            else final_result
                        )
                        print(f"     {preview}")

                    # 显示事件详情
                    print(f"   事件详情:")
                    for i, event in enumerate(
                        response_model.events[:5]
                    ):  # 只显示前5个
                        print(
                            f"     {i+1}. [{event.event_type}] {str(event.data.dict())[:50]}..."
                        )

                break  # JSON格式通常只返回一个模型

    except AutoCoderError as e:
        print(f"❌ SDK 错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

    print()


async def async_text_generator_example():
    """异步文本格式generator示例"""
    print("=== 异步文本格式Generator示例 ===")

    config = SDKConfig(verbose=False)

    async with AsyncAutoCoderClient(config) as client:
        prompt = "创建一个Python装饰器来测量函数执行时间"
        options = QueryOptions(output_format="text")

        try:
            print("开始异步生成...")

            line_count = 0
            start_time = time.time()

            async for line in client.query(prompt, options):
                print(f"[异步{line_count+1}] {line}")
                line_count += 1

                # 检查是否需要中止（比如超过时间限制）
                if time.time() - start_time > 30:  # 30秒超时
                    print("执行时间超过限制，中止操作...")
                    await client.abort()
                    break

                # 模拟实时处理
                await asyncio.sleep(0.1)

            execution_time = time.time() - start_time
            print(
                f"\n✅ 异步完成！共接收{line_count}行输出，用时{execution_time:.2f}秒"
            )

        except AutoCoderError as e:
            print(f"❌ SDK 错误: {e}")
        except Exception as e:
            print(f"❌ 未知错误: {e}")

    print()


async def async_json_generator_example():
    """异步JSON格式generator示例"""
    print("=== 异步JSON格式Generator示例 ===")

    config = SDKConfig(verbose=False)

    async with AsyncAutoCoderClient(config) as client:
        prompt = "创建一个Python上下文管理器来处理数据库连接"
        options = QueryOptions(output_format="json")

        try:
            print("开始异步JSON查询...")

            async for response_model in client.query(prompt, options):
                if isinstance(response_model, QueryResponseModel):
                    print(f"✅ 异步接收到QueryResponseModel")
                    print(f"   会话ID: {response_model.session_id}")

                    # 统计不同类型的事件
                    event_types = {}
                    for event in response_model.events:
                        event_types[event.event_type] = (
                            event_types.get(event.event_type, 0) + 1
                        )

                    print("   事件类型统计:")
                    for event_type, count in event_types.items():
                        print(f"     {event_type}: {count}")

                    # 如果有完成事件，显示结果
                    final_result = response_model.final_result
                    if final_result:
                        print("   生成代码长度:", len(final_result))
                        print("   代码片段预览:")
                        lines = final_result.split("\n")[:5]  # 前5行
                        for i, line in enumerate(lines):
                            print(f"     {i+1}: {line}")
                        if len(final_result.split("\n")) > 5:
                            print("     ...")

                    break

        except AutoCoderError as e:
            print(f"❌ SDK 错误: {e}")
        except Exception as e:
            print(f"❌ 未知错误: {e}")

    print()


async def abort_functionality_example():
    """中止功能示例"""
    print("=== 中止功能示例 ===")

    config = SDKConfig(verbose=False)

    async with AsyncAutoCoderClient(config) as client:
        prompt = """
        创建一个完整的Django Web应用项目，包括：
        1. 用户认证系统
        2. 博客文章管理
        3. 评论系统
        4. API接口
        5. 前端界面
        6. 数据库模型
        7. 单元测试
        8. 部署配置
        """

        options = QueryOptions(output_format="text")

        try:
            print("开始长时间查询（将在5秒后自动中止）...")

            start_time = time.time()
            line_count = 0

            # 启动查询任务
            query_task = asyncio.create_task(
                client.query(prompt, options).__anext__()
            )

            while True:
                try:
                    # 等待下一行输出，但设置超时
                    line = await asyncio.wait_for(query_task, timeout=1.0)
                    print(f"[{line_count+1}] {line}")
                    line_count += 1

                    # 5秒后中止
                    if time.time() - start_time > 5:
                        print("\n⏰ 5秒时间到，执行中止操作...")

                        # 检查是否正在运行
                        if client.is_running:
                            print("   检测到进程正在运行，开始中止...")
                            success = await client.abort()
                            if success:
                                print("   ✅ 成功中止进程")
                            else:
                                print("   ⚠️  中止失败，尝试强制中止...")
                                success = await client.abort_force()
                                if success:
                                    print("   ✅ 强制中止成功")
                                else:
                                    print("   ❌ 强制中止也失败")
                        else:
                            print("   ℹ️  进程已经不在运行中")
                        break

                    # 为下一行准备任务
                    query_task = asyncio.create_task(
                        client.query(prompt, options).__anext__()
                    )

                except asyncio.TimeoutError:
                    # 1秒内没有新输出，继续等待
                    continue
                except StopAsyncIteration:
                    # 查询自然结束
                    print("   查询自然结束")
                    break
                except Exception as e:
                    print(f"   查询过程中发生异常: {e}")
                    break

            execution_time = time.time() - start_time
            print(
                f"\n📊 统计：共接收{line_count}行输出，总用时{execution_time:.2f}秒"
            )

        except Exception as e:
            print(f"❌ 中止功能测试失败: {e}")

    print()


async def batch_query_example():
    """批量查询示例"""
    print("=== 批量查询示例 ===")

    config = SDKConfig(verbose=False)

    async with AsyncAutoCoderClient(config) as client:
        prompts = [
            "创建一个Python函数来验证邮箱地址",
            "创建一个Python函数来生成随机密码",
            "创建一个Python函数来计算文件哈希值",
        ]

        options = QueryOptions(output_format="text")

        try:
            print("开始批量查询（最大并发数: 2）...")
            start_time = time.time()

            results = await client.batch_query(
                prompts, options, max_concurrency=2
            )

            execution_time = time.time() - start_time
            print(f"✅ 批量查询完成！总用时: {execution_time:.2f}秒")

            for i, result in enumerate(results):
                print(f"\n查询 {i+1} 结果:")
                if isinstance(result, list):  # text格式的结果
                    if len(result) > 0:
                        print(f"  成功！生成了{len(result)}行代码")
                        print(f"  预览: {result[0] if result else '无内容'}")
                    else:
                        print("  无输出")
                elif isinstance(result, QueryResponseModel):  # json格式的结果
                    print(f"  JSON响应，事件数: {result.summary.total_events}")
                else:
                    print(f"  未知结果类型: {type(result)}")

        except Exception as e:
            print(f"❌ 批量查询失败: {e}")

    print()


async def main():
    """主函数，运行所有示例"""
    print("=== AutoCoder CLI SDK Generator用法演示 ===\n")

    # 同步示例
    sync_text_generator_example()
    sync_json_generator_example()

    # 异步示例
    await async_text_generator_example()
    await async_json_generator_example()

    # 高级功能
    await abort_functionality_example()
    await batch_query_example()

    print("=== Generator用法演示完成 ===")


if __name__ == "__main__":
    # 运行异步主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断程序执行")
