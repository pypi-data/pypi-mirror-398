"""
AutoCoder CLI SDK 异步客户端

提供异步方式调用auto-coder.run功能的客户端类。
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Optional, Union

# 导入内部SDK模块
try:
    from autocoder.sdk.core import AutoCoderCore
    from autocoder.sdk.models.options import AutoCodeOptions

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

from .models import (
    AutoCoderError,
    ExecutionError,
    QueryOptions,
    SDKConfig,
    ValidationError,
)
from .process_manager import AsyncProcessManager
from .pydantic_models import (
    ConfigResponseModel,
    QueryResponseModel,
    StreamEventModel,
    parse_json_response,
)


class AsyncAutoCoderClient:
    """
    AutoCoder CLI 异步客户端

    提供异步方式调用auto-coder.run命令的各种功能，
    支持流式处理和并发查询。
    """

    def __init__(self, config: Optional[SDKConfig] = None):
        """
        初始化异步客户端

        Args:
            config: SDK配置，如果为None则使用默认配置
        """
        self.config = config or SDKConfig()
        self._loop = None
        self._executor = None
        # 每个客户端实例独立的异步进程管理器，支持并发调用
        self._process_manager = AsyncProcessManager()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._loop = asyncio.get_event_loop()
        # 使用ThreadPoolExecutor来处理同步操作
        import concurrent.futures

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        self._loop = None

    async def query(
        self, prompt: str, options: Optional[QueryOptions] = None
    ) -> AsyncGenerator[Union[str, QueryResponseModel], None]:
        """执行异步代码生成查询，返回AsyncGenerator"""
        try:
            query_opts = options or QueryOptions()
            merged_opts = query_opts.merge_with_config(self.config)
            merged_opts.validate()

            executor = (
                self._execute_via_sdk_async_generator
                if SDK_AVAILABLE
                else self._execute_via_subprocess_async_generator
            )

            async for item in executor(prompt, merged_opts):
                yield item

        except Exception as e:
            if isinstance(e, (AutoCoderError, ValidationError)):
                raise
            else:
                raise AutoCoderError(f"执行异步查询时发生错误: {str(e)}")

    async def _execute_via_sdk_async_generator(
        self, prompt: str, options: QueryOptions
    ) -> AsyncGenerator[Union[str, QueryResponseModel], None]:
        """通过内部SDK执行异步查询，返回generator"""
        try:
            # 转换为AutoCodeOptions
            core_options = AutoCodeOptions(
                max_turns=options.max_turns or 10000,
                system_prompt=options.system_prompt,
                cwd=options.cwd or os.getcwd(),
                allowed_tools=options.allowed_tools or [],
                permission_mode=options.permission_mode,
                output_format=options.output_format,
                stream=True,
                session_id=options.session_id,
                continue_session=options.continue_session,
                model=options.model,
                verbose=options.verbose,
                include_rules=options.include_rules,
                pr=options.pr,
                is_sub_agent=options.is_sub_agent,
            )

            # 创建核心实例
            core = AutoCoderCore(core_options)

            if options.output_format == "json":
                # JSON格式：收集所有事件然后返回模型
                all_events = []
                async for event in core.query_stream(
                    prompt, show_terminal=options.verbose
                ):
                    stream_event = StreamEventModel(
                        event_type=getattr(event, "event_type", "unknown"),
                        data=getattr(event, "data", {}),
                    )
                    all_events.append(stream_event)

                # 创建响应模型
                from .pydantic_models import (
                    QueryResponseModel,
                    QuerySummaryModel,
                )

                summary = QuerySummaryModel(
                    total_events=len(all_events),
                    completion_events=len(
                        [e for e in all_events if e.event_type == "completion"]
                    ),
                    error_events=len(
                        [e for e in all_events if e.event_type == "error"]
                    ),
                    content_events=len(
                        [e for e in all_events if e.event_type == "content"]
                    ),
                )

                response_model = QueryResponseModel(
                    events=all_events,
                    summary=summary,
                    session_id=options.session_id,
                )
                yield response_model
            else:
                # 文本格式：流式输出
                async for event in core.query_stream(
                    prompt, show_terminal=options.verbose
                ):
                    if hasattr(event, "event_type") and event.event_type in [
                        "content",
                        "completion",
                    ]:
                        content = ""
                        if event.event_type == "content" and hasattr(
                            event, "data"
                        ):
                            content = event.data.get("content", "")
                        elif event.event_type == "completion" and hasattr(
                            event, "data"
                        ):
                            content = event.data.get("result", "")

                        if content:
                            # 按行分割输出
                            for line in content.splitlines():
                                yield line

        except Exception as e:
            raise ExecutionError(f"SDK异步执行失败: {str(e)}")

    async def _execute_via_subprocess_async_generator(
        self, prompt: str, options: QueryOptions
    ) -> AsyncGenerator[Union[str, QueryResponseModel], None]:
        """通过subprocess执行异步查询，返回generator"""
        try:
            # 构建命令参数
            cmd = ["auto-coder.run"]
            cmd.extend(self._build_command_args(options))

            # 使用当前客户端实例的异步进程管理器
            await self._process_manager.start_process(cmd, prompt, options.cwd)

            # 根据输出格式处理结果
            if options.output_format == "json":
                # JSON格式：收集所有输出然后解析
                output_lines = []
                async for line in self._process_manager.stream_output_async():
                    output_lines.append(line)

                # 等待进程完成（超时8小时）
                exit_code = await self._process_manager.wait_for_completion(
                    timeout=28800
                )

                if exit_code == 0:
                    try:
                        full_output = "\n".join(output_lines)
                        response_model = parse_json_response(full_output)
                        yield response_model
                    except Exception as e:
                        # JSON解析失败
                        from .pydantic_models import (
                            QueryResponseModel,
                            StreamEventData,
                            StreamEventModel,
                        )

                        error_event = StreamEventModel(
                            event_type="error",
                            data=StreamEventData(
                                error=f"JSON解析失败: {str(e)}"
                            ),
                        )
                        yield QueryResponseModel(events=[error_event])
                else:
                    # 执行失败
                    error_msg = f"命令执行失败，退出码: {exit_code}"
                    from .pydantic_models import (
                        QueryResponseModel,
                        StreamEventData,
                        StreamEventModel,
                    )

                    error_event = StreamEventModel(
                        event_type="error",
                        data=StreamEventData(error=error_msg),
                    )
                    yield QueryResponseModel(events=[error_event])
            else:
                # 文本格式：流式输出
                async for line in self._process_manager.stream_output_async():
                    yield line

                # 检查退出状态（超时8小时）
                exit_code = await self._process_manager.wait_for_completion(
                    timeout=28800
                )
                if exit_code != 0:
                    raise ExecutionError(f"命令执行失败，退出码: {exit_code}")

        except Exception as e:
            if isinstance(e, ExecutionError):
                raise
            else:
                raise ExecutionError(f"Subprocess异步执行失败: {str(e)}")

    def _build_command_args(self, options: QueryOptions) -> List[str]:
        """构建命令参数"""
        args = []

        # 基础选项
        if options.model:
            args.extend(["--model", options.model])

        if options.max_turns and options.max_turns != 10000:
            args.extend(["--max-turns", str(options.max_turns)])

        if options.system_prompt:
            args.extend(["--system-prompt", options.system_prompt])

        if options.output_format != "text":
            args.extend(["--output-format", options.output_format])

        if options.verbose:
            args.append("--verbose")

        # 会话选项
        if options.continue_session:
            args.append("--continue")

        if options.session_id:
            args.extend(["--resume", options.session_id])

        # 工具和权限
        if options.allowed_tools:
            args.extend(["--allowed-tools"] + options.allowed_tools)

        if options.permission_mode != "manual":
            args.extend(["--permission-mode", options.permission_mode])

        # 高级选项
        if options.include_rules:
            args.append("--include-rules")

        if options.pr:
            args.append("--pr")

        if options.is_sub_agent:
            args.append("--is-sub-agent")

        # 异步模式
        if options.async_mode:
            args.append("--async")

            if options.split_mode != "h1":
                args.extend(["--split", options.split_mode])

            if options.delimiter != "===":
                args.extend(["--delimiter", options.delimiter])

            if options.min_level != 1:
                args.extend(["--min-level", str(options.min_level)])

            if options.max_level != 3:
                args.extend(["--max-level", str(options.max_level)])

            if options.workdir:
                args.extend(["--workdir", options.workdir])

            if options.from_branch:
                args.extend(["--from", options.from_branch])

            if options.bg_mode:
                args.append("--bg")

            if options.task_prefix:
                args.extend(["--task-prefix", options.task_prefix])

            if options.worktree_name:
                args.extend(["--worktree-name", options.worktree_name])

        return args

    async def abort(self) -> bool:
        """
        中止当前正在执行的查询

        Returns:
            是否成功中止
        """
        return await self._process_manager.abort()

    async def abort_force(self) -> bool:
        """
        强制中止当前正在执行的查询

        Returns:
            是否成功中止
        """
        return await self._process_manager.abort(force=True)

    @property
    def is_running(self) -> bool:
        """
        检查是否有查询正在执行

        Returns:
            是否正在执行
        """
        return self._process_manager.is_running

    async def configure(
        self, config_dict: Dict[str, str]
    ) -> ConfigResponseModel:
        """
        执行异步配置命令

        Args:
            config_dict: 配置字典

        Returns:
            配置结果
        """
        try:
            if not config_dict:
                return ConfigResponseModel.error_response("配置参数不能为空")

            # 转换为config命令参数格式
            config_args = [
                f"{key}={value}" for key, value in config_dict.items()
            ]

            if SDK_AVAILABLE:
                # 使用内部SDK（在线程池中执行同步操作）
                def sync_configure():
                    from autocoder.sdk.cli.main import AutoCoderCLI
                    from autocoder.sdk.cli.options import CLIOptions

                    cli = AutoCoderCLI()
                    cli_options = CLIOptions(
                        command="config", config_args=config_args
                    )

                    return cli.run(cli_options)

                loop = asyncio.get_event_loop()
                if not self._executor:
                    import concurrent.futures

                    self._executor = concurrent.futures.ThreadPoolExecutor(
                        max_workers=2
                    )

                cli_result = await loop.run_in_executor(
                    self._executor, sync_configure
                )

                if cli_result.success:
                    return ConfigResponseModel.success_response(
                        message=cli_result.output, applied_configs=config_args
                    )
                else:
                    return ConfigResponseModel.error_response(cli_result.error)
            else:
                # 使用subprocess
                cmd = ["auto-coder.run", "config"] + config_args

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    return ConfigResponseModel.success_response(
                        message=stdout.decode("utf-8"),
                        applied_configs=config_args,
                    )
                else:
                    return ConfigResponseModel.error_response(
                        stderr.decode("utf-8")
                        or f"配置失败，退出码: {process.returncode}"
                    )

        except Exception as e:
            return ConfigResponseModel.error_response(
                f"执行异步配置命令时发生错误: {str(e)}"
            )

    @asynccontextmanager
    async def session(self, session_id: Optional[str] = None):
        """
        异步会话上下文管理器

        Args:
            session_id: 会话ID

        Example:
            >>> async with client.session() as session:
            ...     result1 = await session.query("创建一个函数")
            ...     result2 = await session.query("为这个函数添加测试")
        """

        class AsyncSessionContext:
            def __init__(
                self, client: "AsyncAutoCoderClient", session_id: Optional[str]
            ):
                self.client = client
                self.session_id = session_id
                self.first_query = True

            async def query(
                self, prompt: str, options: Optional[QueryOptions] = None
            ) -> AsyncGenerator[Union[str, QueryResponseModel], None]:
                """在会话上下文中执行异步查询"""
                query_opts = options or QueryOptions()

                if self.first_query:
                    if self.session_id:
                        query_opts.session_id = self.session_id
                    self.first_query = False
                else:
                    query_opts.continue_session = True

                async for item in self.client.query(prompt, query_opts):
                    yield item

        session_ctx = AsyncSessionContext(self, session_id)
        try:
            yield session_ctx
        finally:
            # 会话清理工作
            pass

    async def batch_query(
        self,
        prompts: List[str],
        options: Optional[QueryOptions] = None,
        max_concurrency: int = 3,
    ) -> List[Union[List[str], QueryResponseModel]]:
        """
        批量执行多个查询，支持并发控制

        Args:
            prompts: 提示列表
            options: 查询选项
            max_concurrency: 最大并发数

        Returns:
            查询结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def single_query(
            prompt: str,
        ) -> Union[List[str], QueryResponseModel]:
            async with semaphore:
                results = []
                async for item in self.query(prompt, options):
                    if isinstance(item, str):
                        results.append(item)
                    else:
                        return item  # QueryResponseModel
                return results  # List[str]

        # 并发执行所有查询
        tasks = [single_query(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 异常转换为错误响应
                if options and options.output_format == "json":
                    error_event = StreamEventModel(
                        event_type="error",
                        data={"error": f"查询 {i+1} 失败: {str(result)}"},
                    )
                    processed_results.append(
                        QueryResponseModel(events=[error_event])
                    )
                else:
                    processed_results.append([f"错误: {str(result)}"])
            else:
                processed_results.append(result)

        return processed_results

    async def get_version(self) -> str:
        """
        获取AutoCoder版本信息（异步）

        Returns:
            版本字符串
        """
        try:
            if SDK_AVAILABLE:

                def get_version_sync():
                    try:
                        from autocoder.version import __version__

                        return __version__
                    except ImportError:
                        return "unknown"

                loop = asyncio.get_event_loop()
                if not self._executor:
                    import concurrent.futures

                    self._executor = concurrent.futures.ThreadPoolExecutor(
                        max_workers=1
                    )

                return await loop.run_in_executor(
                    self._executor, get_version_sync
                )
            else:
                # 使用subprocess
                process = await asyncio.create_subprocess_exec(
                    "auto-coder.run",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, _ = await process.communicate()

                if process.returncode == 0:
                    return stdout.decode("utf-8").strip()
                else:
                    return "unknown"
        except Exception:
            return "unknown"

    # 便利方法
    async def quick_query(self, prompt: str, **kwargs) -> str:
        """快速异步查询，返回文本结果"""
        options = QueryOptions(output_format="text", **kwargs)
        lines = []
        async for line in self.query(prompt, options):
            lines.append(line)
        return "\n".join(lines)

    async def json_query(self, prompt: str, **kwargs) -> QueryResponseModel:
        """异步JSON查询，返回Pydantic模型"""
        options = QueryOptions(output_format="json", **kwargs)
        async for response in self.query(prompt, options):
            return response
