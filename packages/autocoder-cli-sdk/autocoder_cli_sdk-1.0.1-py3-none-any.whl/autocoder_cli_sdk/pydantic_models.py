"""
AutoCoder CLI SDK Pydantic 响应模型

定义用于JSON输出格式的Pydantic模型，提供类型安全的响应处理。
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class StreamEventData(BaseModel):
    """流式事件数据模型"""

    class Config:
        extra = "allow"


class StreamEventModel(BaseModel):
    """流式事件Pydantic模型"""

    event_type: str = Field(..., description="事件类型")
    data: StreamEventData = Field(..., description="事件数据")
    timestamp: Optional[datetime] = Field(None, description="事件时间戳")
    session_id: Optional[str] = Field(None, description="会话ID")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class ToolCallArgs(BaseModel):
    """工具调用参数模型"""

    result: Optional[str] = Field(None, description="工具执行结果")

    class Config:
        extra = "allow"


class ToolCallData(BaseModel):
    """工具调用数据模型"""

    tool_name: str = Field(..., description="工具名称")
    args: Union[ToolCallArgs, Dict[str, Any]] = Field(
        ..., description="工具参数"
    )

    class Config:
        extra = "allow"


class CompletionEventModel(BaseModel):
    """完成事件模型"""

    event_type: str = Field("completion", description="事件类型")
    data: Dict[str, Any] = Field(..., description="完成数据")
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    session_id: Optional[str] = None

    @property
    def result(self) -> str:
        """获取完成结果"""
        return self.data.get("result", "")


class ContentEventModel(BaseModel):
    """内容事件模型"""

    event_type: str = Field("content", description="事件类型")
    data: Dict[str, str] = Field(..., description="内容数据")
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    session_id: Optional[str] = None

    @property
    def content(self) -> str:
        """获取内容"""
        return self.data.get("content", "")


class ErrorEventModel(BaseModel):
    """错误事件模型"""

    event_type: str = Field("error", description="事件类型")
    data: Dict[str, str] = Field(..., description="错误数据")
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    session_id: Optional[str] = None

    @property
    def error_message(self) -> str:
        """获取错误消息"""
        return self.data.get("error", "")


class StartEventModel(BaseModel):
    """开始事件模型"""

    event_type: str = Field("start", description="事件类型")
    data: Dict[str, str] = Field(default_factory=lambda: {"status": "started"})
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    session_id: Optional[str] = None


class EndEventModel(BaseModel):
    """结束事件模型"""

    event_type: str = Field("end", description="事件类型")
    data: Dict[str, str] = Field(
        default_factory=lambda: {"status": "completed"}
    )
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    session_id: Optional[str] = None


class QuerySummaryModel(BaseModel):
    """查询摘要模型"""

    total_events: int = Field(0, description="总事件数")
    start_events: int = Field(0, description="开始事件数")
    completion_events: int = Field(0, description="完成事件数")
    error_events: int = Field(0, description="错误事件数")
    content_events: int = Field(0, description="内容事件数")
    tool_call_events: int = Field(0, description="工具调用事件数")


class QueryResponseModel(BaseModel):
    """查询响应模型（用于JSON输出格式）"""

    events: List[StreamEventModel] = Field(
        default_factory=list, description="事件列表"
    )
    summary: QuerySummaryModel = Field(
        default_factory=QuerySummaryModel, description="事件摘要"
    )
    session_id: Optional[str] = Field(None, description="会话ID")
    execution_time: Optional[float] = Field(None, description="执行时间")

    @property
    def final_result(self) -> str:
        """获取最终结果（从completion事件中提取）"""
        for event in reversed(self.events):  # 从后往前查找最后的completion事件
            if event.event_type == "completion":
                return event.data.dict().get("result", "")
            elif (
                event.event_type == "tool_call"
                and isinstance(event.data.dict(), dict)
                and event.data.dict().get("tool_name")
                == "AttemptCompletionTool"
            ):
                args = event.data.dict().get("args", {})
                if isinstance(args, dict):
                    return args.get("result", "")
        return ""

    @property
    def all_content(self) -> str:
        """获取所有内容事件的内容拼接"""
        content_parts = []
        for event in self.events:
            if event.event_type == "content":
                content = event.data.dict().get("content", "")
                if content:
                    content_parts.append(content)
        return "".join(content_parts)

    @property
    def has_errors(self) -> bool:
        """检查是否有错误事件"""
        return any(event.event_type == "error" for event in self.events)

    @property
    def error_messages(self) -> List[str]:
        """获取所有错误消息"""
        errors = []
        for event in self.events:
            if event.event_type == "error":
                error_msg = event.data.dict().get("error", "")
                if error_msg:
                    errors.append(error_msg)
        return errors


class ConfigResponseModel(BaseModel):
    """配置响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field("", description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")
    applied_configs: List[str] = Field(
        default_factory=list, description="已应用的配置"
    )

    @classmethod
    def success_response(
        cls, message: str, applied_configs: Optional[List[str]] = None
    ):
        """创建成功响应"""
        return cls(
            success=True,
            message=message,
            applied_configs=applied_configs or [],
        )

    @classmethod
    def error_response(cls, error: str):
        """创建错误响应"""
        return cls(success=False, error=error)


class VersionResponseModel(BaseModel):
    """版本响应模型"""

    version: str = Field(..., description="版本号")
    sdk_version: str = Field("1.0.0", description="SDK版本")

    @property
    def is_unknown(self) -> bool:
        """是否为未知版本"""
        return self.version == "unknown"


def parse_event_from_dict(data: Dict[str, Any]) -> StreamEventModel:
    """从字典解析事件模型"""
    try:
        return StreamEventModel(**data)
    except Exception:
        # 如果解析失败，创建一个通用的事件模型
        return StreamEventModel(
            event_type=data.get("event_type", "unknown"),
            data=StreamEventData(**data.get("data", {})),
            timestamp=datetime.now() if not data.get("timestamp") else None,
            session_id=data.get("session_id"),
        )


def parse_json_response(json_str: str) -> QueryResponseModel:
    """解析JSON响应字符串为模型"""
    try:
        data = json.loads(json_str)

        # 处理事件列表
        events = []
        if "events" in data and isinstance(data["events"], list):
            for event_data in data["events"]:
                events.append(parse_event_from_dict(event_data))

        # 处理摘要
        summary_data = data.get("summary", {})
        summary = (
            QuerySummaryModel(**summary_data)
            if summary_data
            else QuerySummaryModel()
        )

        return QueryResponseModel(
            events=events,
            summary=summary,
            session_id=data.get("session_id"),
            execution_time=data.get("execution_time"),
        )

    except json.JSONDecodeError as e:
        # JSON解析失败，创建错误事件
        error_event = StreamEventModel(
            event_type="error",
            data=StreamEventData(error=f"JSON解析失败: {str(e)}"),
            timestamp=datetime.now(),
        )
        return QueryResponseModel(
            events=[error_event],
            summary=QuerySummaryModel(total_events=1, error_events=1),
        )
    except Exception as e:
        # 其他异常
        error_event = StreamEventModel(
            event_type="error",
            data=StreamEventData(error=f"响应解析失败: {str(e)}"),
            timestamp=datetime.now(),
        )
        return QueryResponseModel(
            events=[error_event],
            summary=QuerySummaryModel(total_events=1, error_events=1),
        )
