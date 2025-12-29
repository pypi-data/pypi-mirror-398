from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecutionRequest(_message.Message):
    __slots__ = ("envelope_id", "state_graph", "config", "enable_callbacks", "initial_state")
    class ConfigEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_GRAPH_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    ENABLE_CALLBACKS_FIELD_NUMBER: _ClassVar[int]
    INITIAL_STATE_FIELD_NUMBER: _ClassVar[int]
    envelope_id: str
    state_graph: bytes
    config: _containers.ScalarMap[str, str]
    enable_callbacks: bool
    initial_state: bytes
    def __init__(self, envelope_id: _Optional[str] = ..., state_graph: _Optional[bytes] = ..., config: _Optional[_Mapping[str, str]] = ..., enable_callbacks: bool = ..., initial_state: _Optional[bytes] = ...) -> None: ...

class ExecutionResponse(_message.Message):
    __slots__ = ("execution_id", "pid", "version")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    pid: int
    version: str
    def __init__(self, execution_id: _Optional[str] = ..., pid: _Optional[int] = ..., version: _Optional[str] = ...) -> None: ...

class CallbackEvent(_message.Message):
    __slots__ = ("envelope_id", "timestamp_ns", "llm_start", "llm_end", "llm_error", "tool_start", "tool_end", "tool_error", "chain_start", "chain_end", "streaming_chunk", "error", "complete")
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    LLM_START_FIELD_NUMBER: _ClassVar[int]
    LLM_END_FIELD_NUMBER: _ClassVar[int]
    LLM_ERROR_FIELD_NUMBER: _ClassVar[int]
    TOOL_START_FIELD_NUMBER: _ClassVar[int]
    TOOL_END_FIELD_NUMBER: _ClassVar[int]
    TOOL_ERROR_FIELD_NUMBER: _ClassVar[int]
    CHAIN_START_FIELD_NUMBER: _ClassVar[int]
    CHAIN_END_FIELD_NUMBER: _ClassVar[int]
    STREAMING_CHUNK_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    COMPLETE_FIELD_NUMBER: _ClassVar[int]
    envelope_id: str
    timestamp_ns: int
    llm_start: LLMStartEvent
    llm_end: LLMEndEvent
    llm_error: LLMErrorEvent
    tool_start: ToolStartEvent
    tool_end: ToolEndEvent
    tool_error: ToolErrorEvent
    chain_start: ChainStartEvent
    chain_end: ChainEndEvent
    streaming_chunk: StreamingChunkEvent
    error: ErrorEvent
    complete: CompleteEvent
    def __init__(self, envelope_id: _Optional[str] = ..., timestamp_ns: _Optional[int] = ..., llm_start: _Optional[_Union[LLMStartEvent, _Mapping]] = ..., llm_end: _Optional[_Union[LLMEndEvent, _Mapping]] = ..., llm_error: _Optional[_Union[LLMErrorEvent, _Mapping]] = ..., tool_start: _Optional[_Union[ToolStartEvent, _Mapping]] = ..., tool_end: _Optional[_Union[ToolEndEvent, _Mapping]] = ..., tool_error: _Optional[_Union[ToolErrorEvent, _Mapping]] = ..., chain_start: _Optional[_Union[ChainStartEvent, _Mapping]] = ..., chain_end: _Optional[_Union[ChainEndEvent, _Mapping]] = ..., streaming_chunk: _Optional[_Union[StreamingChunkEvent, _Mapping]] = ..., error: _Optional[_Union[ErrorEvent, _Mapping]] = ..., complete: _Optional[_Union[CompleteEvent, _Mapping]] = ...) -> None: ...

class LLMStartEvent(_message.Message):
    __slots__ = ("model_id", "prompt_preview", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    PROMPT_PREVIEW_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    prompt_preview: str
    parameters: _containers.ScalarMap[str, str]
    def __init__(self, model_id: _Optional[str] = ..., prompt_preview: _Optional[str] = ..., parameters: _Optional[_Mapping[str, str]] = ...) -> None: ...

class LLMEndEvent(_message.Message):
    __slots__ = ("model_id", "input_tokens", "output_tokens", "latency_ms", "cost_usd", "completion_preview")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    INPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    COST_USD_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_PREVIEW_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float
    completion_preview: str
    def __init__(self, model_id: _Optional[str] = ..., input_tokens: _Optional[int] = ..., output_tokens: _Optional[int] = ..., latency_ms: _Optional[int] = ..., cost_usd: _Optional[float] = ..., completion_preview: _Optional[str] = ...) -> None: ...

class LLMErrorEvent(_message.Message):
    __slots__ = ("model_id", "error_message", "error_type", "recoverable")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_TYPE_FIELD_NUMBER: _ClassVar[int]
    RECOVERABLE_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    error_message: str
    error_type: str
    recoverable: bool
    def __init__(self, model_id: _Optional[str] = ..., error_message: _Optional[str] = ..., error_type: _Optional[str] = ..., recoverable: bool = ...) -> None: ...

class ToolStartEvent(_message.Message):
    __slots__ = ("tool_name", "input_data", "tool_call_id")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_DATA_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALL_ID_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    input_data: bytes
    tool_call_id: str
    def __init__(self, tool_name: _Optional[str] = ..., input_data: _Optional[bytes] = ..., tool_call_id: _Optional[str] = ...) -> None: ...

class ToolEndEvent(_message.Message):
    __slots__ = ("tool_name", "output_data", "tool_call_id", "latency_ms")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_DATA_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALL_ID_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    output_data: bytes
    tool_call_id: str
    latency_ms: int
    def __init__(self, tool_name: _Optional[str] = ..., output_data: _Optional[bytes] = ..., tool_call_id: _Optional[str] = ..., latency_ms: _Optional[int] = ...) -> None: ...

class ToolErrorEvent(_message.Message):
    __slots__ = ("tool_name", "tool_call_id", "error_message", "recoverable")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALL_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECOVERABLE_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    tool_call_id: str
    error_message: str
    recoverable: bool
    def __init__(self, tool_name: _Optional[str] = ..., tool_call_id: _Optional[str] = ..., error_message: _Optional[str] = ..., recoverable: bool = ...) -> None: ...

class ChainStartEvent(_message.Message):
    __slots__ = ("node_name", "node_id", "input_state")
    NODE_NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    INPUT_STATE_FIELD_NUMBER: _ClassVar[int]
    node_name: str
    node_id: str
    input_state: bytes
    def __init__(self, node_name: _Optional[str] = ..., node_id: _Optional[str] = ..., input_state: _Optional[bytes] = ...) -> None: ...

class ChainEndEvent(_message.Message):
    __slots__ = ("node_name", "node_id", "output_state")
    NODE_NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_STATE_FIELD_NUMBER: _ClassVar[int]
    node_name: str
    node_id: str
    output_state: bytes
    def __init__(self, node_name: _Optional[str] = ..., node_id: _Optional[str] = ..., output_state: _Optional[bytes] = ...) -> None: ...

class StreamingChunkEvent(_message.Message):
    __slots__ = ("model_id", "chunk", "chunk_index", "is_final")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    CHUNK_INDEX_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    chunk: str
    chunk_index: int
    is_final: bool
    def __init__(self, model_id: _Optional[str] = ..., chunk: _Optional[str] = ..., chunk_index: _Optional[int] = ..., is_final: bool = ...) -> None: ...

class ErrorEvent(_message.Message):
    __slots__ = ("message", "stack_trace", "error_type", "recoverable", "exit_code")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STACK_TRACE_FIELD_NUMBER: _ClassVar[int]
    ERROR_TYPE_FIELD_NUMBER: _ClassVar[int]
    RECOVERABLE_FIELD_NUMBER: _ClassVar[int]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    message: str
    stack_trace: str
    error_type: str
    recoverable: bool
    exit_code: int
    def __init__(self, message: _Optional[str] = ..., stack_trace: _Optional[str] = ..., error_type: _Optional[str] = ..., recoverable: bool = ..., exit_code: _Optional[int] = ...) -> None: ...

class CompleteEvent(_message.Message):
    __slots__ = ("result", "checkpoint", "total_time_ms", "final_state")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    FINAL_STATE_FIELD_NUMBER: _ClassVar[int]
    result: bytes
    checkpoint: bytes
    total_time_ms: int
    final_state: bytes
    def __init__(self, result: _Optional[bytes] = ..., checkpoint: _Optional[bytes] = ..., total_time_ms: _Optional[int] = ..., final_state: _Optional[bytes] = ...) -> None: ...

class TerminateRequest(_message.Message):
    __slots__ = ("envelope_id", "reason", "force", "timeout_ms")
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    envelope_id: str
    reason: str
    force: bool
    timeout_ms: int
    def __init__(self, envelope_id: _Optional[str] = ..., reason: _Optional[str] = ..., force: bool = ..., timeout_ms: _Optional[int] = ...) -> None: ...

class TerminateResponse(_message.Message):
    __slots__ = ("success", "message", "final_state")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FINAL_STATE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    final_state: bytes
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., final_state: _Optional[bytes] = ...) -> None: ...

class CheckpointRequest(_message.Message):
    __slots__ = ("envelope_id", "include_state")
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_STATE_FIELD_NUMBER: _ClassVar[int]
    envelope_id: str
    include_state: bool
    def __init__(self, envelope_id: _Optional[str] = ..., include_state: bool = ...) -> None: ...

class CheckpointResponse(_message.Message):
    __slots__ = ("checkpoint", "state_hash", "cost", "state")
    CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    STATE_HASH_FIELD_NUMBER: _ClassVar[int]
    COST_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    checkpoint: bytes
    state_hash: str
    cost: CostSnapshot
    state: bytes
    def __init__(self, checkpoint: _Optional[bytes] = ..., state_hash: _Optional[str] = ..., cost: _Optional[_Union[CostSnapshot, _Mapping]] = ..., state: _Optional[bytes] = ...) -> None: ...

class CostSnapshot(_message.Message):
    __slots__ = ("total_input_tokens", "total_output_tokens", "total_cost_usd", "llm_call_count", "tool_call_count")
    TOTAL_INPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_OUTPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COST_USD_FIELD_NUMBER: _ClassVar[int]
    LLM_CALL_COUNT_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALL_COUNT_FIELD_NUMBER: _ClassVar[int]
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    llm_call_count: int
    tool_call_count: int
    def __init__(self, total_input_tokens: _Optional[int] = ..., total_output_tokens: _Optional[int] = ..., total_cost_usd: _Optional[float] = ..., llm_call_count: _Optional[int] = ..., tool_call_count: _Optional[int] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ("pid",)
    PID_FIELD_NUMBER: _ClassVar[int]
    pid: int
    def __init__(self, pid: _Optional[int] = ...) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("healthy", "pid", "uptime_seconds", "memory_bytes")
    HEALTHY_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    MEMORY_BYTES_FIELD_NUMBER: _ClassVar[int]
    healthy: bool
    pid: int
    uptime_seconds: int
    memory_bytes: int
    def __init__(self, healthy: bool = ..., pid: _Optional[int] = ..., uptime_seconds: _Optional[int] = ..., memory_bytes: _Optional[int] = ...) -> None: ...
