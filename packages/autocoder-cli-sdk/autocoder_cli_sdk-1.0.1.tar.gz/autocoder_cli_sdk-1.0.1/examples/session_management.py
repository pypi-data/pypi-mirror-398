"""
AutoCoder CLI SDK 会话管理示例

演示如何使用SDK进行会话管理，包括多轮对话、会话恢复等功能。
"""

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


def basic_session_example():
    """基础会话管理示例"""
    print("=== 基础会话管理示例 ===")

    config = SDKConfig(verbose=False)
    client = AutoCoderClient(config)

    try:
        # 使用会话上下文管理器
        with client.session() as session:
            print("开始新会话...")

            # 第一轮：创建基础类
            print("\n第一轮：创建基础类")
            result1 = session.query(
                """
            创建一个Python的博客文章类（BlogPost），包含以下属性：
            - title (标题)
            - content (内容) 
            - author (作者)
            - created_at (创建时间)
            - tags (标签列表)
            
            请包含基本的初始化方法和__str__方法。
            """
            )

            if result1.is_success:
                print("✅ 第一轮成功")
                print("生成的代码长度:", len(result1.content), "字符")
                print("代码预览:")
                print(
                    result1.content[:200] + "..."
                    if len(result1.content) > 200
                    else result1.content
                )
            else:
                print("❌ 第一轮失败:", result1.error)
                return

            # 第二轮：添加方法
            print("\n第二轮：添加方法")
            result2 = session.query(
                """
            为刚才创建的BlogPost类添加以下方法：
            1. add_tag(tag) - 添加标签
            2. remove_tag(tag) - 删除标签
            3. get_summary(length=100) - 获取内容摘要
            4. to_dict() - 转换为字典
            5. from_dict(data) - 从字典创建实例（类方法）
            """
            )

            if result2.is_success:
                print("✅ 第二轮成功")
                print("生成的代码长度:", len(result2.content), "字符")
            else:
                print("❌ 第二轮失败:", result2.error)
                return

            # 第三轮：添加验证和单元测试
            print("\n第三轮：添加验证和测试")
            result3 = session.query(
                """
            为BlogPost类添加：
            1. 输入验证（标题不能为空，内容长度限制等）
            2. 完整的单元测试，测试所有方法
            3. 使用示例代码
            """
            )

            if result3.is_success:
                print("✅ 第三轮成功")
                print("生成的代码长度:", len(result3.content), "字符")
                print("\n最终完整代码:")
                print("=" * 60)
                print(result3.content)
                print("=" * 60)
            else:
                print("❌ 第三轮失败:", result3.error)

    except Exception as e:
        print(f"❌ 会话示例失败: {e}")

    print()


def session_with_options_example():
    """带选项的会话示例"""
    print("=== 带选项的会话示例 ===")

    config = SDKConfig(default_max_turns=15, verbose=False)
    client = AutoCoderClient(config)

    # 自定义选项
    options = QueryOptions(
        system_prompt="你是一个资深的Python Web开发工程师，请提供生产级别的代码。",
        max_turns=20,
        permission_mode="acceptEdits",
    )

    try:
        with client.session() as session:
            print("开始带自定义选项的会话...")

            # 第一步：创建Flask API
            result1 = session.query(
                """
            使用Flask创建一个RESTful API，用于管理用户信息：
            - GET /users - 获取所有用户
            - GET /users/<id> - 获取特定用户
            - POST /users - 创建用户  
            - PUT /users/<id> - 更新用户
            - DELETE /users/<id> - 删除用户
            
            要求包含：
            1. 输入验证
            2. 错误处理
            3. 适当的HTTP状态码
            4. JSON响应格式
            """,
                options,
            )

            if result1.is_success:
                print("✅ Flask API 创建成功")
                print("代码长度:", len(result1.content), "字符")
            else:
                print("❌ Flask API 创建失败:", result1.error)
                return

            # 第二步：添加数据模型和数据库支持
            result2 = session.query(
                """
            为刚才的Flask API添加：
            1. SQLAlchemy数据模型（User model）
            2. 数据库配置和连接
            3. 数据库迁移支持
            4. 将API端点连接到数据库操作
            """,
                options,
            )

            if result2.is_success:
                print("✅ 数据库支持添加成功")
                print("代码长度:", len(result2.content), "字符")
            else:
                print("❌ 数据库支持添加失败:", result2.error)
                return

            # 第三步：添加认证和测试
            result3 = session.query(
                """
            为Flask API添加：
            1. JWT认证中间件
            2. 用户登录/注册端点
            3. 权限控制（只有认证用户才能修改数据）
            4. 完整的单元测试和集成测试
            5. API文档（swagger/openapi）
            """,
                options,
            )

            if result3.is_success:
                print("✅ 认证和测试添加成功")
                print("最终代码长度:", len(result3.content), "字符")

                # 保存到文件（演示用）
                output_file = Path(__file__).parent / "generated_flask_api.py"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"# Generated Flask API with Authentication\n")
                    f.write(f"# Generated by AutoCoder CLI SDK\n\n")
                    f.write(result3.content)

                print(f"完整代码已保存到: {output_file}")
            else:
                print("❌ 认证和测试添加失败:", result3.error)

    except Exception as e:
        print(f"❌ 带选项会话示例失败: {e}")

    print()


def session_resume_example():
    """会话恢复示例（模拟）"""
    print("=== 会话恢复示例 ===")

    client = AutoCoderClient()

    # 注意：实际的会话ID需要从真实的AutoCoder会话中获取
    # 这里只是演示API的使用方式
    fake_session_id = "session_123456"

    try:
        print("尝试恢复会话（演示用）...")

        # 创建恢复选项
        resume_options = QueryOptions(session_id=fake_session_id, verbose=True)

        # 尝试在恢复的会话中继续对话
        result = client.query(
            "请总结一下我们之前讨论的内容，并提供下一步的建议。",
            resume_options,
        )

        if result.is_success:
            print("✅ 会话恢复成功")
            print("回复内容:", result.content)
        else:
            print("⚠️  会话恢复失败（这是预期的，因为会话ID是模拟的）")
            print("错误信息:", result.error)

    except Exception as e:
        print(f"⚠️  会话恢复示例跳过: {e}")

    print()


def continue_session_example():
    """继续最近会话示例"""
    print("=== 继续最近会话示例 ===")

    client = AutoCoderClient()

    try:
        print("尝试继续最近的会话...")

        # 使用continue_session选项
        continue_options = QueryOptions(continue_session=True, verbose=False)

        result = client.query(
            "请帮我优化刚才生成的代码，主要关注性能和可读性。",
            continue_options,
        )

        if result.is_success:
            print("✅ 继续会话成功")
            print("回复长度:", len(result.content), "字符")
            print(
                "回复预览:",
                (
                    result.content[:150] + "..."
                    if len(result.content) > 150
                    else result.content
                ),
            )
        else:
            print("⚠️  继续会话失败（可能没有最近的会话）")
            print("错误信息:", result.error)

    except Exception as e:
        print(f"⚠️  继续会话示例跳过: {e}")

    print()


def multi_session_example():
    """多会话并行示例"""
    print("=== 多会话并行示例 ===")

    client = AutoCoderClient()

    try:
        print("创建多个独立的会话...")

        # 会话1：前端开发
        print("\n会话1：前端开发")
        with client.session() as frontend_session:
            result = frontend_session.query(
                """
            创建一个React组件，用于显示用户个人资料卡片。
            包含头像、姓名、邮箱、工作职位等信息。
            使用现代化的CSS样式。
            """
            )

            if result.is_success:
                print("✅ 前端组件创建成功")
                print("代码长度:", len(result.content), "字符")
            else:
                print("❌ 前端组件创建失败:", result.error)

        # 会话2：后端开发（独立的会话上下文）
        print("\n会话2：后端开发")
        with client.session() as backend_session:
            result = backend_session.query(
                """
            创建一个FastAPI应用，提供用户认证API：
            - 用户注册
            - 用户登录
            - 获取用户信息
            - 更新用户信息
            
            使用JWT认证和Pydantic模型。
            """
            )

            if result.is_success:
                print("✅ 后端API创建成功")
                print("代码长度:", len(result.content), "字符")
            else:
                print("❌ 后端API创建失败:", result.error)

        # 会话3：数据库设计
        print("\n会话3：数据库设计")
        with client.session() as db_session:
            result = db_session.query(
                """
            设计一个用户管理系统的数据库模式：
            1. 用户表（users）
            2. 角色表（roles）
            3. 权限表（permissions）
            4. 用户角色关联表（user_roles）
            5. 角色权限关联表（role_permissions）
            
            提供SQL DDL语句和索引优化建议。
            """
            )

            if result.is_success:
                print("✅ 数据库设计完成")
                print("代码长度:", len(result.content), "字符")
            else:
                print("❌ 数据库设计失败:", result.error)

        print("\n所有并行会话完成！每个会话都有独立的上下文。")

    except Exception as e:
        print(f"❌ 多会话示例失败: {e}")

    print()


def main():
    """主函数"""
    print("=== AutoCoder CLI SDK 会话管理演示 ===\n")

    # 运行各种会话管理示例
    basic_session_example()
    session_with_options_example()
    session_resume_example()
    continue_session_example()
    multi_session_example()

    print("=== 会话管理演示完成 ===")


if __name__ == "__main__":
    main()
