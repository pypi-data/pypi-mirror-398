"""
AutoCoder CLI SDK 客户端测试

测试同步客户端的各种功能。
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from autocoder_cli_sdk.client import AutoCoderClient
from autocoder_cli_sdk.models import (
    AutoCoderError,
    ConfigResult,
    QueryOptions,
    QueryResult,
    SDKConfig,
    ValidationError,
)


class TestAutoCoderClient:
    """测试AutoCoderClient类"""

    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        client = AutoCoderClient()
        assert client.config is not None
        assert isinstance(client.config, SDKConfig)

    def test_init_with_custom_config(self):
        """测试使用自定义配置初始化"""
        config = SDKConfig(verbose=True, default_model="gpt-4")
        client = AutoCoderClient(config)
        assert client.config is config
        assert client.config.verbose is True
        assert client.config.default_model == "gpt-4"

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", False)
    @patch("autocoder_cli_sdk.client.AutoCoderClient._can_use_subprocess")
    def test_init_without_sdk_or_subprocess(self, mock_subprocess_check):
        """测试既无SDK也无subprocess时的初始化"""
        mock_subprocess_check.return_value = False

        with pytest.raises(AutoCoderError) as excinfo:
            AutoCoderClient()

        assert "无法使用AutoCoder SDK" in str(excinfo.value)

    @patch("subprocess.run")
    def test_can_use_subprocess_success(self, mock_run):
        """测试subprocess检查成功"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        client = AutoCoderClient()
        assert client._can_use_subprocess() is True

    @patch("subprocess.run")
    def test_can_use_subprocess_failure(self, mock_run):
        """测试subprocess检查失败"""
        mock_run.side_effect = FileNotFoundError()

        client = AutoCoderClient()
        assert client._can_use_subprocess() is False

    def test_query_with_validation_error(self):
        """测试查询参数验证错误"""
        client = AutoCoderClient()
        invalid_options = QueryOptions(output_format="invalid_format")

        result = client.query("test prompt", invalid_options)

        assert result.success is False
        assert result.has_error is True
        assert "不支持的输出格式" in result.error

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", True)
    def test_query_via_sdk_success(self):
        """测试通过SDK成功查询"""
        # Mock CLI结果
        mock_cli_result = Mock()
        mock_cli_result.success = True
        mock_cli_result.output = "Generated code"
        mock_cli_result.error = None
        mock_cli_result.debug_info = {"test": "info"}

        # Mock CLI实例
        mock_cli = Mock()
        mock_cli.run.return_value = mock_cli_result

        with patch(
            "autocoder_cli_sdk.client.AutoCoderCLI", return_value=mock_cli
        ):
            client = AutoCoderClient()
            result = client.query("Create a function")

            assert result.success is True
            assert result.content == "Generated code"
            assert result.execution_time is not None

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", True)
    def test_query_via_sdk_failure(self):
        """测试通过SDK查询失败"""
        # Mock CLI结果
        mock_cli_result = Mock()
        mock_cli_result.success = False
        mock_cli_result.output = ""
        mock_cli_result.error = "Query failed"
        mock_cli_result.debug_info = {}

        # Mock CLI实例
        mock_cli = Mock()
        mock_cli.run.return_value = mock_cli_result

        with patch(
            "autocoder_cli_sdk.client.AutoCoderCLI", return_value=mock_cli
        ):
            client = AutoCoderClient()
            result = client.query("Create a function")

            assert result.success is False
            assert result.error == "Query failed"

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", False)
    @patch("subprocess.run")
    def test_query_via_subprocess_success(self, mock_run):
        """测试通过subprocess成功查询"""
        # Mock subprocess结果
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated code via subprocess"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Mock subprocess检查
        with patch.object(
            AutoCoderClient, "_can_use_subprocess", return_value=True
        ):
            client = AutoCoderClient()
            result = client.query("Create a function")

            assert result.success is True
            assert result.content == "Generated code via subprocess"
            assert result.metadata.get("subprocess") is True

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", False)
    @patch("subprocess.run")
    def test_query_via_subprocess_failure(self, mock_run):
        """测试通过subprocess查询失败"""
        # Mock subprocess结果
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_run.return_value = mock_result

        # Mock subprocess检查
        with patch.object(
            AutoCoderClient, "_can_use_subprocess", return_value=True
        ):
            client = AutoCoderClient()
            result = client.query("Create a function")

            assert result.success is False
            assert result.error == "Command failed"
            assert result.metadata.get("exit_code") == 1

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", False)
    @patch("subprocess.run")
    def test_query_via_subprocess_with_large_prompt(self, mock_run):
        """测试通过subprocess处理大型提示"""
        # Mock subprocess结果
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated code"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Mock subprocess检查
        with patch.object(
            AutoCoderClient, "_can_use_subprocess", return_value=True
        ):
            client = AutoCoderClient()

            # 创建一个大型提示（>1000字符）
            large_prompt = "Create a function. " * 100  # > 1000字符
            result = client.query(large_prompt)

            assert result.success is True
            assert result.content == "Generated code"

    def test_stream_query(self):
        """测试流式查询"""
        client = AutoCoderClient()

        # Mock query方法
        mock_result = QueryResult.success_result("Generated code")
        with patch.object(client, "query", return_value=mock_result):
            events = list(client.stream_query("Create a function"))

            # 应该有开始、内容和结束事件
            assert len(events) >= 3
            assert events[0].event_type == "start"
            assert any(event.event_type == "content" for event in events)
            assert events[-1].event_type == "end"

    def test_stream_query_with_error(self):
        """测试流式查询错误处理"""
        client = AutoCoderClient()

        # Mock query方法抛出异常
        with patch.object(
            client, "query", side_effect=Exception("Test error")
        ):
            events = list(client.stream_query("Create a function"))

            # 应该有错误事件
            assert len(events) == 1
            assert events[0].event_type == "error"
            assert "Test error" in events[0].data["error"]

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", True)
    def test_configure_via_sdk_success(self):
        """测试通过SDK配置成功"""
        # Mock CLI结果
        mock_cli_result = Mock()
        mock_cli_result.success = True
        mock_cli_result.output = "Configuration updated"
        mock_cli_result.error = None

        # Mock CLI实例
        mock_cli = Mock()
        mock_cli.run.return_value = mock_cli_result

        with patch(
            "autocoder_cli_sdk.client.AutoCoderCLI", return_value=mock_cli
        ):
            client = AutoCoderClient()
            result = client.configure({"model": "gpt-4", "max_turns": "20"})

            assert result.success is True
            assert result.message == "Configuration updated"
            assert "model=gpt-4" in result.applied_configs
            assert "max_turns=20" in result.applied_configs

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", False)
    @patch("subprocess.run")
    def test_configure_via_subprocess_success(self, mock_run):
        """测试通过subprocess配置成功"""
        # Mock subprocess结果
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Configuration updated"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with patch.object(
            AutoCoderClient, "_can_use_subprocess", return_value=True
        ):
            client = AutoCoderClient()
            result = client.configure({"model": "gpt-4"})

            assert result.success is True
            assert result.message == "Configuration updated"

    def test_configure_empty_dict(self):
        """测试空配置字典"""
        client = AutoCoderClient()
        result = client.configure({})

        assert result.success is False
        assert "配置参数不能为空" in result.error

    def test_session_context_manager(self):
        """测试会话上下文管理器"""
        client = AutoCoderClient()

        # Mock query方法
        mock_results = [
            QueryResult.success_result("First response"),
            QueryResult.success_result("Second response"),
        ]

        with patch.object(
            client, "query", side_effect=mock_results
        ) as mock_query:
            with client.session() as session:
                result1 = session.query("First prompt")
                result2 = session.query("Second prompt")

                assert result1.content == "First response"
                assert result2.content == "Second response"

                # 检查调用参数
                calls = mock_query.call_args_list

                # 第一次调用不应该有continue_session
                first_options = calls[0][0][1]  # 第二个参数是options
                assert first_options.continue_session is False

                # 第二次调用应该有continue_session
                second_options = calls[1][0][1]
                assert second_options.continue_session is True

    def test_session_with_existing_session_id(self):
        """测试使用现有会话ID"""
        client = AutoCoderClient()

        mock_result = QueryResult.success_result("Response")

        with patch.object(
            client, "query", return_value=mock_result
        ) as mock_query:
            with client.session("existing_session_123") as session:
                session.query("Test prompt")

                # 检查调用参数
                options = mock_query.call_args[0][1]
                assert options.session_id == "existing_session_123"

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", True)
    def test_get_version_via_sdk(self):
        """测试通过SDK获取版本"""
        with patch("autocoder.version.__version__", "1.2.3"):
            client = AutoCoderClient()
            version = client.get_version()
            assert version == "1.2.3"

    @patch("autocoder_cli_sdk.client.SDK_AVAILABLE", False)
    @patch("subprocess.run")
    def test_get_version_via_subprocess(self, mock_run):
        """测试通过subprocess获取版本"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "AutoCoder v1.2.3"
        mock_run.return_value = mock_result

        with patch.object(
            AutoCoderClient, "_can_use_subprocess", return_value=True
        ):
            client = AutoCoderClient()
            version = client.get_version()
            assert version == "AutoCoder v1.2.3"

    def test_get_version_failure(self):
        """测试获取版本失败"""
        with patch("autocoder_cli_sdk.client.SDK_AVAILABLE", False):
            with patch.object(
                AutoCoderClient, "_can_use_subprocess", return_value=True
            ):
                with patch("subprocess.run", side_effect=Exception("Error")):
                    client = AutoCoderClient()
                    version = client.get_version()
                    assert version == "unknown"

    def test_convert_to_cli_options(self):
        """测试转换为CLI选项"""
        client = AutoCoderClient()

        options = QueryOptions(
            model="gpt-4",
            max_turns=15,
            system_prompt="Test prompt",
            verbose=True,
            async_mode=True,
            split_mode="h2",
        )

        cli_options = client._convert_to_cli_options("test prompt", options)

        assert cli_options.prompt == "test prompt"
        assert cli_options.model == "gpt-4"
        assert cli_options.max_turns == 15
        assert cli_options.system_prompt == "Test prompt"
        assert cli_options.verbose is True
        assert cli_options.async_mode is True
        assert cli_options.split_mode == "h2"

    def test_build_command_args(self):
        """测试构建命令参数"""
        client = AutoCoderClient()

        options = QueryOptions(
            model="gpt-4",
            max_turns=15,
            system_prompt="Test",
            verbose=True,
            continue_session=True,
            allowed_tools=["tool1", "tool2"],
            async_mode=True,
            split_mode="h2",
            bg_mode=True,
        )

        args = client._build_command_args(options)

        assert "--model" in args
        assert "gpt-4" in args
        assert "--max-turns" in args
        assert "15" in args
        assert "--system-prompt" in args
        assert "Test" in args
        assert "--verbose" in args
        assert "--continue" in args
        assert "--allowed-tools" in args
        assert "tool1" in args
        assert "tool2" in args
        assert "--async" in args
        assert "--split" in args
        assert "h2" in args
        assert "--bg" in args
