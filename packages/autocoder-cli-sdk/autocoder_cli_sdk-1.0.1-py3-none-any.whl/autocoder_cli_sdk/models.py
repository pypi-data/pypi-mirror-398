"""
AutoCoder CLI SDK 数据模型

定义SDK中使用的各种数据结构和异常类。
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class AutoCoderError(Exception):
    """SDK基础异常类"""

    pass


class ValidationError(AutoCoderError):
    """参数验证异常"""

    pass


class ExecutionError(AutoCoderError):
    """执行异常"""

    def __init__(self, message: str, exit_code: int = 1, output: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.output = output


@dataclass
class SDKConfig:
    """SDK全局配置"""

    # 基础设置
    default_model: Optional[str] = None
    default_max_turns: int = 10000
    default_permission_mode: str = "manual"  # manual, acceptEdits
    default_output_format: str = "text"  # text, json, stream-json
    verbose: bool = False

    # 路径设置
    default_cwd: Optional[str] = None
    system_prompt_path: Optional[str] = None

    # 高级设置
    include_rules: bool = False
    default_allowed_tools: Optional[List[str]] = None

    def __post_init__(self):
        """初始化后验证"""
        if self.default_cwd is None:
            self.default_cwd = os.getcwd()

        # 验证输出格式
        valid_formats = ["text", "json", "stream-json"]
        if self.default_output_format not in valid_formats:
            raise ValidationError(
                f"不支持的输出格式: {self.default_output_format}"
            )

        # 验证权限模式
        valid_permissions = ["manual", "acceptEdits"]
        if self.default_permission_mode not in valid_permissions:
            raise ValidationError(
                f"不支持的权限模式: {self.default_permission_mode}"
            )


@dataclass
class QueryOptions:
    """单次查询的配置选项"""

    # 基础查询选项
    model: Optional[str] = None
    max_turns: Optional[int] = None
    system_prompt: Optional[str] = None
    system_prompt_path: Optional[str] = None
    output_format: str = "text"  # text, json, stream-json
    input_format: str = "text"  # text, json, stream-json
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
    split_mode: str = "h1"  # h1, h2, h3, any, delimiter
    delimiter: str = "==="
    min_level: int = 1
    max_level: int = 3
    workdir: Optional[str] = None
    from_branch: str = ""
    bg_mode: bool = False
    task_prefix: str = ""
    worktree_name: Optional[str] = None

    def merge_with_config(self, config: SDKConfig) -> "QueryOptions":
        """与全局配置合并，返回新的选项对象"""
        merged = QueryOptions(
            model=self.model or config.default_model,
            max_turns=self.max_turns or config.default_max_turns,
            system_prompt=self.system_prompt,
            system_prompt_path=self.system_prompt_path,
            output_format=self.output_format or config.default_output_format,
            input_format=self.input_format,
            verbose=self.verbose or config.verbose,
            cwd=self.cwd or config.default_cwd,
            session_id=self.session_id,
            continue_session=self.continue_session,
            allowed_tools=self.allowed_tools or config.default_allowed_tools,
            permission_mode=self.permission_mode
            or config.default_permission_mode,
            include_rules=self.include_rules or config.include_rules,
            pr=self.pr,
            is_sub_agent=self.is_sub_agent,
            async_mode=self.async_mode,
            split_mode=self.split_mode,
            delimiter=self.delimiter,
            min_level=self.min_level,
            max_level=self.max_level,
            workdir=self.workdir,
            from_branch=self.from_branch,
            bg_mode=self.bg_mode,
            task_prefix=self.task_prefix,
            worktree_name=self.worktree_name,
        )

        # 加载系统提示文件
        if config.system_prompt_path and not merged.system_prompt:
            try:
                with open(
                    config.system_prompt_path, "r", encoding="utf-8"
                ) as f:
                    merged.system_prompt = f.read().strip()
            except Exception as e:
                raise ValidationError(
                    f"无法读取系统提示文件 {config.system_prompt_path}: {e}"
                )

        return merged

    def validate(self) -> None:
        """验证选项有效性"""
        # 验证输出格式
        valid_formats = ["text", "json", "stream-json"]
        if self.output_format not in valid_formats:
            raise ValidationError(f"不支持的输出格式: {self.output_format}")

        # 验证输入格式
        if self.input_format not in valid_formats:
            raise ValidationError(f"不支持的输入格式: {self.input_format}")

        # 验证权限模式
        valid_permissions = ["manual", "acceptEdits"]
        if self.permission_mode not in valid_permissions:
            raise ValidationError(f"不支持的权限模式: {self.permission_mode}")

        # 验证工作目录
        if self.cwd and not os.path.exists(self.cwd):
            raise ValidationError(f"工作目录不存在: {self.cwd}")

        # 验证异步模式相关参数
        if self.async_mode:
            valid_split_modes = ["h1", "h2", "h3", "any", "delimiter"]
            if self.split_mode not in valid_split_modes:
                raise ValidationError(f"不支持的分割模式: {self.split_mode}")

            if self.split_mode == "any":
                if self.min_level < 1 or self.max_level < 1:
                    raise ValidationError("标题级别必须大于等于1")
                if self.min_level > self.max_level:
                    raise ValidationError("最小级别不能大于最大级别")

            if self.split_mode == "delimiter" and not self.delimiter.strip():
                raise ValidationError("分隔符模式需要提供分隔符")


@dataclass
class StreamEvent:
    """流式事件数据"""

    event_type: str  # start, content, tool_call, completion, error, end
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def is_content(self) -> bool:
        """是否为内容事件"""
        return self.event_type in ["content", "completion"]

    @property
    def content(self) -> str:
        """获取事件内容"""
        if self.event_type == "content":
            return self.data.get("content", "")
        elif self.event_type == "completion":
            return self.data.get("result", "")
        elif self.event_type == "tool_call":
            # 特殊处理工具调用事件
            tool_name = self.data.get("tool_name", "")
            if tool_name == "AttemptCompletionTool":
                return self.data.get("args", {}).get("result", "")
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": (
                self.timestamp.isoformat() if self.timestamp else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEvent":
        """从字典创建实例"""
        timestamp = None
        if data.get("timestamp"):
            timestamp = datetime.fromisoformat(data["timestamp"])

        return cls(
            event_type=data["event_type"],
            data=data["data"],
            timestamp=timestamp,
        )


@dataclass
class QueryResult:
    """查询结果"""

    success: bool
    content: str
    error: Optional[str] = None
    session_id: Optional[str] = None
    events: List[StreamEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.success

    @property
    def has_error(self) -> bool:
        """是否有错误"""
        return not self.success or self.error is not None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "session_id": self.session_id,
            "events": [event.to_dict() for event in self.events],
            "metadata": self.metadata,
            "execution_time": self.execution_time,
        }

    @classmethod
    def success_result(
        cls,
        content: str,
        session_id: Optional[str] = None,
        events: Optional[List[StreamEvent]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
    ) -> "QueryResult":
        """创建成功结果"""
        return cls(
            success=True,
            content=content,
            session_id=session_id,
            events=events or [],
            metadata=metadata or {},
            execution_time=execution_time,
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        content: str = "",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "QueryResult":
        """创建错误结果"""
        return cls(
            success=False,
            content=content,
            error=error,
            session_id=session_id,
            metadata=metadata or {},
        )


@dataclass
class ConfigResult:
    """配置命令结果"""

    success: bool
    message: str
    error: Optional[str] = None
    applied_configs: List[str] = field(default_factory=list)

    @classmethod
    def success_result(
        cls, message: str, applied_configs: Optional[List[str]] = None
    ) -> "ConfigResult":
        """创建成功结果"""
        return cls(
            success=True,
            message=message,
            applied_configs=applied_configs or [],
        )

    @classmethod
    def error_result(cls, error: str) -> "ConfigResult":
        """创建错误结果"""
        return cls(success=False, message="", error=error)


@dataclass
class SessionInfo:
    """会话信息"""

    session_id: str
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    message_count: int = 0
    status: str = "active"  # active, archived, deleted
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "message_count": self.message_count,
            "status": self.status,
            "metadata": self.metadata,
        }
