import datetime

from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CheckpointType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CHECKPOINT_TYPE_UNSPECIFIED: _ClassVar[CheckpointType]
    CHECKPOINT_TYPE_MANUAL: _ClassVar[CheckpointType]
    CHECKPOINT_TYPE_AUTO: _ClassVar[CheckpointType]
    CHECKPOINT_TYPE_PRE_TERMINATE: _ClassVar[CheckpointType]
    CHECKPOINT_TYPE_ERROR: _ClassVar[CheckpointType]
    CHECKPOINT_TYPE_MILESTONE: _ClassVar[CheckpointType]

class ContextScope(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTEXT_SCOPE_UNSPECIFIED: _ClassVar[ContextScope]
    CONTEXT_SCOPE_EXECUTION: _ClassVar[ContextScope]
    CONTEXT_SCOPE_WORKFLOW: _ClassVar[ContextScope]
    CONTEXT_SCOPE_TENANT: _ClassVar[ContextScope]

class MergeStrategy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MERGE_STRATEGY_UNSPECIFIED: _ClassVar[MergeStrategy]
    MERGE_STRATEGY_LAST_WRITE_WINS: _ClassVar[MergeStrategy]
    MERGE_STRATEGY_FAIL_ON_CONFLICT: _ClassVar[MergeStrategy]
    MERGE_STRATEGY_MERGE_RECURSIVE: _ClassVar[MergeStrategy]
    MERGE_STRATEGY_CUSTOM: _ClassVar[MergeStrategy]
CHECKPOINT_TYPE_UNSPECIFIED: CheckpointType
CHECKPOINT_TYPE_MANUAL: CheckpointType
CHECKPOINT_TYPE_AUTO: CheckpointType
CHECKPOINT_TYPE_PRE_TERMINATE: CheckpointType
CHECKPOINT_TYPE_ERROR: CheckpointType
CHECKPOINT_TYPE_MILESTONE: CheckpointType
CONTEXT_SCOPE_UNSPECIFIED: ContextScope
CONTEXT_SCOPE_EXECUTION: ContextScope
CONTEXT_SCOPE_WORKFLOW: ContextScope
CONTEXT_SCOPE_TENANT: ContextScope
MERGE_STRATEGY_UNSPECIFIED: MergeStrategy
MERGE_STRATEGY_LAST_WRITE_WINS: MergeStrategy
MERGE_STRATEGY_FAIL_ON_CONFLICT: MergeStrategy
MERGE_STRATEGY_MERGE_RECURSIVE: MergeStrategy
MERGE_STRATEGY_CUSTOM: MergeStrategy

class Checkpoint(_message.Message):
    __slots__ = ("checkpoint_id", "envelope_id", "execution_id", "tenant_id", "version", "parent_version", "metadata", "data", "created_at", "expires_at", "size_bytes", "save_duration_ms")
    CHECKPOINT_ID_FIELD_NUMBER: _ClassVar[int]
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PARENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    SAVE_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    checkpoint_id: str
    envelope_id: str
    execution_id: str
    tenant_id: str
    version: int
    parent_version: str
    metadata: CheckpointMetadata
    data: _struct_pb2.Struct
    created_at: _timestamp_pb2.Timestamp
    expires_at: _timestamp_pb2.Timestamp
    size_bytes: int
    save_duration_ms: int
    def __init__(self, checkpoint_id: _Optional[str] = ..., envelope_id: _Optional[str] = ..., execution_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., version: _Optional[int] = ..., parent_version: _Optional[str] = ..., metadata: _Optional[_Union[CheckpointMetadata, _Mapping]] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., size_bytes: _Optional[int] = ..., save_duration_ms: _Optional[int] = ...) -> None: ...

class CheckpointMetadata(_message.Message):
    __slots__ = ("type", "framework_type", "framework_version", "execution_status", "step_count", "current_node", "cost_snapshot_usd", "tokens_consumed", "tags", "description", "compressed", "compression_algorithm")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FRAMEWORK_TYPE_FIELD_NUMBER: _ClassVar[int]
    FRAMEWORK_VERSION_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_STATUS_FIELD_NUMBER: _ClassVar[int]
    STEP_COUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENT_NODE_FIELD_NUMBER: _ClassVar[int]
    COST_SNAPSHOT_USD_FIELD_NUMBER: _ClassVar[int]
    TOKENS_CONSUMED_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    COMPRESSED_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    type: CheckpointType
    framework_type: str
    framework_version: str
    execution_status: str
    step_count: int
    current_node: str
    cost_snapshot_usd: float
    tokens_consumed: int
    tags: _containers.ScalarMap[str, str]
    description: str
    compressed: bool
    compression_algorithm: str
    def __init__(self, type: _Optional[_Union[CheckpointType, str]] = ..., framework_type: _Optional[str] = ..., framework_version: _Optional[str] = ..., execution_status: _Optional[str] = ..., step_count: _Optional[int] = ..., current_node: _Optional[str] = ..., cost_snapshot_usd: _Optional[float] = ..., tokens_consumed: _Optional[int] = ..., tags: _Optional[_Mapping[str, str]] = ..., description: _Optional[str] = ..., compressed: bool = ..., compression_algorithm: _Optional[str] = ...) -> None: ...

class CheckpointVersion(_message.Message):
    __slots__ = ("checkpoint_id", "version", "parent_version", "created_at", "metadata", "size_bytes")
    CHECKPOINT_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PARENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    checkpoint_id: str
    version: int
    parent_version: str
    created_at: _timestamp_pb2.Timestamp
    metadata: CheckpointMetadata
    size_bytes: int
    def __init__(self, checkpoint_id: _Optional[str] = ..., version: _Optional[int] = ..., parent_version: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., metadata: _Optional[_Union[CheckpointMetadata, _Mapping]] = ..., size_bytes: _Optional[int] = ...) -> None: ...

class SaveCheckpointRequest(_message.Message):
    __slots__ = ("checkpoint", "auto_version", "max_versions")
    CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    AUTO_VERSION_FIELD_NUMBER: _ClassVar[int]
    MAX_VERSIONS_FIELD_NUMBER: _ClassVar[int]
    checkpoint: Checkpoint
    auto_version: bool
    max_versions: int
    def __init__(self, checkpoint: _Optional[_Union[Checkpoint, _Mapping]] = ..., auto_version: bool = ..., max_versions: _Optional[int] = ...) -> None: ...

class SaveCheckpointResponse(_message.Message):
    __slots__ = ("checkpoint_id", "version", "created_at")
    CHECKPOINT_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    checkpoint_id: str
    version: int
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, checkpoint_id: _Optional[str] = ..., version: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetCheckpointRequest(_message.Message):
    __slots__ = ("checkpoint_id", "version")
    CHECKPOINT_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    checkpoint_id: str
    version: int
    def __init__(self, checkpoint_id: _Optional[str] = ..., version: _Optional[int] = ...) -> None: ...

class GetCheckpointResponse(_message.Message):
    __slots__ = ("checkpoint",)
    CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    checkpoint: Checkpoint
    def __init__(self, checkpoint: _Optional[_Union[Checkpoint, _Mapping]] = ...) -> None: ...

class ListCheckpointsRequest(_message.Message):
    __slots__ = ("tenant_id", "envelope_id", "execution_id", "page_size", "page_token", "order_by")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ORDER_BY_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    envelope_id: str
    execution_id: str
    page_size: int
    page_token: str
    order_by: str
    def __init__(self, tenant_id: _Optional[str] = ..., envelope_id: _Optional[str] = ..., execution_id: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ..., order_by: _Optional[str] = ...) -> None: ...

class ListCheckpointsResponse(_message.Message):
    __slots__ = ("checkpoints", "next_page_token", "total_count")
    CHECKPOINTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    checkpoints: _containers.RepeatedCompositeFieldContainer[Checkpoint]
    next_page_token: str
    total_count: int
    def __init__(self, checkpoints: _Optional[_Iterable[_Union[Checkpoint, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class DeleteCheckpointRequest(_message.Message):
    __slots__ = ("checkpoint_id", "soft_delete", "delete_all_versions")
    CHECKPOINT_ID_FIELD_NUMBER: _ClassVar[int]
    SOFT_DELETE_FIELD_NUMBER: _ClassVar[int]
    DELETE_ALL_VERSIONS_FIELD_NUMBER: _ClassVar[int]
    checkpoint_id: str
    soft_delete: bool
    delete_all_versions: bool
    def __init__(self, checkpoint_id: _Optional[str] = ..., soft_delete: bool = ..., delete_all_versions: bool = ...) -> None: ...

class DeleteCheckpointResponse(_message.Message):
    __slots__ = ("success", "versions_deleted")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    VERSIONS_DELETED_FIELD_NUMBER: _ClassVar[int]
    success: bool
    versions_deleted: int
    def __init__(self, success: bool = ..., versions_deleted: _Optional[int] = ...) -> None: ...

class ListCheckpointVersionsRequest(_message.Message):
    __slots__ = ("execution_id", "page_size", "page_token")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    page_size: int
    page_token: str
    def __init__(self, execution_id: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListCheckpointVersionsResponse(_message.Message):
    __slots__ = ("versions", "next_page_token", "total_count")
    VERSIONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    versions: _containers.RepeatedCompositeFieldContainer[CheckpointVersion]
    next_page_token: str
    total_count: int
    def __init__(self, versions: _Optional[_Iterable[_Union[CheckpointVersion, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class GetCheckpointVersionRequest(_message.Message):
    __slots__ = ("execution_id", "version")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    version: int
    def __init__(self, execution_id: _Optional[str] = ..., version: _Optional[int] = ...) -> None: ...

class GetCheckpointVersionResponse(_message.Message):
    __slots__ = ("checkpoint",)
    CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    checkpoint: Checkpoint
    def __init__(self, checkpoint: _Optional[_Union[Checkpoint, _Mapping]] = ...) -> None: ...

class QueryCheckpointsRequest(_message.Message):
    __slots__ = ("query", "page_size", "page_token", "order_by")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ORDER_BY_FIELD_NUMBER: _ClassVar[int]
    query: CheckpointQuery
    page_size: int
    page_token: str
    order_by: str
    def __init__(self, query: _Optional[_Union[CheckpointQuery, _Mapping]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ..., order_by: _Optional[str] = ...) -> None: ...

class QueryCheckpointsResponse(_message.Message):
    __slots__ = ("checkpoints", "next_page_token", "total_count")
    CHECKPOINTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    checkpoints: _containers.RepeatedCompositeFieldContainer[Checkpoint]
    next_page_token: str
    total_count: int
    def __init__(self, checkpoints: _Optional[_Iterable[_Union[Checkpoint, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class CheckpointQuery(_message.Message):
    __slots__ = ("tenant_ids", "envelope_ids", "execution_ids", "types", "created_after", "created_before", "framework_types", "tags", "min_cost_usd", "max_cost_usd", "min_size_bytes", "max_size_bytes")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TENANT_IDS_FIELD_NUMBER: _ClassVar[int]
    ENVELOPE_IDS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_IDS_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    CREATED_AFTER_FIELD_NUMBER: _ClassVar[int]
    CREATED_BEFORE_FIELD_NUMBER: _ClassVar[int]
    FRAMEWORK_TYPES_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    MIN_COST_USD_FIELD_NUMBER: _ClassVar[int]
    MAX_COST_USD_FIELD_NUMBER: _ClassVar[int]
    MIN_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    MAX_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    tenant_ids: _containers.RepeatedScalarFieldContainer[str]
    envelope_ids: _containers.RepeatedScalarFieldContainer[str]
    execution_ids: _containers.RepeatedScalarFieldContainer[str]
    types: _containers.RepeatedScalarFieldContainer[CheckpointType]
    created_after: _timestamp_pb2.Timestamp
    created_before: _timestamp_pb2.Timestamp
    framework_types: _containers.RepeatedScalarFieldContainer[str]
    tags: _containers.ScalarMap[str, str]
    min_cost_usd: float
    max_cost_usd: float
    min_size_bytes: int
    max_size_bytes: int
    def __init__(self, tenant_ids: _Optional[_Iterable[str]] = ..., envelope_ids: _Optional[_Iterable[str]] = ..., execution_ids: _Optional[_Iterable[str]] = ..., types: _Optional[_Iterable[_Union[CheckpointType, str]]] = ..., created_after: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., created_before: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., framework_types: _Optional[_Iterable[str]] = ..., tags: _Optional[_Mapping[str, str]] = ..., min_cost_usd: _Optional[float] = ..., max_cost_usd: _Optional[float] = ..., min_size_bytes: _Optional[int] = ..., max_size_bytes: _Optional[int] = ...) -> None: ...

class ExecutionContext(_message.Message):
    __slots__ = ("execution_id", "tenant_id", "workflow_id", "scope", "data", "parent_execution_id", "inherited_keys", "version", "updated_at")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    PARENT_EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    INHERITED_KEYS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    tenant_id: str
    workflow_id: str
    scope: ContextScope
    data: _struct_pb2.Struct
    parent_execution_id: str
    inherited_keys: _containers.RepeatedScalarFieldContainer[str]
    version: int
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, execution_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., scope: _Optional[_Union[ContextScope, str]] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., parent_execution_id: _Optional[str] = ..., inherited_keys: _Optional[_Iterable[str]] = ..., version: _Optional[int] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetExecutionContextRequest(_message.Message):
    __slots__ = ("execution_id", "keys", "include_inherited")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_INHERITED_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    keys: _containers.RepeatedScalarFieldContainer[str]
    include_inherited: bool
    def __init__(self, execution_id: _Optional[str] = ..., keys: _Optional[_Iterable[str]] = ..., include_inherited: bool = ...) -> None: ...

class GetExecutionContextResponse(_message.Message):
    __slots__ = ("context",)
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    context: ExecutionContext
    def __init__(self, context: _Optional[_Union[ExecutionContext, _Mapping]] = ...) -> None: ...

class UpdateExecutionContextRequest(_message.Message):
    __slots__ = ("execution_id", "updates", "delete_keys", "expected_version", "merge_strategy")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    DELETE_KEYS_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VERSION_FIELD_NUMBER: _ClassVar[int]
    MERGE_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    updates: _struct_pb2.Struct
    delete_keys: _containers.RepeatedScalarFieldContainer[str]
    expected_version: int
    merge_strategy: MergeStrategy
    def __init__(self, execution_id: _Optional[str] = ..., updates: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., delete_keys: _Optional[_Iterable[str]] = ..., expected_version: _Optional[int] = ..., merge_strategy: _Optional[_Union[MergeStrategy, str]] = ...) -> None: ...

class UpdateExecutionContextResponse(_message.Message):
    __slots__ = ("context", "conflict_detected", "conflict_resolution")
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    CONFLICT_DETECTED_FIELD_NUMBER: _ClassVar[int]
    CONFLICT_RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    context: ExecutionContext
    conflict_detected: bool
    conflict_resolution: str
    def __init__(self, context: _Optional[_Union[ExecutionContext, _Mapping]] = ..., conflict_detected: bool = ..., conflict_resolution: _Optional[str] = ...) -> None: ...
