"""
AutoCoder CLI SDK 同步客户端

提供同步方式调用auto-coder.run功能的客户端类。
"""

import json
from contextlib import contextmanager
from typing import Dict, Generator, List, Optional, TypeVar, Union

# 导入内部SDK模块
try:
    # 尝试导入auto-coder内部模块
    from autocoder.sdk.cli.main import AutoCoderCLI
    from autocoder.sdk.cli.options import CLIOptions

    SDK_AVAILABLE = True
except ImportError:
    # 如果无法导入，将使用subprocess调用
    SDK_AVAILABLE = False

from .models import (
    AutoCoderError,
    ExecutionError,
    QueryOptions,
    QueryResult,
    SDKConfig,
    ValidationError,
)
from .process_manager import ProcessManager
from .pydantic_models import (
    ConfigResponseModel,
    QueryResponseModel,
    parse_json_response,
)

# 类型变量
T = TypeVar("T")


class AutoCoderClient:
    """
    AutoCoder CLI 同步客户端

    提供便捷的方法来调用auto-coder.run命令的各种功能，
    无需直接使用subprocess或命令行。
    """

    def __init__(self, config: Optional[SDKConfig] = None):
        """
        初始化客户端

        Args:
            config: SDK配置，如果为None则使用默认配置
        """
        self.config = config or SDKConfig()
        self._cli = None
        # 每个客户端实例独立的进程管理器，支持并发调用
        self._process_manager = ProcessManager()

        if SDK_AVAILABLE:
            self._cli = AutoCoderCLI()
        elif not self._can_use_subprocess():
            raise AutoCoderError(
                "无法使用AutoCoder SDK: 既无法导入内部模块，也无法找到auto-coder.run命令。"
                "请确保已安装auto-coder并且命令在PATH中可用。"
            )

    def _can_use_subprocess(self) -> bool:
        """检查是否可以使用subprocess调用auto-coder.run"""
        try:
            import subprocess

            # 直接运行 auto-coder.run --help 来检测命令是否存在（超时600秒）
            help_result = subprocess.run(
                ["auto-coder.run", "--help"],
                capture_output=True,
                text=True,
                timeout=600,
            )
            return help_result.returncode == 0

        except Exception:
            return False

    def query(
        self, prompt: str, options: Optional[QueryOptions] = None
    ) -> Generator[Union[str, QueryResponseModel], None, None]:
        """
        执行代码生成查询，返回generator

        Args:
            prompt: 用户提示内容
            options: 查询选项，如果为None则使用默认选项

        Yields:
            str: 如果输出格式为text，逐行输出内容
            QueryResponseModel: 如果输出格式为json，输出pydantic模型

        Raises:
            AutoCoderError: 当执行失败时
            ValidationError: 当参数验证失败时
        """
        try:
            # 准备查询选项
            query_opts = options or QueryOptions()
            merged_opts = query_opts.merge_with_config(self.config)
            merged_opts.validate()

            # 执行查询
            if SDK_AVAILABLE and self._cli:
                yield from self._execute_via_sdk_generator(prompt, merged_opts)
            else:
                yield from self._execute_via_subprocess_generator(
                    prompt, merged_opts
                )

        except Exception as e:
            if isinstance(e, (AutoCoderError, ValidationError)):
                raise
            else:
                raise AutoCoderError(f"执行查询时发生错误: {str(e)}")

    def _execute_via_sdk_generator(
        self, prompt: str, options: QueryOptions
    ) -> Generator[Union[str, QueryResponseModel], None, None]:
        """通过内部SDK执行查询，返回generator"""
        try:
            # 转换为CLI选项
            cli_options = self._convert_to_cli_options(prompt, options)

            # 执行命令
            cli_result = self._cli.run(cli_options, cwd=options.cwd)

            # 根据输出格式处理结果
            if options.output_format == "json":
                # JSON格式：解析为pydantic模型
                if cli_result.success:
                    try:
                        response_model = parse_json_response(cli_result.output)
                        yield response_model
                    except Exception as e:
                        # 解析失败，创建错误模型
                        yield self._create_error_response(
                            f"JSON解析失败: {str(e)}"
                        )
                else:
                    # 执行失败，创建错误模型
                    yield self._create_error_response(
                        cli_result.error or "执行失败"
                    )
            else:
                # 文本格式：逐行输出
                if cli_result.success:
                    # 按行分割输出
                    lines = cli_result.output.splitlines()
                    for line in lines:
                        yield line
                else:
                    raise ExecutionError(cli_result.error or "SDK执行失败")

        except Exception as e:
            if isinstance(e, ExecutionError):
                raise
            else:
                raise ExecutionError(f"SDK执行失败: {str(e)}")

    def _execute_via_subprocess_generator(
        self, prompt: str, options: QueryOptions
    ) -> Generator[Union[str, QueryResponseModel], None, None]:
        """通过subprocess执行查询，返回generator"""
        try:
            # 构建命令参数
            cmd = ["auto-coder.run"]
            cmd.extend(self._build_command_args(options))

            # 使用当前客户端实例的进程管理器启动进程
            self._process_manager.start_process(cmd, prompt, options.cwd)

            # 根据输出格式处理结果
            if options.output_format == "json":
                # JSON格式：收集所有输出然后解析
                stdout_lines = []

                try:
                    for line in self._process_manager.stream_output_sync():
                        stdout_lines.append(line)

                    # 获取stderr
                    _, stderr = self._process_manager.read_output_sync()

                    # 等待进程完成（超时8小时）
                    exit_code = self._process_manager.wait_for_completion(
                        timeout=28800
                    )

                    if exit_code is None:
                        yield self._create_error_response("进程执行超时")
                    elif exit_code == 0:
                        # 成功，解析JSON输出（可能是混合格式）
                        full_output = "\n".join(stdout_lines)
                        if full_output.strip():
                            try:
                                # 尝试解析混合输出格式
                                text_result, json_data = (
                                    self._parse_mixed_json_output(full_output)
                                )
                                if json_data:
                                    response_model = parse_json_response(
                                        json.dumps(json_data)
                                    )
                                    # 如果有文本结果，添加到响应中
                                    if text_result:
                                        response_model.metadata = {
                                            "text_result": text_result
                                        }
                                    yield response_model
                                else:
                                    # 纯JSON格式或解析失败，尝试直接解析
                                    response_model = parse_json_response(
                                        full_output
                                    )
                                    yield response_model
                            except Exception as e:
                                yield self._create_error_response(
                                    f"JSON解析失败: {str(e)}"
                                )
                        else:
                            # 空输出
                            yield self._create_error_response("无输出内容")
                    else:
                        # 执行失败
                        error_msg = (
                            stderr.strip()
                            if stderr
                            else f"命令执行失败，退出码: {exit_code}"
                        )
                        yield self._create_error_response(error_msg)

                except Exception as e:
                    # 进程异常
                    yield self._create_error_response(
                        f"进程执行异常: {str(e)}"
                    )

            elif options.output_format == "stream-json":
                # Stream-JSON格式：逐行解析JSON事件
                from .pydantic_models import (
                    QueryResponseModel,
                    StreamEventModel,
                )
                import json

                events = []
                try:
                    for line in self._process_manager.stream_output_sync():
                        line = line.strip()
                        if line and line.startswith("{"):
                            try:
                                event_data = json.loads(line)
                                event = StreamEventModel(
                                    event_type=event_data.get(
                                        "event_type", "unknown"
                                    ),
                                    data=event_data.get("data", {}),
                                    timestamp=None,
                                    session_id=event_data.get("session_id"),
                                )
                                events.append(event)
                            except json.JSONDecodeError:
                                # 跳过无法解析的行
                                continue

                    # 等待进程完成（超时8小时）
                    exit_code = self._process_manager.wait_for_completion(
                        timeout=28800
                    )

                    if exit_code is None:
                        events.append(
                            StreamEventModel(
                                event_type="error",
                                data={"error": "进程执行超时"},
                            )
                        )
                    elif exit_code != 0:
                        events.append(
                            StreamEventModel(
                                event_type="error",
                                data={
                                    "error": f"命令执行失败，退出码: {exit_code}"
                                },
                            )
                        )

                    # 创建响应模型
                    response = QueryResponseModel(events=events)
                    yield response

                except Exception as e:
                    yield self._create_error_response(
                        f"Stream-JSON处理异常: {str(e)}"
                    )
            else:
                # 文本格式：逐行流式输出
                try:
                    for line in self._process_manager.stream_output_sync():
                        yield line

                    # 检查退出状态（超时8小时）
                    exit_code = self._process_manager.wait_for_completion(
                        timeout=28800
                    )
                    if exit_code is None:
                        raise ExecutionError("进程执行超时")
                    elif exit_code != 0:
                        raise ExecutionError(
                            f"命令执行失败，退出码: {exit_code}"
                        )

                except Exception as e:
                    if isinstance(e, ExecutionError):
                        raise
                    else:
                        raise ExecutionError(f"进程执行异常: {str(e)}")

        except Exception as e:
            if isinstance(e, ExecutionError):
                raise
            else:
                raise ExecutionError(f"Subprocess执行失败: {str(e)}")

    def _create_error_response(self, error_msg: str) -> QueryResponseModel:
        """创建错误响应模型"""
        from .pydantic_models import (
            QueryResponseModel,
            StreamEventData,
            StreamEventModel,
        )

        error_event = StreamEventModel(
            event_type="error", data=StreamEventData(error=error_msg)
        )
        return QueryResponseModel(events=[error_event])

    def _parse_mixed_json_output(self, output: str) -> tuple[str, dict]:
        """
        解析json+verbose的混合输出

        Returns:
            (text_result, json_data) 元组
        """
        import json

        lines = output.split("\n")

        # 查找JSON开始位置
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        if json_start == -1:
            # 没有JSON部分，全部是文本
            return output.strip(), {}

        # 分离文本和JSON部分
        text_part = "\n".join(lines[:json_start]).strip()
        json_part = "\n".join(lines[json_start:])

        try:
            json_data = json.loads(json_part)
            return text_part, json_data
        except json.JSONDecodeError:
            # JSON解析失败，返回空字典
            return output.strip(), {}

    def _convert_to_cli_options(self, prompt: str, options: QueryOptions):
        """将QueryOptions转换为CLIOptions"""
        if not SDK_AVAILABLE:
            raise AutoCoderError("SDK不可用，无法转换CLI选项")

        return CLIOptions(
            prompt=prompt,
            model=options.model,
            max_turns=options.max_turns,
            system_prompt=options.system_prompt,
            system_prompt_path=options.system_prompt_path,
            output_format=options.output_format,
            input_format=options.input_format,
            verbose=options.verbose,
            continue_session=options.continue_session,
            resume_session=options.session_id,
            allowed_tools=options.allowed_tools or [],
            permission_mode=options.permission_mode,
            include_rules=options.include_rules,
            pr=options.pr,
            is_sub_agent=options.is_sub_agent,
            async_mode=options.async_mode,
            split_mode=options.split_mode,
            delimiter=options.delimiter,
            min_level=options.min_level,
            max_level=options.max_level,
            workdir=options.workdir,
            from_branch=options.from_branch,
            bg_mode=options.bg_mode,
            task_prefix=options.task_prefix,
            worktree_name=options.worktree_name,
        )

    def _convert_cli_result(self, cli_result, options: QueryOptions):
        """将CLIResult转换为QueryResult"""
        if cli_result.success:
            return QueryResult.success_result(
                content=cli_result.output, metadata=cli_result.debug_info or {}
            )
        else:
            return QueryResult.error_result(
                error=cli_result.error,
                content=cli_result.output,
                metadata=cli_result.debug_info or {},
            )

    def _build_command_args(self, options: QueryOptions) -> List[str]:
        """构建subprocess命令参数"""
        args = []

        # 基础选项映射
        basic_args = [
            ("--model", options.model),
            ("--system-prompt", options.system_prompt),
            ("--system-prompt-path", options.system_prompt_path),
            ("--output-format", options.output_format, "text"),
            ("--input-format", options.input_format, "text"),
            ("--permission-mode", options.permission_mode, "manual"),
            ("--resume", options.session_id),
        ]

        for flag, value, *default in basic_args:
            default_val = default[0] if default else None
            if value and value != default_val:
                args.extend([flag, str(value)])

        # 数值选项
        if options.max_turns and options.max_turns != 10000:
            args.extend(["--max-turns", str(options.max_turns)])

        # 布尔选项 - stream-json格式必须启用verbose
        verbose_required = (
            options.verbose or options.output_format == "stream-json"
        )
        bool_flags = [
            ("--verbose", verbose_required),
            ("--continue", options.continue_session),
            ("--include-rules", options.include_rules),
            ("--pr", options.pr),
            ("--is-sub-agent", options.is_sub_agent),
        ]

        for flag, enabled in bool_flags:
            if enabled:
                args.append(flag)

        # 工具列表
        if options.allowed_tools:
            args.extend(["--allowed-tools"] + options.allowed_tools)

        # 异步模式
        if options.async_mode:
            args.append("--async")

            async_args = [
                ("--split", options.split_mode, "h1"),
                ("--delimiter", options.delimiter, "==="),
                ("--workdir", options.workdir),
                ("--from", options.from_branch),
                ("--task-prefix", options.task_prefix),
                ("--worktree-name", options.worktree_name),
            ]

            for flag, value, *default in async_args:
                default_val = default[0] if default else None
                if value and value != default_val:
                    args.extend([flag, str(value)])

            # 异步数值选项
            if options.min_level != 1:
                args.extend(["--min-level", str(options.min_level)])
            if options.max_level != 3:
                args.extend(["--max-level", str(options.max_level)])
            if options.bg_mode:
                args.append("--bg")

        return args

    def abort(self) -> bool:
        """
        中止当前正在执行的查询

        Returns:
            是否成功中止
        """
        return self._process_manager.abort()

    def abort_force(self) -> bool:
        """
        强制中止当前正在执行的查询

        Returns:
            是否成功中止
        """
        return self._process_manager.abort(force=True)

    def is_running(self) -> bool:
        """
        检查是否有查询正在执行

        Returns:
            是否正在执行
        """
        return self._process_manager.is_running

    def configure(self, config_dict: Dict[str, str]) -> ConfigResponseModel:
        """执行配置命令"""
        if not config_dict:
            return ConfigResponseModel.error_response("配置参数不能为空")

        config_args = [f"{key}={value}" for key, value in config_dict.items()]

        try:
            if SDK_AVAILABLE and self._cli:
                # 使用内部SDK
                cli_options = CLIOptions(
                    command="config", config_args=config_args
                )
                cli_result = self._cli.run(cli_options)

                return (
                    ConfigResponseModel.success_response(
                        cli_result.output, config_args
                    )
                    if cli_result.success
                    else ConfigResponseModel.error_response(cli_result.error)
                )
            else:
                # 使用subprocess
                import subprocess

                result = subprocess.run(
                    ["auto-coder.run", "config"] + config_args,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                return (
                    ConfigResponseModel.success_response(
                        result.stdout, config_args
                    )
                    if result.returncode == 0
                    else ConfigResponseModel.error_response(
                        result.stderr
                        or f"配置失败，退出码: {result.returncode}"
                    )
                )

        except Exception as e:
            return ConfigResponseModel.error_response(
                f"执行配置命令时发生错误: {str(e)}"
            )

    @contextmanager
    def session(self, session_id: Optional[str] = None):
        """
        会话上下文管理器，方便进行多轮对话

        Args:
            session_id: 会话ID，如果为None则创建新会话

        Example:
            >>> with client.session() as session:
            ...     result1 = session.query("创建一个函数")
            ...     result2 = session.query("为这个函数添加测试")
        """

        class SessionContext:
            def __init__(
                self, client: "AutoCoderClient", session_id: Optional[str]
            ):
                self.client = client
                self.session_id = session_id
                self.first_query = True

            def query(
                self, prompt: str, options: Optional[QueryOptions] = None
            ) -> Generator[Union[str, QueryResponseModel], None, None]:
                """在会话上下文中执行查询"""
                query_opts = options or QueryOptions()

                if self.first_query:
                    if self.session_id:
                        # 恢复现有会话
                        query_opts.session_id = self.session_id
                    # 首次查询不设置continue_session
                    self.first_query = False
                else:
                    # 后续查询继续会话
                    query_opts.continue_session = True

                yield from self.client.query(prompt, query_opts)

            def quick_query(self, prompt: str, **kwargs) -> str:
                """会话中的快速查询"""
                return "\n".join(
                    self.query(
                        prompt, QueryOptions(output_format="text", **kwargs)
                    )
                )

            def json_query(self, prompt: str, **kwargs) -> QueryResponseModel:
                """会话中的JSON查询"""
                for response in self.query(
                    prompt, QueryOptions(output_format="json", **kwargs)
                ):
                    return response

        session_ctx = SessionContext(self, session_id)
        try:
            yield session_ctx
        finally:
            # 会话清理工作
            pass

    def get_version(self) -> str:
        """获取AutoCoder版本信息"""
        try:
            if SDK_AVAILABLE:
                from autocoder.version import __version__

                return __version__
            else:
                import subprocess

                result = subprocess.run(
                    ["auto-coder.run", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return (
                    result.stdout.strip()
                    if result.returncode == 0
                    else "unknown"
                )
        except Exception:
            return "unknown"

    def check_availability(self) -> Dict[str, bool]:
        """检查各种功能的可用性"""
        return {
            "sdk_available": SDK_AVAILABLE,
            "subprocess_available": self._can_use_subprocess(),
            "version_available": self.get_version() != "unknown",
        }

    # 便利方法
    def quick_query(self, prompt: str, **kwargs) -> str:
        """快速查询，返回文本结果"""
        options = QueryOptions(output_format="text", **kwargs)
        return "\n".join(self.query(prompt, options))

    def json_query(self, prompt: str, **kwargs) -> QueryResponseModel:
        """JSON查询，返回Pydantic模型"""
        options = QueryOptions(output_format="json", **kwargs)
        for response in self.query(prompt, options):
            return response

    def query_from_file(
        self, file_path: str, options: Optional[QueryOptions] = None
    ) -> Generator[Union[str, QueryResponseModel], None, None]:
        """从文件读取提示内容并查询"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                raise ValueError(f"文件 {file_path} 为空")

            # 根据输入格式处理内容
            query_opts = options or QueryOptions()
            processed_prompt = self._process_input(
                content, query_opts.input_format
            )

            yield from self.query(processed_prompt, query_opts)

        except Exception as e:
            raise AutoCoderError(f"从文件读取失败: {str(e)}")

    def _process_input(self, content: str, input_format: str) -> str:
        """处理输入内容格式"""
        if input_format == "text":
            return content
        elif input_format == "json":
            try:
                import json

                data = json.loads(content)
                # 尝试提取提示内容
                if isinstance(data, dict):
                    if "prompt" in data:
                        return data["prompt"]
                    elif "message" in data:
                        message = data["message"]
                        if isinstance(message, dict) and "content" in message:
                            return message["content"]
                        elif isinstance(message, str):
                            return message
                return content  # 如果无法提取，返回原始内容
            except json.JSONDecodeError:
                return content  # JSON解析失败，返回原始内容
        else:
            # stream-json 或其他格式，直接返回
            return content
