"""
AutoCoder CLI SDK

一个便于在Python代码中调用auto-coder.run功能的SDK，
无需直接使用subprocess或fork进程。

基本用法:
    >>> from autocoder_cli_sdk import AutoCoderClient
    >>>
    >>> client = AutoCoderClient()
    >>> for line in client.query("创建一个简单的Python函数"):
    ...     print(line)

异步用法:
    >>> import asyncio
    >>> from autocoder_cli_sdk import AsyncAutoCoderClient
    >>>
    >>> async def main():
    ...     async with AsyncAutoCoderClient() as client:
    ...         async for line in client.query("创建一个简单的Python函数"):
    ...             print(line)
    >>>
    >>> asyncio.run(main())
"""

from .async_client import AsyncAutoCoderClient
from .client import AutoCoderClient
from .diagnostics import (
    get_recommendations,
    print_diagnostics,
    run_diagnostics,
)
from .models import (
    AutoCoderError,
    ConfigResult,
    ExecutionError,
    QueryOptions,
    QueryResult,
    SDKConfig,
    SessionInfo,
    StreamEvent,
    ValidationError,
)
from .process_manager import (
    AsyncProcessManager,
    ProcessManager,
)
from .pydantic_models import (
    CompletionEventModel,
    ConfigResponseModel,
    ContentEventModel,
    EndEventModel,
    ErrorEventModel,
    QueryResponseModel,
    StartEventModel,
    StreamEventModel,
    VersionResponseModel,
)

__version__ = "1.0.1"
__author__ = "AutoCoder Team"
__email__ = "support@autocoder.com"

__all__ = [
    # 客户端类
    "AutoCoderClient",
    "AsyncAutoCoderClient",
    # 配置和选项
    "SDKConfig",
    "QueryOptions",
    # 响应类型
    "QueryResult",
    "StreamEvent",
    "ConfigResult",
    "SessionInfo",
    # Pydantic响应模型
    "QueryResponseModel",
    "StreamEventModel",
    "ConfigResponseModel",
    "VersionResponseModel",
    "CompletionEventModel",
    "ContentEventModel",
    "ErrorEventModel",
    "StartEventModel",
    "EndEventModel",
    # 进程管理
    "ProcessManager",
    "AsyncProcessManager",
    # 诊断工具
    "run_diagnostics",
    "print_diagnostics",
    "get_recommendations",
    # 异常
    "AutoCoderError",
    "ValidationError",
    "ExecutionError",
    # 元数据
    "__version__",
]
