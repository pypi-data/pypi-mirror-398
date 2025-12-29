import datetime

from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
import envelope_pb2 as _envelope_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BudgetPeriodType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BUDGET_PERIOD_TYPE_UNSPECIFIED: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_HOURLY: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_DAILY: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_WEEKLY: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_MONTHLY: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_QUARTERLY: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_YEARLY: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_CUSTOM: _ClassVar[BudgetPeriodType]
    BUDGET_PERIOD_TYPE_INFINITE: _ClassVar[BudgetPeriodType]

class BudgetStatusType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BUDGET_STATUS_TYPE_UNSPECIFIED: _ClassVar[BudgetStatusType]
    BUDGET_STATUS_TYPE_OK: _ClassVar[BudgetStatusType]
    BUDGET_STATUS_TYPE_WARNING: _ClassVar[BudgetStatusType]
    BUDGET_STATUS_TYPE_CRITICAL: _ClassVar[BudgetStatusType]
    BUDGET_STATUS_TYPE_EXCEEDED: _ClassVar[BudgetStatusType]
    BUDGET_STATUS_TYPE_SUSPENDED: _ClassVar[BudgetStatusType]

class SpendGroupBy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SPEND_GROUP_BY_UNSPECIFIED: _ClassVar[SpendGroupBy]
    SPEND_GROUP_BY_MODEL: _ClassVar[SpendGroupBy]
    SPEND_GROUP_BY_DAY: _ClassVar[SpendGroupBy]
    SPEND_GROUP_BY_WEEK: _ClassVar[SpendGroupBy]
    SPEND_GROUP_BY_MONTH: _ClassVar[SpendGroupBy]
    SPEND_GROUP_BY_WORKFLOW: _ClassVar[SpendGroupBy]
BUDGET_PERIOD_TYPE_UNSPECIFIED: BudgetPeriodType
BUDGET_PERIOD_TYPE_HOURLY: BudgetPeriodType
BUDGET_PERIOD_TYPE_DAILY: BudgetPeriodType
BUDGET_PERIOD_TYPE_WEEKLY: BudgetPeriodType
BUDGET_PERIOD_TYPE_MONTHLY: BudgetPeriodType
BUDGET_PERIOD_TYPE_QUARTERLY: BudgetPeriodType
BUDGET_PERIOD_TYPE_YEARLY: BudgetPeriodType
BUDGET_PERIOD_TYPE_CUSTOM: BudgetPeriodType
BUDGET_PERIOD_TYPE_INFINITE: BudgetPeriodType
BUDGET_STATUS_TYPE_UNSPECIFIED: BudgetStatusType
BUDGET_STATUS_TYPE_OK: BudgetStatusType
BUDGET_STATUS_TYPE_WARNING: BudgetStatusType
BUDGET_STATUS_TYPE_CRITICAL: BudgetStatusType
BUDGET_STATUS_TYPE_EXCEEDED: BudgetStatusType
BUDGET_STATUS_TYPE_SUSPENDED: BudgetStatusType
SPEND_GROUP_BY_UNSPECIFIED: SpendGroupBy
SPEND_GROUP_BY_MODEL: SpendGroupBy
SPEND_GROUP_BY_DAY: SpendGroupBy
SPEND_GROUP_BY_WEEK: SpendGroupBy
SPEND_GROUP_BY_MONTH: SpendGroupBy
SPEND_GROUP_BY_WORKFLOW: SpendGroupBy

class Budget(_message.Message):
    __slots__ = ("budget_id", "tenant_id", "workflow_id", "limits", "thresholds", "period", "current_spend", "status", "name", "description", "tags", "created_at", "updated_at", "reset_at")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    BUDGET_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    LIMITS_FIELD_NUMBER: _ClassVar[int]
    THRESHOLDS_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    CURRENT_SPEND_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    RESET_AT_FIELD_NUMBER: _ClassVar[int]
    budget_id: str
    tenant_id: str
    workflow_id: str
    limits: BudgetLimits
    thresholds: _containers.RepeatedCompositeFieldContainer[NotificationThreshold]
    period: BudgetPeriod
    current_spend: SpendSummary
    status: BudgetStatusType
    name: str
    description: str
    tags: _containers.ScalarMap[str, str]
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    reset_at: _timestamp_pb2.Timestamp
    def __init__(self, budget_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., limits: _Optional[_Union[BudgetLimits, _Mapping]] = ..., thresholds: _Optional[_Iterable[_Union[NotificationThreshold, _Mapping]]] = ..., period: _Optional[_Union[BudgetPeriod, _Mapping]] = ..., current_spend: _Optional[_Union[SpendSummary, _Mapping]] = ..., status: _Optional[_Union[BudgetStatusType, str]] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., tags: _Optional[_Mapping[str, str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., reset_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class BudgetLimits(_message.Message):
    __slots__ = ("max_tokens", "max_input_tokens", "max_output_tokens", "max_cost_usd", "max_llm_calls", "max_tool_calls", "max_execution_time_seconds")
    MAX_TOKENS_FIELD_NUMBER: _ClassVar[int]
    MAX_INPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    MAX_OUTPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    MAX_COST_USD_FIELD_NUMBER: _ClassVar[int]
    MAX_LLM_CALLS_FIELD_NUMBER: _ClassVar[int]
    MAX_TOOL_CALLS_FIELD_NUMBER: _ClassVar[int]
    MAX_EXECUTION_TIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    max_tokens: int
    max_input_tokens: int
    max_output_tokens: int
    max_cost_usd: float
    max_llm_calls: int
    max_tool_calls: int
    max_execution_time_seconds: int
    def __init__(self, max_tokens: _Optional[int] = ..., max_input_tokens: _Optional[int] = ..., max_output_tokens: _Optional[int] = ..., max_cost_usd: _Optional[float] = ..., max_llm_calls: _Optional[int] = ..., max_tool_calls: _Optional[int] = ..., max_execution_time_seconds: _Optional[int] = ...) -> None: ...

class NotificationThreshold(_message.Message):
    __slots__ = ("threshold_percent", "notified", "notified_at")
    THRESHOLD_PERCENT_FIELD_NUMBER: _ClassVar[int]
    NOTIFIED_FIELD_NUMBER: _ClassVar[int]
    NOTIFIED_AT_FIELD_NUMBER: _ClassVar[int]
    threshold_percent: float
    notified: bool
    notified_at: _timestamp_pb2.Timestamp
    def __init__(self, threshold_percent: _Optional[float] = ..., notified: bool = ..., notified_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class BudgetPeriod(_message.Message):
    __slots__ = ("period_type", "duration_seconds", "period_start", "period_end")
    PERIOD_TYPE_FIELD_NUMBER: _ClassVar[int]
    DURATION_SECONDS_FIELD_NUMBER: _ClassVar[int]
    PERIOD_START_FIELD_NUMBER: _ClassVar[int]
    PERIOD_END_FIELD_NUMBER: _ClassVar[int]
    period_type: BudgetPeriodType
    duration_seconds: int
    period_start: _timestamp_pb2.Timestamp
    period_end: _timestamp_pb2.Timestamp
    def __init__(self, period_type: _Optional[_Union[BudgetPeriodType, str]] = ..., duration_seconds: _Optional[int] = ..., period_start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., period_end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class SpendSummary(_message.Message):
    __slots__ = ("total_tokens", "total_input_tokens", "total_output_tokens", "total_cost_usd", "total_llm_calls", "total_tool_calls", "total_executions", "completed_executions", "failed_executions", "terminated_executions", "total_execution_time_seconds", "average_execution_time_seconds", "model_costs", "period_start", "period_end")
    TOTAL_TOKENS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_INPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_OUTPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COST_USD_FIELD_NUMBER: _ClassVar[int]
    TOTAL_LLM_CALLS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_TOOL_CALLS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    FAILED_EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    TERMINATED_EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_EXECUTION_TIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_EXECUTION_TIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    MODEL_COSTS_FIELD_NUMBER: _ClassVar[int]
    PERIOD_START_FIELD_NUMBER: _ClassVar[int]
    PERIOD_END_FIELD_NUMBER: _ClassVar[int]
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    total_llm_calls: int
    total_tool_calls: int
    total_executions: int
    completed_executions: int
    failed_executions: int
    terminated_executions: int
    total_execution_time_seconds: int
    average_execution_time_seconds: int
    model_costs: _containers.RepeatedCompositeFieldContainer[_envelope_pb2.ModelCost]
    period_start: _timestamp_pb2.Timestamp
    period_end: _timestamp_pb2.Timestamp
    def __init__(self, total_tokens: _Optional[int] = ..., total_input_tokens: _Optional[int] = ..., total_output_tokens: _Optional[int] = ..., total_cost_usd: _Optional[float] = ..., total_llm_calls: _Optional[int] = ..., total_tool_calls: _Optional[int] = ..., total_executions: _Optional[int] = ..., completed_executions: _Optional[int] = ..., failed_executions: _Optional[int] = ..., terminated_executions: _Optional[int] = ..., total_execution_time_seconds: _Optional[int] = ..., average_execution_time_seconds: _Optional[int] = ..., model_costs: _Optional[_Iterable[_Union[_envelope_pb2.ModelCost, _Mapping]]] = ..., period_start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., period_end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class BudgetStatus(_message.Message):
    __slots__ = ("budget_id", "status", "token_usage_percent", "cost_usage_percent", "llm_call_usage_percent", "tool_call_usage_percent", "remaining", "current_spend", "next_threshold", "updated_at")
    BUDGET_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOKEN_USAGE_PERCENT_FIELD_NUMBER: _ClassVar[int]
    COST_USAGE_PERCENT_FIELD_NUMBER: _ClassVar[int]
    LLM_CALL_USAGE_PERCENT_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALL_USAGE_PERCENT_FIELD_NUMBER: _ClassVar[int]
    REMAINING_FIELD_NUMBER: _ClassVar[int]
    CURRENT_SPEND_FIELD_NUMBER: _ClassVar[int]
    NEXT_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    budget_id: str
    status: BudgetStatusType
    token_usage_percent: float
    cost_usage_percent: float
    llm_call_usage_percent: float
    tool_call_usage_percent: float
    remaining: BudgetLimits
    current_spend: SpendSummary
    next_threshold: NotificationThreshold
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, budget_id: _Optional[str] = ..., status: _Optional[_Union[BudgetStatusType, str]] = ..., token_usage_percent: _Optional[float] = ..., cost_usage_percent: _Optional[float] = ..., llm_call_usage_percent: _Optional[float] = ..., tool_call_usage_percent: _Optional[float] = ..., remaining: _Optional[_Union[BudgetLimits, _Mapping]] = ..., current_spend: _Optional[_Union[SpendSummary, _Mapping]] = ..., next_threshold: _Optional[_Union[NotificationThreshold, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateBudgetRequest(_message.Message):
    __slots__ = ("budget",)
    BUDGET_FIELD_NUMBER: _ClassVar[int]
    budget: Budget
    def __init__(self, budget: _Optional[_Union[Budget, _Mapping]] = ...) -> None: ...

class CreateBudgetResponse(_message.Message):
    __slots__ = ("budget",)
    BUDGET_FIELD_NUMBER: _ClassVar[int]
    budget: Budget
    def __init__(self, budget: _Optional[_Union[Budget, _Mapping]] = ...) -> None: ...

class GetBudgetRequest(_message.Message):
    __slots__ = ("budget_id",)
    BUDGET_ID_FIELD_NUMBER: _ClassVar[int]
    budget_id: str
    def __init__(self, budget_id: _Optional[str] = ...) -> None: ...

class GetBudgetResponse(_message.Message):
    __slots__ = ("budget",)
    BUDGET_FIELD_NUMBER: _ClassVar[int]
    budget: Budget
    def __init__(self, budget: _Optional[_Union[Budget, _Mapping]] = ...) -> None: ...

class UpdateBudgetRequest(_message.Message):
    __slots__ = ("budget", "update_mask")
    BUDGET_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    budget: Budget
    update_mask: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, budget: _Optional[_Union[Budget, _Mapping]] = ..., update_mask: _Optional[_Iterable[str]] = ...) -> None: ...

class UpdateBudgetResponse(_message.Message):
    __slots__ = ("budget",)
    BUDGET_FIELD_NUMBER: _ClassVar[int]
    budget: Budget
    def __init__(self, budget: _Optional[_Union[Budget, _Mapping]] = ...) -> None: ...

class DeleteBudgetRequest(_message.Message):
    __slots__ = ("budget_id",)
    BUDGET_ID_FIELD_NUMBER: _ClassVar[int]
    budget_id: str
    def __init__(self, budget_id: _Optional[str] = ...) -> None: ...

class DeleteBudgetResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ListBudgetsRequest(_message.Message):
    __slots__ = ("tenant_id", "workflow_id", "status", "page_size", "page_token")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    workflow_id: str
    status: BudgetStatusType
    page_size: int
    page_token: str
    def __init__(self, tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., status: _Optional[_Union[BudgetStatusType, str]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListBudgetsResponse(_message.Message):
    __slots__ = ("budgets", "next_page_token", "total_count")
    BUDGETS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    budgets: _containers.RepeatedCompositeFieldContainer[Budget]
    next_page_token: str
    total_count: int
    def __init__(self, budgets: _Optional[_Iterable[_Union[Budget, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class GetCostSummaryRequest(_message.Message):
    __slots__ = ("envelope_id",)
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    envelope_id: str
    def __init__(self, envelope_id: _Optional[str] = ...) -> None: ...

class GetCostSummaryResponse(_message.Message):
    __slots__ = ("cost_summary",)
    COST_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    cost_summary: _envelope_pb2.CostSummary
    def __init__(self, cost_summary: _Optional[_Union[_envelope_pb2.CostSummary, _Mapping]] = ...) -> None: ...

class GetSpendSummaryRequest(_message.Message):
    __slots__ = ("tenant_id", "workflow_id", "start_time", "end_time", "group_by")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    GROUP_BY_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    workflow_id: str
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    group_by: SpendGroupBy
    def __init__(self, tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., start_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., group_by: _Optional[_Union[SpendGroupBy, str]] = ...) -> None: ...

class GetSpendSummaryResponse(_message.Message):
    __slots__ = ("summary", "grouped_summaries")
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    GROUPED_SUMMARIES_FIELD_NUMBER: _ClassVar[int]
    summary: SpendSummary
    grouped_summaries: _containers.RepeatedCompositeFieldContainer[GroupedSpendSummary]
    def __init__(self, summary: _Optional[_Union[SpendSummary, _Mapping]] = ..., grouped_summaries: _Optional[_Iterable[_Union[GroupedSpendSummary, _Mapping]]] = ...) -> None: ...

class GroupedSpendSummary(_message.Message):
    __slots__ = ("group_key", "summary")
    GROUP_KEY_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    group_key: str
    summary: SpendSummary
    def __init__(self, group_key: _Optional[str] = ..., summary: _Optional[_Union[SpendSummary, _Mapping]] = ...) -> None: ...

class GetBudgetStatusRequest(_message.Message):
    __slots__ = ("budget_id",)
    BUDGET_ID_FIELD_NUMBER: _ClassVar[int]
    budget_id: str
    def __init__(self, budget_id: _Optional[str] = ...) -> None: ...

class GetBudgetStatusResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: BudgetStatus
    def __init__(self, status: _Optional[_Union[BudgetStatus, _Mapping]] = ...) -> None: ...

class PredictCostRequest(_message.Message):
    __slots__ = ("tenant_id", "workflow_id", "input_text", "estimated_input_tokens", "model_ids", "use_historical_data", "lookback_days")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    INPUT_TEXT_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_INPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    MODEL_IDS_FIELD_NUMBER: _ClassVar[int]
    USE_HISTORICAL_DATA_FIELD_NUMBER: _ClassVar[int]
    LOOKBACK_DAYS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    workflow_id: str
    input_text: str
    estimated_input_tokens: int
    model_ids: _containers.RepeatedScalarFieldContainer[str]
    use_historical_data: bool
    lookback_days: int
    def __init__(self, tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., input_text: _Optional[str] = ..., estimated_input_tokens: _Optional[int] = ..., model_ids: _Optional[_Iterable[str]] = ..., use_historical_data: bool = ..., lookback_days: _Optional[int] = ...) -> None: ...

class PredictCostResponse(_message.Message):
    __slots__ = ("prediction", "historical_based", "sample_size")
    PREDICTION_FIELD_NUMBER: _ClassVar[int]
    HISTORICAL_BASED_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_SIZE_FIELD_NUMBER: _ClassVar[int]
    prediction: CostPrediction
    historical_based: bool
    sample_size: int
    def __init__(self, prediction: _Optional[_Union[CostPrediction, _Mapping]] = ..., historical_based: bool = ..., sample_size: _Optional[int] = ...) -> None: ...

class CostPrediction(_message.Message):
    __slots__ = ("estimated_input_tokens", "estimated_output_tokens", "estimated_total_tokens", "estimated_cost_usd", "estimated_cost_usd_min", "estimated_cost_usd_max", "confidence", "confidence_level", "estimated_duration_seconds", "model_predictions")
    ESTIMATED_INPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_OUTPUT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_TOTAL_TOKENS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_COST_USD_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_COST_USD_MIN_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_COST_USD_MAX_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_DURATION_SECONDS_FIELD_NUMBER: _ClassVar[int]
    MODEL_PREDICTIONS_FIELD_NUMBER: _ClassVar[int]
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_total_tokens: int
    estimated_cost_usd: float
    estimated_cost_usd_min: float
    estimated_cost_usd_max: float
    confidence: float
    confidence_level: str
    estimated_duration_seconds: int
    model_predictions: _containers.RepeatedCompositeFieldContainer[ModelCostPrediction]
    def __init__(self, estimated_input_tokens: _Optional[int] = ..., estimated_output_tokens: _Optional[int] = ..., estimated_total_tokens: _Optional[int] = ..., estimated_cost_usd: _Optional[float] = ..., estimated_cost_usd_min: _Optional[float] = ..., estimated_cost_usd_max: _Optional[float] = ..., confidence: _Optional[float] = ..., confidence_level: _Optional[str] = ..., estimated_duration_seconds: _Optional[int] = ..., model_predictions: _Optional[_Iterable[_Union[ModelCostPrediction, _Mapping]]] = ...) -> None: ...

class ModelCostPrediction(_message.Message):
    __slots__ = ("model_id", "estimated_tokens", "estimated_cost_usd", "estimated_calls")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_TOKENS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_COST_USD_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_CALLS_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    estimated_tokens: int
    estimated_cost_usd: float
    estimated_calls: int
    def __init__(self, model_id: _Optional[str] = ..., estimated_tokens: _Optional[int] = ..., estimated_cost_usd: _Optional[float] = ..., estimated_calls: _Optional[int] = ...) -> None: ...
