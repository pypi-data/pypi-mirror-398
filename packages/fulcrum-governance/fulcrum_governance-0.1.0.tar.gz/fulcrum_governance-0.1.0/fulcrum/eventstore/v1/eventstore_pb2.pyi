import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StoredEvent(_message.Message):
    __slots__ = ("event_id", "execution_id", "envelope_id", "tenant_id", "workflow_id", "event_type", "timestamp", "sequence_number", "payload", "trace_id", "span_id", "labels", "stream_name", "stream_sequence", "stored_at")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    SPAN_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
    STREAM_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    STORED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    execution_id: str
    envelope_id: str
    tenant_id: str
    workflow_id: str
    event_type: str
    timestamp: _timestamp_pb2.Timestamp
    sequence_number: int
    payload: _struct_pb2.Struct
    trace_id: str
    span_id: str
    labels: _containers.ScalarMap[str, str]
    stream_name: str
    stream_sequence: int
    stored_at: _timestamp_pb2.Timestamp
    def __init__(self, event_id: _Optional[str] = ..., execution_id: _Optional[str] = ..., envelope_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., event_type: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., sequence_number: _Optional[int] = ..., payload: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., trace_id: _Optional[str] = ..., span_id: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., stream_name: _Optional[str] = ..., stream_sequence: _Optional[int] = ..., stored_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PublishEventRequest(_message.Message):
    __slots__ = ("event",)
    EVENT_FIELD_NUMBER: _ClassVar[int]
    event: EventPayload
    def __init__(self, event: _Optional[_Union[EventPayload, _Mapping]] = ...) -> None: ...

class PublishEventResponse(_message.Message):
    __slots__ = ("event_id", "stream_sequence", "stored_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    STREAM_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    STORED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    stream_sequence: int
    stored_at: _timestamp_pb2.Timestamp
    def __init__(self, event_id: _Optional[str] = ..., stream_sequence: _Optional[int] = ..., stored_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PublishEventBatchRequest(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[EventPayload]
    def __init__(self, events: _Optional[_Iterable[_Union[EventPayload, _Mapping]]] = ...) -> None: ...

class PublishEventBatchResponse(_message.Message):
    __slots__ = ("published_count", "event_ids", "first_sequence", "last_sequence")
    PUBLISHED_COUNT_FIELD_NUMBER: _ClassVar[int]
    EVENT_IDS_FIELD_NUMBER: _ClassVar[int]
    FIRST_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    LAST_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    published_count: int
    event_ids: _containers.RepeatedScalarFieldContainer[str]
    first_sequence: int
    last_sequence: int
    def __init__(self, published_count: _Optional[int] = ..., event_ids: _Optional[_Iterable[str]] = ..., first_sequence: _Optional[int] = ..., last_sequence: _Optional[int] = ...) -> None: ...

class EventPayload(_message.Message):
    __slots__ = ("execution_id", "envelope_id", "tenant_id", "workflow_id", "event_type", "timestamp", "payload", "trace_id", "span_id", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    SPAN_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    envelope_id: str
    tenant_id: str
    workflow_id: str
    event_type: str
    timestamp: _timestamp_pb2.Timestamp
    payload: _struct_pb2.Struct
    trace_id: str
    span_id: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, execution_id: _Optional[str] = ..., envelope_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., event_type: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., payload: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., trace_id: _Optional[str] = ..., span_id: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class QueryEventsRequest(_message.Message):
    __slots__ = ("tenant_id", "execution_id", "workflow_id", "event_type", "start_time", "end_time", "labels", "limit", "page_token", "order")
    class OrderDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ORDER_DIRECTION_UNSPECIFIED: _ClassVar[QueryEventsRequest.OrderDirection]
        ASCENDING: _ClassVar[QueryEventsRequest.OrderDirection]
        DESCENDING: _ClassVar[QueryEventsRequest.OrderDirection]
    ORDER_DIRECTION_UNSPECIFIED: QueryEventsRequest.OrderDirection
    ASCENDING: QueryEventsRequest.OrderDirection
    DESCENDING: QueryEventsRequest.OrderDirection
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    execution_id: str
    workflow_id: str
    event_type: str
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    labels: _containers.ScalarMap[str, str]
    limit: int
    page_token: str
    order: QueryEventsRequest.OrderDirection
    def __init__(self, tenant_id: _Optional[str] = ..., execution_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., event_type: _Optional[str] = ..., start_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., labels: _Optional[_Mapping[str, str]] = ..., limit: _Optional[int] = ..., page_token: _Optional[str] = ..., order: _Optional[_Union[QueryEventsRequest.OrderDirection, str]] = ...) -> None: ...

class QueryEventsResponse(_message.Message):
    __slots__ = ("events", "next_page_token", "total_count")
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[StoredEvent]
    next_page_token: str
    total_count: int
    def __init__(self, events: _Optional[_Iterable[_Union[StoredEvent, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class GetExecutionEventsRequest(_message.Message):
    __slots__ = ("execution_id", "event_type", "start_time", "end_time", "limit", "page_token")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    event_type: str
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    limit: int
    page_token: str
    def __init__(self, execution_id: _Optional[str] = ..., event_type: _Optional[str] = ..., start_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., limit: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class GetExecutionEventsResponse(_message.Message):
    __slots__ = ("events", "next_page_token", "execution_started_at", "execution_ended_at", "total_event_count")
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_STARTED_AT_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ENDED_AT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_EVENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[StoredEvent]
    next_page_token: str
    execution_started_at: _timestamp_pb2.Timestamp
    execution_ended_at: _timestamp_pb2.Timestamp
    total_event_count: int
    def __init__(self, events: _Optional[_Iterable[_Union[StoredEvent, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., execution_started_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., execution_ended_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., total_event_count: _Optional[int] = ...) -> None: ...

class StreamEventsRequest(_message.Message):
    __slots__ = ("tenant_id", "execution_id", "workflow_id", "event_type", "start_sequence", "start_time", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    execution_id: str
    workflow_id: str
    event_type: str
    start_sequence: int
    start_time: _timestamp_pb2.Timestamp
    labels: _containers.ScalarMap[str, str]
    def __init__(self, tenant_id: _Optional[str] = ..., execution_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., event_type: _Optional[str] = ..., start_sequence: _Optional[int] = ..., start_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class GetEventStoreStatsRequest(_message.Message):
    __slots__ = ("tenant_id",)
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    def __init__(self, tenant_id: _Optional[str] = ...) -> None: ...

class GetEventStoreStatsResponse(_message.Message):
    __slots__ = ("total_events", "events_by_type", "storage_bytes", "oldest_event", "newest_event", "streams")
    class EventsByTypeEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    class StreamInfo(_message.Message):
        __slots__ = ("stream_name", "message_count", "bytes", "first_timestamp", "last_timestamp")
        STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
        BYTES_FIELD_NUMBER: _ClassVar[int]
        FIRST_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        LAST_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        stream_name: str
        message_count: int
        bytes: int
        first_timestamp: _timestamp_pb2.Timestamp
        last_timestamp: _timestamp_pb2.Timestamp
        def __init__(self, stream_name: _Optional[str] = ..., message_count: _Optional[int] = ..., bytes: _Optional[int] = ..., first_timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., last_timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    TOTAL_EVENTS_FIELD_NUMBER: _ClassVar[int]
    EVENTS_BY_TYPE_FIELD_NUMBER: _ClassVar[int]
    STORAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    OLDEST_EVENT_FIELD_NUMBER: _ClassVar[int]
    NEWEST_EVENT_FIELD_NUMBER: _ClassVar[int]
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    total_events: int
    events_by_type: _containers.ScalarMap[str, int]
    storage_bytes: int
    oldest_event: _timestamp_pb2.Timestamp
    newest_event: _timestamp_pb2.Timestamp
    streams: _containers.RepeatedCompositeFieldContainer[GetEventStoreStatsResponse.StreamInfo]
    def __init__(self, total_events: _Optional[int] = ..., events_by_type: _Optional[_Mapping[str, int]] = ..., storage_bytes: _Optional[int] = ..., oldest_event: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., newest_event: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., streams: _Optional[_Iterable[_Union[GetEventStoreStatsResponse.StreamInfo, _Mapping]]] = ...) -> None: ...

class EventFilter(_message.Message):
    __slots__ = ("filter_id", "name", "description", "event_types", "tenant_ids", "labels", "retention")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class RetentionPolicy(_message.Message):
        __slots__ = ("duration", "max_bytes", "max_messages")
        DURATION_FIELD_NUMBER: _ClassVar[int]
        MAX_BYTES_FIELD_NUMBER: _ClassVar[int]
        MAX_MESSAGES_FIELD_NUMBER: _ClassVar[int]
        duration: str
        max_bytes: int
        max_messages: int
        def __init__(self, duration: _Optional[str] = ..., max_bytes: _Optional[int] = ..., max_messages: _Optional[int] = ...) -> None: ...
    FILTER_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPES_FIELD_NUMBER: _ClassVar[int]
    TENANT_IDS_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    RETENTION_FIELD_NUMBER: _ClassVar[int]
    filter_id: str
    name: str
    description: str
    event_types: _containers.RepeatedScalarFieldContainer[str]
    tenant_ids: _containers.RepeatedScalarFieldContainer[str]
    labels: _containers.ScalarMap[str, str]
    retention: EventFilter.RetentionPolicy
    def __init__(self, filter_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., event_types: _Optional[_Iterable[str]] = ..., tenant_ids: _Optional[_Iterable[str]] = ..., labels: _Optional[_Mapping[str, str]] = ..., retention: _Optional[_Union[EventFilter.RetentionPolicy, _Mapping]] = ...) -> None: ...
