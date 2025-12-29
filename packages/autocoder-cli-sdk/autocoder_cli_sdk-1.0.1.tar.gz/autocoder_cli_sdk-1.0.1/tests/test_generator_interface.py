"""
测试Generator接口和新功能

测试SDK的generator接口、pydantic模型支持和abort功能。
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest

from autocoder_cli_sdk.async_client import AsyncAutoCoderClient
from autocoder_cli_sdk.client import AutoCoderClient
from autocoder_cli_sdk.models import QueryOptions, SDKConfig
from autocoder_cli_sdk.pydantic_models import (
    QueryResponseModel,
    StreamEventModel,
)


class TestGeneratorInterface:
    """测试Generator接口"""

    def test_sync_text_generator_return_type(self):
        """测试同步文本格式generator返回类型"""
        client = AutoCoderClient()
        options = QueryOptions(output_format="text")

        # Mock _execute_via_subprocess_generator方法
        def mock_generator(prompt, options):
            yield "line 1"
            yield "line 2"
            yield "line 3"

        with patch.object(
            client,
            "_execute_via_subprocess_generator",
            side_effect=mock_generator,
        ):
            result = client.query("test prompt", options)

            # 验证返回类型是generator
            assert hasattr(result, "__iter__")
            assert hasattr(result, "__next__")

            # 验证内容
            lines = list(result)
            assert len(lines) == 3
            assert lines[0] == "line 1"
            assert lines[1] == "line 2"
            assert lines[2] == "line 3"

    def test_sync_json_generator_return_type(self):
        """测试同步JSON格式generator返回类型"""
        client = AutoCoderClient()
        options = QueryOptions(output_format="json")

        # Mock响应模型
        mock_response = QueryResponseModel(
            events=[
                StreamEventModel(
                    event_type="start", data={"status": "started"}
                ),
                StreamEventModel(
                    event_type="completion", data={"result": "test result"}
                ),
            ]
        )

        def mock_generator(prompt, options):
            yield mock_response

        with patch.object(
            client,
            "_execute_via_subprocess_generator",
            side_effect=mock_generator,
        ):
            result = client.query("test prompt", options)

            # 验证返回类型
            assert hasattr(result, "__iter__")

            # 验证内容
            responses = list(result)
            assert len(responses) == 1
            assert isinstance(responses[0], QueryResponseModel)
            assert responses[0].summary.total_events == 2

    @pytest.mark.asyncio
    async def test_async_text_generator_return_type(self):
        """测试异步文本格式generator返回类型"""
        config = SDKConfig()

        async with AsyncAutoCoderClient(config) as client:
            options = QueryOptions(output_format="text")

            # Mock异步generator
            async def mock_async_generator(prompt, options):
                yield "async line 1"
                yield "async line 2"

            with patch.object(
                client,
                "_execute_via_subprocess_async_generator",
                side_effect=mock_async_generator,
            ):
                result = client.query("test prompt", options)

                # 验证返回类型是async generator
                assert hasattr(result, "__aiter__")
                assert hasattr(result, "__anext__")

                # 验证内容
                lines = []
                async for line in result:
                    lines.append(line)

                assert len(lines) == 2
                assert lines[0] == "async line 1"
                assert lines[1] == "async line 2"

    @pytest.mark.asyncio
    async def test_async_json_generator_return_type(self):
        """测试异步JSON格式generator返回类型"""
        config = SDKConfig()

        async with AsyncAutoCoderClient(config) as client:
            options = QueryOptions(output_format="json")

            # Mock响应模型
            mock_response = QueryResponseModel(
                events=[
                    StreamEventModel(
                        event_type="start", data={"status": "started"}
                    )
                ]
            )

            async def mock_async_generator(prompt, options):
                yield mock_response

            with patch.object(
                client,
                "_execute_via_subprocess_async_generator",
                side_effect=mock_async_generator,
            ):
                result = client.query("test prompt", options)

                # 验证内容
                responses = []
                async for response in result:
                    responses.append(response)

                assert len(responses) == 1
                assert isinstance(responses[0], QueryResponseModel)


class TestAbortFunctionality:
    """测试中止功能"""

    def test_sync_abort(self):
        """测试同步中止功能"""
        client = AutoCoderClient()

        # Mock进程管理器
        with patch(
            "autocoder_cli_sdk.client.get_sync_process_manager"
        ) as mock_get_manager:
            mock_manager = Mock()
            mock_manager.abort.return_value = True
            mock_get_manager.return_value = mock_manager

            # 测试中止
            result = client.abort()
            assert result is True
            mock_manager.abort.assert_called_once_with()

    def test_sync_abort_force(self):
        """测试同步强制中止功能"""
        client = AutoCoderClient()

        with patch(
            "autocoder_cli_sdk.client.get_sync_process_manager"
        ) as mock_get_manager:
            mock_manager = Mock()
            mock_manager.abort.return_value = True
            mock_get_manager.return_value = mock_manager

            # 测试强制中止
            result = client.abort_force()
            assert result is True
            mock_manager.abort.assert_called_once_with(force=True)

    def test_sync_is_running(self):
        """测试同步运行状态检查"""
        client = AutoCoderClient()

        with patch(
            "autocoder_cli_sdk.client.get_sync_process_manager"
        ) as mock_get_manager:
            mock_manager = Mock()
            mock_manager.is_running = True
            mock_get_manager.return_value = mock_manager

            # 测试运行状态
            result = client.is_running()
            assert result is True

    @pytest.mark.asyncio
    async def test_async_abort(self):
        """测试异步中止功能"""
        config = SDKConfig()

        async with AsyncAutoCoderClient(config) as client:
            with patch(
                "autocoder_cli_sdk.async_client.get_async_process_manager"
            ) as mock_get_manager:
                mock_manager = Mock()
                mock_manager.abort.return_value = asyncio.Future()
                mock_manager.abort.return_value.set_result(True)
                mock_get_manager.return_value = mock_manager

                # 测试异步中止
                result = await client.abort()
                assert result is True

    @pytest.mark.asyncio
    async def test_async_is_running(self):
        """测试异步运行状态检查"""
        config = SDKConfig()

        async with AsyncAutoCoderClient(config) as client:
            with patch(
                "autocoder_cli_sdk.async_client.get_async_process_manager"
            ) as mock_get_manager:
                mock_manager = Mock()
                mock_manager.is_running = False
                mock_get_manager.return_value = mock_manager

                # 测试运行状态
                result = client.is_running
                assert result is False


class TestPydanticModels:
    """测试Pydantic模型"""

    def test_query_response_model_creation(self):
        """测试QueryResponseModel创建"""
        events = [
            StreamEventModel(event_type="start", data={"status": "started"}),
            StreamEventModel(event_type="content", data={"content": "Hello"}),
            StreamEventModel(
                event_type="completion", data={"result": "Final result"}
            ),
        ]

        response = QueryResponseModel(events=events)

        assert len(response.events) == 3
        assert response.summary.total_events == 3
        assert response.final_result == "Final result"
        assert response.all_content == "Hello"
        assert response.has_errors is False

    def test_query_response_model_with_errors(self):
        """测试包含错误的QueryResponseModel"""
        events = [
            StreamEventModel(event_type="start", data={"status": "started"}),
            StreamEventModel(
                event_type="error", data={"error": "Something went wrong"}
            ),
        ]

        response = QueryResponseModel(events=events)

        assert response.has_errors is True
        assert len(response.error_messages) == 1
        assert response.error_messages[0] == "Something went wrong"

    def test_stream_event_model_content_extraction(self):
        """测试StreamEventModel内容提取"""
        # 内容事件
        content_event = StreamEventModel(
            event_type="content", data={"content": "Hello World"}
        )
        assert content_event.content == "Hello World"

        # 完成事件
        completion_event = StreamEventModel(
            event_type="completion", data={"result": "Done"}
        )
        assert completion_event.content == "Done"

        # 工具调用事件
        tool_event = StreamEventModel(
            event_type="tool_call",
            data={
                "tool_name": "AttemptCompletionTool",
                "args": {"result": "Completed"},
            },
        )
        assert tool_event.content == "Completed"

        # 其他事件
        start_event = StreamEventModel(
            event_type="start", data={"status": "started"}
        )
        assert start_event.content == ""

    def test_config_response_model(self):
        """测试ConfigResponseModel"""
        from autocoder_cli_sdk.pydantic_models import ConfigResponseModel

        # 成功响应
        success_response = ConfigResponseModel.success_response(
            message="Configuration updated", applied_configs=["model=gpt-4"]
        )

        assert success_response.success is True
        assert success_response.message == "Configuration updated"
        assert len(success_response.applied_configs) == 1

        # 错误响应
        error_response = ConfigResponseModel.error_response(
            "Configuration failed"
        )

        assert error_response.success is False
        assert error_response.error == "Configuration failed"
