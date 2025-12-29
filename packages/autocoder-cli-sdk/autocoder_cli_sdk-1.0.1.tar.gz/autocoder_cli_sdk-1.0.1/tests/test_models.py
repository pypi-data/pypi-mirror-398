"""
AutoCoder CLI SDK 模型测试

测试各种数据模型的功能，包括验证、序列化等。
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from autocoder_cli_sdk.models import (
    AutoCoderError,
    ConfigResult,
    QueryOptions,
    QueryResult,
    SDKConfig,
    SessionInfo,
    StreamEvent,
    ValidationError,
)


class TestSDKConfig:
    """测试SDKConfig类"""

    def test_default_config(self):
        """测试默认配置"""
        config = SDKConfig()
        assert config.default_model is None
        assert config.default_max_turns == 10000
        assert config.default_permission_mode == "manual"
        assert config.default_output_format == "text"
        assert config.verbose is False
        assert config.include_rules is False
        assert config.default_allowed_tools is None

    def test_config_with_custom_values(self):
        """测试自定义配置值"""
        config = SDKConfig(
            default_model="gpt-4",
            default_max_turns=20,
            verbose=True,
            default_output_format="json",
        )
        assert config.default_model == "gpt-4"
        assert config.default_max_turns == 20
        assert config.verbose is True
        assert config.default_output_format == "json"

    def test_invalid_output_format(self):
        """测试无效的输出格式"""
        with pytest.raises(ValidationError):
            SDKConfig(default_output_format="invalid_format")

    def test_invalid_permission_mode(self):
        """测试无效的权限模式"""
        with pytest.raises(ValidationError):
            SDKConfig(default_permission_mode="invalid_mode")

    def test_default_cwd_assignment(self):
        """测试默认工作目录分配"""
        config = SDKConfig()
        assert config.default_cwd is not None
        assert Path(config.default_cwd).exists()


class TestQueryOptions:
    """测试QueryOptions类"""

    def test_default_options(self):
        """测试默认选项"""
        options = QueryOptions()
        assert options.model is None
        assert options.max_turns is None
        assert options.system_prompt is None
        assert options.output_format == "text"
        assert options.verbose is False
        assert options.continue_session is False
        assert options.async_mode is False

    def test_custom_options(self):
        """测试自定义选项"""
        options = QueryOptions(
            model="gpt-3.5-turbo",
            max_turns=15,
            verbose=True,
            async_mode=True,
            split_mode="h2",
        )
        assert options.model == "gpt-3.5-turbo"
        assert options.max_turns == 15
        assert options.verbose is True
        assert options.async_mode is True
        assert options.split_mode == "h2"

    def test_merge_with_config(self):
        """测试与全局配置合并"""
        config = SDKConfig(
            default_model="gpt-4", default_max_turns=25, verbose=True
        )

        options = QueryOptions(max_turns=15)  # 只设置部分选项

        merged = options.merge_with_config(config)

        assert merged.model == "gpt-4"  # 从config继承
        assert merged.max_turns == 15  # 从options覆盖
        assert merged.verbose is True  # 从config继承

    def test_merge_with_system_prompt_file(self):
        """测试系统提示文件合并"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt"
        ) as f:
            f.write("这是一个测试系统提示")
            temp_file = f.name

        try:
            config = SDKConfig(system_prompt_path=temp_file)
            options = QueryOptions()

            merged = options.merge_with_config(config)

            assert merged.system_prompt == "这是一个测试系统提示"
        finally:
            os.unlink(temp_file)

    def test_validate_valid_options(self):
        """测试有效选项验证"""
        options = QueryOptions(
            output_format="json",
            permission_mode="acceptEdits",
            async_mode=True,
            split_mode="h1",
        )
        # 不应该抛出异常
        options.validate()

    def test_validate_invalid_output_format(self):
        """测试无效输出格式验证"""
        options = QueryOptions(output_format="invalid")
        with pytest.raises(ValidationError):
            options.validate()

    def test_validate_invalid_permission_mode(self):
        """测试无效权限模式验证"""
        options = QueryOptions(permission_mode="invalid")
        with pytest.raises(ValidationError):
            options.validate()

    def test_validate_invalid_split_mode(self):
        """测试无效分割模式验证"""
        options = QueryOptions(async_mode=True, split_mode="invalid")
        with pytest.raises(ValidationError):
            options.validate()

    def test_validate_invalid_level_range(self):
        """测试无效级别范围验证"""
        options = QueryOptions(
            async_mode=True, split_mode="any", min_level=5, max_level=2
        )
        with pytest.raises(ValidationError):
            options.validate()

    def test_validate_empty_delimiter(self):
        """测试空分隔符验证"""
        options = QueryOptions(
            async_mode=True, split_mode="delimiter", delimiter=""
        )
        with pytest.raises(ValidationError):
            options.validate()


class TestStreamEvent:
    """测试StreamEvent类"""

    def test_create_stream_event(self):
        """测试创建流式事件"""
        event = StreamEvent(
            event_type="content", data={"content": "Hello World"}
        )

        assert event.event_type == "content"
        assert event.data["content"] == "Hello World"
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_is_content_property(self):
        """测试内容事件判断"""
        content_event = StreamEvent("content", {"content": "test"})
        completion_event = StreamEvent("completion", {"result": "done"})
        start_event = StreamEvent("start", {"status": "started"})

        assert content_event.is_content is True
        assert completion_event.is_content is True
        assert start_event.is_content is False

    def test_content_property(self):
        """测试内容提取"""
        content_event = StreamEvent("content", {"content": "Hello"})
        completion_event = StreamEvent("completion", {"result": "Done"})
        tool_event = StreamEvent(
            "tool_call",
            {
                "tool_name": "AttemptCompletionTool",
                "args": {"result": "Completed"},
            },
        )
        start_event = StreamEvent("start", {"status": "started"})

        assert content_event.content == "Hello"
        assert completion_event.content == "Done"
        assert tool_event.content == "Completed"
        assert start_event.content == ""

    def test_to_dict(self):
        """测试转换为字典"""
        event = StreamEvent("test", {"key": "value"})
        event_dict = event.to_dict()

        assert event_dict["event_type"] == "test"
        assert event_dict["data"]["key"] == "value"
        assert "timestamp" in event_dict

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "event_type": "content",
            "data": {"content": "test"},
            "timestamp": "2023-01-01T12:00:00",
        }

        event = StreamEvent.from_dict(data)

        assert event.event_type == "content"
        assert event.data["content"] == "test"
        assert event.timestamp is not None


class TestQueryResult:
    """测试QueryResult类"""

    def test_success_result(self):
        """测试成功结果"""
        result = QueryResult.success_result(
            content="Generated code",
            session_id="test_session",
            execution_time=1.5,
        )

        assert result.success is True
        assert result.content == "Generated code"
        assert result.session_id == "test_session"
        assert result.execution_time == 1.5
        assert result.is_success is True
        assert result.has_error is False

    def test_error_result(self):
        """测试错误结果"""
        result = QueryResult.error_result(
            error="Something went wrong",
            content="partial content",
            session_id="test_session",
        )

        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.content == "partial content"
        assert result.session_id == "test_session"
        assert result.is_success is False
        assert result.has_error is True

    def test_to_dict(self):
        """测试转换为字典"""
        result = QueryResult.success_result("test content")
        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["content"] == "test content"
        assert "events" in result_dict
        assert "metadata" in result_dict


class TestConfigResult:
    """测试ConfigResult类"""

    def test_success_config_result(self):
        """测试成功配置结果"""
        result = ConfigResult.success_result(
            message="Configuration updated",
            applied_configs=["model=gpt-4", "max_turns=20"],
        )

        assert result.success is True
        assert result.message == "Configuration updated"
        assert len(result.applied_configs) == 2
        assert "model=gpt-4" in result.applied_configs

    def test_error_config_result(self):
        """测试错误配置结果"""
        result = ConfigResult.error_result("Configuration failed")

        assert result.success is False
        assert result.error == "Configuration failed"
        assert result.message == ""
        assert len(result.applied_configs) == 0


class TestSessionInfo:
    """测试SessionInfo类"""

    def test_create_session_info(self):
        """测试创建会话信息"""
        session = SessionInfo(
            session_id="test_session_123", name="Test Session"
        )

        assert session.session_id == "test_session_123"
        assert session.name == "Test Session"
        assert session.created_at is not None
        assert session.last_updated is not None
        assert session.message_count == 0
        assert session.status == "active"

    def test_to_dict(self):
        """测试转换为字典"""
        session = SessionInfo(session_id="test", name="Test")
        session_dict = session.to_dict()

        assert session_dict["session_id"] == "test"
        assert session_dict["name"] == "Test"
        assert "created_at" in session_dict
        assert "last_updated" in session_dict
        assert session_dict["message_count"] == 0
        assert session_dict["status"] == "active"


class TestExceptions:
    """测试异常类"""

    def test_autocoder_error(self):
        """测试基础异常"""
        error = AutoCoderError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_validation_error(self):
        """测试验证异常"""
        error = ValidationError("Invalid parameter")
        assert str(error) == "Invalid parameter"
        assert isinstance(error, AutoCoderError)

    def test_execution_error(self):
        """测试执行异常"""
        from autocoder_cli_sdk.models import ExecutionError

        error = ExecutionError(
            "Execution failed", exit_code=1, output="error output"
        )
        assert str(error) == "Execution failed"
        assert error.exit_code == 1
        assert error.output == "error output"
        assert isinstance(error, AutoCoderError)
