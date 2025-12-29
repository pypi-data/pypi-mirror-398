# AutoCoder CLI SDK for Python

auto-coder.chat 的 python SDK。 可以通过引入该包实现代码修改等功能。

## 特性

- **易于使用**: 提供简洁直观的API接口，支持快速查询方法
- **同步/异步**: 同时支持同步和异步调用方式
- **Generator接口**: 流式输出支持，逐行处理结果
- **会话管理**: 内置会话上下文管理，支持多轮对话
- **并发支持**: 异步客户端支持批量并发查询
- **完整配置**: 支持所有auto-coder.run命令行选项
- **双模式运行**: 自动检测并使用内部SDK或subprocess调用
- **类型提示**: 完整的类型提示和Pydantic模型支持
- **诊断工具**: 内置环境诊断功能，快速排查问题

## 安装

### 使用 pip

```bash
pip install autocoder-cli-sdk
```

## 快速开始

### 最简单用法（便利方法）

```python
from autocoder_cli_sdk import AutoCoderClient

client = AutoCoderClient()

# 快速查询，返回完整文本结果
result = client.quick_query("创建一个Python函数来计算斐波那契数列")
print(result)

# JSON格式查询，返回Pydantic模型
response = client.json_query("创建一个简单的类")
print(f"事件总数: {response.summary.total_events}")
print(f"最终结果: {response.final_result}")
```

### Generator接口（流式输出）

```python
from autocoder_cli_sdk import AutoCoderClient, QueryOptions

client = AutoCoderClient()

# 文本格式 - 逐行输出
options = QueryOptions(output_format="text")
for line in client.query("创建一个Python函数", options):
    print(line)

# JSON格式 - 返回Pydantic模型
options = QueryOptions(output_format="json")
for response in client.query("创建一个Python类", options):
    if response.has_errors:
        print(f"错误: {response.error_messages}")
    else:
        print(f"结果: {response.final_result}")
```

### 异步用法

```python
import asyncio
from autocoder_cli_sdk import AsyncAutoCoderClient, QueryOptions

async def main():
    async with AsyncAutoCoderClient() as client:
        # 快速查询
        result = await client.quick_query("创建一个排序函数")
        print(result)
        
        # Generator接口
        async for line in client.query("创建一个Python类", QueryOptions(output_format="text")):
            print(line)

asyncio.run(main())
```

### 批量并发查询

```python
import asyncio
from autocoder_cli_sdk import AsyncAutoCoderClient

async def main():
    async with AsyncAutoCoderClient() as client:
        prompts = [
            "创建一个用户管理模块",
            "创建一个日志模块",
            "创建一个配置管理模块"
        ]
        
        # 并发执行，最大并发数为2
        results = await client.batch_query(prompts, max_concurrency=2)
        
        for i, result in enumerate(results):
            print(f"查询 {i+1}: 完成")

asyncio.run(main())
```

### 中止操作

```python
import threading
from autocoder_cli_sdk import AutoCoderClient

client = AutoCoderClient()

# 在另一个线程中启动查询
def run_query():
    for line in client.query("复杂的查询任务"):
        print(line)

thread = threading.Thread(target=run_query)
thread.start()

# 5秒后中止
import time
time.sleep(5)
if client.is_running():
    client.abort()  # 优雅中止
    # 或者 client.abort_force()  # 强制中止
```

### 会话管理

```python
from autocoder_cli_sdk import AutoCoderClient

client = AutoCoderClient()

# 使用会话上下文进行多轮对话
with client.session() as session:
    # 第一轮
    result1 = session.quick_query("创建一个User类")
    print(f"第一轮: {len(result1)} 字符")
    
    # 第二轮（基于第一轮的上下文）
    result2 = session.quick_query("为User类添加验证方法")
    print(f"第二轮: {len(result2)} 字符")
    
    # JSON格式查询
    response = session.json_query("添加单元测试")
    print(f"第三轮事件数: {response.summary.total_events}")
```

## API 文档

### 客户端类

#### `AutoCoderClient` (同步客户端)

```python
class AutoCoderClient:
    def __init__(self, config: Optional[SDKConfig] = None)
    
    # 核心方法 - Generator接口
    def query(self, prompt: str, options: Optional[QueryOptions] = None) -> Generator[Union[str, QueryResponseModel], None, None]
    
    # 便利方法
    def quick_query(self, prompt: str, **kwargs) -> str
    def json_query(self, prompt: str, **kwargs) -> QueryResponseModel
    def query_from_file(self, file_path: str, options: Optional[QueryOptions] = None) -> Generator
    
    # 配置和状态
    def configure(self, config_dict: Dict[str, str]) -> ConfigResponseModel
    def get_version(self) -> str
    def check_availability(self) -> Dict[str, bool]
    
    # 进程控制
    def is_running(self) -> bool
    def abort(self) -> bool
    def abort_force(self) -> bool
    
    # 会话管理
    def session(self, session_id: Optional[str] = None) -> ContextManager
```

#### `AsyncAutoCoderClient` (异步客户端)

```python
class AsyncAutoCoderClient:
    async def __aenter__(self)
    async def __aexit__(...)
    
    # 核心方法 - AsyncGenerator接口
    async def query(self, prompt: str, options: Optional[QueryOptions] = None) -> AsyncGenerator[Union[str, QueryResponseModel], None]
    
    # 便利方法
    async def quick_query(self, prompt: str, **kwargs) -> str
    async def json_query(self, prompt: str, **kwargs) -> QueryResponseModel
    
    # 批量查询
    async def batch_query(self, prompts: List[str], options: Optional[QueryOptions] = None, max_concurrency: int = 3) -> List[Union[List[str], QueryResponseModel]]
    
    # 配置和状态
    async def configure(self, config_dict: Dict[str, str]) -> ConfigResponseModel
    async def get_version(self) -> str
    
    # 进程控制
    @property
    def is_running(self) -> bool
    async def abort(self) -> bool
    async def abort_force(self) -> bool
    
    # 会话管理
    async def session(self, session_id: Optional[str] = None) -> AsyncContextManager
```

### 配置类

#### `SDKConfig` (SDK全局配置)

```python
@dataclass
class SDKConfig:
    # 基础设置
    default_model: Optional[str] = None
    default_max_turns: int = 10000
    default_permission_mode: str = "manual"  # manual, acceptEdits
    default_output_format: str = "text"      # text, json, stream-json
    verbose: bool = False
    
    # 路径设置
    default_cwd: Optional[str] = None
    system_prompt_path: Optional[str] = None
    
    # 高级设置
    include_rules: bool = False
    default_allowed_tools: Optional[List[str]] = None
```

#### `QueryOptions` (查询选项)

```python
@dataclass
class QueryOptions:
    # 基础查询选项
    model: Optional[str] = None
    max_turns: Optional[int] = None
    system_prompt: Optional[str] = None
    system_prompt_path: Optional[str] = None
    output_format: str = "text"    # text, json, stream-json
    input_format: str = "text"     # text, json, stream-json
    verbose: bool = False
    cwd: Optional[str] = None
    
    # 会话管理
    session_id: Optional[str] = None
    continue_session: bool = False
    
    # 工具和权限
    allowed_tools: Optional[List[str]] = None
    permission_mode: str = "manual"
    
    # 高级选项
    include_rules: bool = False
    pr: bool = False
    is_sub_agent: bool = False
    
    # 异步代理运行器选项
    async_mode: bool = False
    split_mode: str = "h1"         # h1, h2, h3, any, delimiter
    delimiter: str = "==="
    min_level: int = 1
    max_level: int = 3
    workdir: Optional[str] = None
    from_branch: str = ""
    bg_mode: bool = False
    task_prefix: str = ""
    worktree_name: Optional[str] = None
```

### Pydantic响应模型

#### `QueryResponseModel` (JSON格式查询响应)

```python
class QueryResponseModel(BaseModel):
    events: List[StreamEventModel] = []
    summary: QuerySummaryModel
    session_id: Optional[str] = None
    execution_time: Optional[float] = None
    
    @property
    def final_result(self) -> str           # 获取最终结果
    @property
    def all_content(self) -> str            # 获取所有内容拼接
    @property
    def has_errors(self) -> bool            # 检查是否有错误
    @property
    def error_messages(self) -> List[str]   # 获取所有错误消息
```

#### `QuerySummaryModel` (查询摘要)

```python
class QuerySummaryModel(BaseModel):
    total_events: int = 0
    start_events: int = 0
    completion_events: int = 0
    error_events: int = 0
    content_events: int = 0
    tool_call_events: int = 0
```

#### `StreamEventModel` (流式事件)

```python
class StreamEventModel(BaseModel):
    event_type: str           # start, content, tool_call, completion, error, end
    data: StreamEventData
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
```

#### `ConfigResponseModel` (配置响应)

```python
class ConfigResponseModel(BaseModel):
    success: bool
    message: str = ""
    error: Optional[str] = None
    applied_configs: List[str] = []
```

### Dataclass响应类型

#### `QueryResult` (查询结果 - 内部使用)

```python
@dataclass
class QueryResult:
    success: bool
    content: str
    error: Optional[str] = None
    session_id: Optional[str] = None
    events: List[StreamEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    
    @property
    def is_success(self) -> bool
    @property
    def has_error(self) -> bool
```

#### `StreamEvent` (流式事件 - Dataclass版)

```python
@dataclass
class StreamEvent:
    event_type: str  # start, content, tool_call, completion, error, end
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    @property
    def is_content(self) -> bool
    @property
    def content(self) -> str
```

## 高级用法

### 自定义配置

```python
from autocoder_cli_sdk import AutoCoderClient, SDKConfig, QueryOptions

# 全局配置
config = SDKConfig(
    default_model="gpt-4",
    default_max_turns=20,
    verbose=True,
    default_permission_mode="acceptEdits"
)

client = AutoCoderClient(config)

# 查询特定选项
options = QueryOptions(
    max_turns=15,
    system_prompt="你是一个Python专家",
    output_format="json",
    include_rules=True
)

response = client.json_query("创建一个数据结构", **options.__dict__)
```

### 配置管理

```python
from autocoder_cli_sdk import AutoCoderClient

client = AutoCoderClient()

# 设置配置
result = client.configure({
    "model": "gpt-4",
    "max_turns": "25",
    "permission_mode": "acceptEdits"
})

if result.success:
    print("配置更新成功")
    print("应用的配置:", result.applied_configs)
else:
    print("配置失败:", result.error)
```

### 异步代理运行器

```python
from autocoder_cli_sdk import AutoCoderClient, QueryOptions

client = AutoCoderClient()

# 使用异步代理运行器模式
options = QueryOptions(
    async_mode=True,
    split_mode="h1",
    workdir="/path/to/work",
    bg_mode=False,
    task_prefix="feature-"
)

for line in client.query("""
# 任务1：用户管理模块

创建用户管理相关功能...

# 任务2：权限管理模块

创建权限管理相关功能...
""", options):
    print(line)
```

### 从文件读取提示

```python
from autocoder_cli_sdk import AutoCoderClient, QueryOptions

client = AutoCoderClient()

# 从文件读取提示内容并执行查询
for line in client.query_from_file("prompt.txt", QueryOptions(output_format="text")):
    print(line)

# 支持JSON格式输入
options = QueryOptions(input_format="json", output_format="json")
for response in client.query_from_file("prompt.json", options):
    print(response.final_result)
```

### 诊断工具

```python
from autocoder_cli_sdk import run_diagnostics, print_diagnostics, get_recommendations

# 运行完整诊断
results = run_diagnostics(verbose=True)

# 获取建议
recommendations = get_recommendations(results)
for rec in recommendations:
    print(f"- {rec}")
```

诊断工具会检查：
- Python环境信息
- 依赖包安装状态
- auto-coder.run命令可用性
- SDK功能完整性

## 示例项目

查看 `examples/` 目录中的完整示例：

- `quick_start.py` - 快速开始示例，最常用的用法
- `basic_usage.py` - 基础用法演示
- `async_usage.py` - 异步用法演示
- `session_management.py` - 会话管理演示
- `generator_usage.py` - Generator接口详解
- `feature_coverage_test.py` - 功能覆盖测试

运行示例：

```bash
# 使用 uv (推荐)
uv run python examples/quick_start.py
uv run python examples/basic_usage.py
uv run python examples/async_usage.py

# 或使用开发脚本
python scripts/dev.py example quick_start
python scripts/dev.py example basic_usage
```

## 错误处理

```python
from autocoder_cli_sdk import (
    AutoCoderClient,
    AutoCoderError,
    ValidationError,
    ExecutionError
)

client = AutoCoderClient()

try:
    for line in client.query("创建一个函数"):
        print(line)
        
except ValidationError as e:
    print("参数验证失败:", e)
except ExecutionError as e:
    print("执行错误:", e)
    print("退出码:", e.exit_code)
    print("输出:", e.output)
except AutoCoderError as e:
    print("SDK错误:", e)
except Exception as e:
    print("未知错误:", e)
```

## 依赖说明

这个SDK设计为双模式运行：

1. **内部SDK模式**: 如果可以导入`autocoder.sdk`模块，将直接使用内部API，性能更好
2. **Subprocess模式**: 如果无法导入内部模块，将回退到调用`auto-coder.run`命令行工具

两种模式API完全一致，用户无需关心底层实现。可以通过以下方式检查：

```python
from autocoder_cli_sdk import AutoCoderClient

client = AutoCoderClient()
availability = client.check_availability()
print(f"内部SDK可用: {availability['sdk_available']}")
print(f"命令行可用: {availability['subprocess_available']}")
```

## 类型提示

SDK提供完整的类型提示支持，包括：
- 所有公开类和方法的类型注解
- Pydantic模型的字段类型
- py.typed 标记文件

```python
from typing import Optional
from autocoder_cli_sdk import (
    AutoCoderClient,
    QueryOptions,
    QueryResponseModel,
    SDKConfig
)

config: SDKConfig = SDKConfig(verbose=True)
client: AutoCoderClient = AutoCoderClient(config)
options: Optional[QueryOptions] = QueryOptions(max_turns=10)

# json_query 返回 QueryResponseModel
response: QueryResponseModel = client.json_query("prompt", **options.__dict__)

# quick_query 返回 str
result: str = client.quick_query("prompt")
```


