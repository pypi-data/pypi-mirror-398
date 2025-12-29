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

class PolicyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    POLICY_STATUS_UNSPECIFIED: _ClassVar[PolicyStatus]
    POLICY_STATUS_DRAFT: _ClassVar[PolicyStatus]
    POLICY_STATUS_ACTIVE: _ClassVar[PolicyStatus]
    POLICY_STATUS_INACTIVE: _ClassVar[PolicyStatus]
    POLICY_STATUS_ARCHIVED: _ClassVar[PolicyStatus]

class EnforcementLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ENFORCEMENT_LEVEL_UNSPECIFIED: _ClassVar[EnforcementLevel]
    ENFORCEMENT_LEVEL_AUDIT: _ClassVar[EnforcementLevel]
    ENFORCEMENT_LEVEL_WARN: _ClassVar[EnforcementLevel]
    ENFORCEMENT_LEVEL_BLOCK: _ClassVar[EnforcementLevel]
    ENFORCEMENT_LEVEL_TERMINATE: _ClassVar[EnforcementLevel]

class RuleType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RULE_TYPE_UNSPECIFIED: _ClassVar[RuleType]
    RULE_TYPE_RBAC: _ClassVar[RuleType]
    RULE_TYPE_CONTENT_FILTER: _ClassVar[RuleType]
    RULE_TYPE_TOOL_ALLOWLIST: _ClassVar[RuleType]
    RULE_TYPE_MODEL_RESTRICTION: _ClassVar[RuleType]
    RULE_TYPE_RATE_LIMIT: _ClassVar[RuleType]
    RULE_TYPE_COST_CONTROL: _ClassVar[RuleType]
    RULE_TYPE_CUSTOM: _ClassVar[RuleType]

class ConditionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONDITION_TYPE_UNSPECIFIED: _ClassVar[ConditionType]
    CONDITION_TYPE_FIELD_MATCH: _ClassVar[ConditionType]
    CONDITION_TYPE_REGEX: _ClassVar[ConditionType]
    CONDITION_TYPE_RANGE: _ClassVar[ConditionType]
    CONDITION_TYPE_IN_LIST: _ClassVar[ConditionType]
    CONDITION_TYPE_CONTAINS: _ClassVar[ConditionType]
    CONDITION_TYPE_STARTS_WITH: _ClassVar[ConditionType]
    CONDITION_TYPE_ENDS_WITH: _ClassVar[ConditionType]
    CONDITION_TYPE_LOGICAL: _ClassVar[ConditionType]

class ConditionOperator(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONDITION_OPERATOR_UNSPECIFIED: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_EQUALS: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_NOT_EQUALS: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_GREATER_THAN: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_LESS_THAN: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_GREATER_EQUAL: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_LESS_EQUAL: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_MATCHES: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_CONTAINS: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_IN: _ClassVar[ConditionOperator]
    CONDITION_OPERATOR_NOT_IN: _ClassVar[ConditionOperator]

class LogicalOperator(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOGICAL_OPERATOR_UNSPECIFIED: _ClassVar[LogicalOperator]
    LOGICAL_OPERATOR_AND: _ClassVar[LogicalOperator]
    LOGICAL_OPERATOR_OR: _ClassVar[LogicalOperator]
    LOGICAL_OPERATOR_NOT: _ClassVar[LogicalOperator]

class ActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ACTION_TYPE_UNSPECIFIED: _ClassVar[ActionType]
    ACTION_TYPE_ALLOW: _ClassVar[ActionType]
    ACTION_TYPE_DENY: _ClassVar[ActionType]
    ACTION_TYPE_WARN: _ClassVar[ActionType]
    ACTION_TYPE_MODIFY: _ClassVar[ActionType]
    ACTION_TYPE_REDIRECT: _ClassVar[ActionType]
    ACTION_TYPE_AUDIT: _ClassVar[ActionType]
    ACTION_TYPE_THROTTLE: _ClassVar[ActionType]
    ACTION_TYPE_REQUIRE_APPROVAL: _ClassVar[ActionType]

class SeverityLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SEVERITY_LEVEL_UNSPECIFIED: _ClassVar[SeverityLevel]
    SEVERITY_LEVEL_INFO: _ClassVar[SeverityLevel]
    SEVERITY_LEVEL_LOW: _ClassVar[SeverityLevel]
    SEVERITY_LEVEL_MEDIUM: _ClassVar[SeverityLevel]
    SEVERITY_LEVEL_HIGH: _ClassVar[SeverityLevel]
    SEVERITY_LEVEL_CRITICAL: _ClassVar[SeverityLevel]

class ExecutionPhase(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXECUTION_PHASE_UNSPECIFIED: _ClassVar[ExecutionPhase]
    EXECUTION_PHASE_PRE_EXECUTION: _ClassVar[ExecutionPhase]
    EXECUTION_PHASE_PRE_LLM_CALL: _ClassVar[ExecutionPhase]
    EXECUTION_PHASE_POST_LLM_CALL: _ClassVar[ExecutionPhase]
    EXECUTION_PHASE_PRE_TOOL_CALL: _ClassVar[ExecutionPhase]
    EXECUTION_PHASE_POST_TOOL_CALL: _ClassVar[ExecutionPhase]
    EXECUTION_PHASE_POST_EXECUTION: _ClassVar[ExecutionPhase]

class EvaluationDecision(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVALUATION_DECISION_UNSPECIFIED: _ClassVar[EvaluationDecision]
    EVALUATION_DECISION_ALLOW: _ClassVar[EvaluationDecision]
    EVALUATION_DECISION_DENY: _ClassVar[EvaluationDecision]
    EVALUATION_DECISION_WARN: _ClassVar[EvaluationDecision]
    EVALUATION_DECISION_REQUIRE_APPROVAL: _ClassVar[EvaluationDecision]
POLICY_STATUS_UNSPECIFIED: PolicyStatus
POLICY_STATUS_DRAFT: PolicyStatus
POLICY_STATUS_ACTIVE: PolicyStatus
POLICY_STATUS_INACTIVE: PolicyStatus
POLICY_STATUS_ARCHIVED: PolicyStatus
ENFORCEMENT_LEVEL_UNSPECIFIED: EnforcementLevel
ENFORCEMENT_LEVEL_AUDIT: EnforcementLevel
ENFORCEMENT_LEVEL_WARN: EnforcementLevel
ENFORCEMENT_LEVEL_BLOCK: EnforcementLevel
ENFORCEMENT_LEVEL_TERMINATE: EnforcementLevel
RULE_TYPE_UNSPECIFIED: RuleType
RULE_TYPE_RBAC: RuleType
RULE_TYPE_CONTENT_FILTER: RuleType
RULE_TYPE_TOOL_ALLOWLIST: RuleType
RULE_TYPE_MODEL_RESTRICTION: RuleType
RULE_TYPE_RATE_LIMIT: RuleType
RULE_TYPE_COST_CONTROL: RuleType
RULE_TYPE_CUSTOM: RuleType
CONDITION_TYPE_UNSPECIFIED: ConditionType
CONDITION_TYPE_FIELD_MATCH: ConditionType
CONDITION_TYPE_REGEX: ConditionType
CONDITION_TYPE_RANGE: ConditionType
CONDITION_TYPE_IN_LIST: ConditionType
CONDITION_TYPE_CONTAINS: ConditionType
CONDITION_TYPE_STARTS_WITH: ConditionType
CONDITION_TYPE_ENDS_WITH: ConditionType
CONDITION_TYPE_LOGICAL: ConditionType
CONDITION_OPERATOR_UNSPECIFIED: ConditionOperator
CONDITION_OPERATOR_EQUALS: ConditionOperator
CONDITION_OPERATOR_NOT_EQUALS: ConditionOperator
CONDITION_OPERATOR_GREATER_THAN: ConditionOperator
CONDITION_OPERATOR_LESS_THAN: ConditionOperator
CONDITION_OPERATOR_GREATER_EQUAL: ConditionOperator
CONDITION_OPERATOR_LESS_EQUAL: ConditionOperator
CONDITION_OPERATOR_MATCHES: ConditionOperator
CONDITION_OPERATOR_CONTAINS: ConditionOperator
CONDITION_OPERATOR_IN: ConditionOperator
CONDITION_OPERATOR_NOT_IN: ConditionOperator
LOGICAL_OPERATOR_UNSPECIFIED: LogicalOperator
LOGICAL_OPERATOR_AND: LogicalOperator
LOGICAL_OPERATOR_OR: LogicalOperator
LOGICAL_OPERATOR_NOT: LogicalOperator
ACTION_TYPE_UNSPECIFIED: ActionType
ACTION_TYPE_ALLOW: ActionType
ACTION_TYPE_DENY: ActionType
ACTION_TYPE_WARN: ActionType
ACTION_TYPE_MODIFY: ActionType
ACTION_TYPE_REDIRECT: ActionType
ACTION_TYPE_AUDIT: ActionType
ACTION_TYPE_THROTTLE: ActionType
ACTION_TYPE_REQUIRE_APPROVAL: ActionType
SEVERITY_LEVEL_UNSPECIFIED: SeverityLevel
SEVERITY_LEVEL_INFO: SeverityLevel
SEVERITY_LEVEL_LOW: SeverityLevel
SEVERITY_LEVEL_MEDIUM: SeverityLevel
SEVERITY_LEVEL_HIGH: SeverityLevel
SEVERITY_LEVEL_CRITICAL: SeverityLevel
EXECUTION_PHASE_UNSPECIFIED: ExecutionPhase
EXECUTION_PHASE_PRE_EXECUTION: ExecutionPhase
EXECUTION_PHASE_PRE_LLM_CALL: ExecutionPhase
EXECUTION_PHASE_POST_LLM_CALL: ExecutionPhase
EXECUTION_PHASE_PRE_TOOL_CALL: ExecutionPhase
EXECUTION_PHASE_POST_TOOL_CALL: ExecutionPhase
EXECUTION_PHASE_POST_EXECUTION: ExecutionPhase
EVALUATION_DECISION_UNSPECIFIED: EvaluationDecision
EVALUATION_DECISION_ALLOW: EvaluationDecision
EVALUATION_DECISION_DENY: EvaluationDecision
EVALUATION_DECISION_WARN: EvaluationDecision
EVALUATION_DECISION_REQUIRE_APPROVAL: EvaluationDecision

class Policy(_message.Message):
    __slots__ = ("policy_id", "tenant_id", "name", "description", "tags", "rules", "scope", "status", "enforcement", "priority", "created_at", "updated_at", "effective_at", "expires_at", "created_by")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    POLICY_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    RULES_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENFORCEMENT_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    EFFECTIVE_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    policy_id: str
    tenant_id: str
    name: str
    description: str
    tags: _containers.ScalarMap[str, str]
    rules: _containers.RepeatedCompositeFieldContainer[PolicyRule]
    scope: PolicyScope
    status: PolicyStatus
    enforcement: EnforcementLevel
    priority: int
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    effective_at: _timestamp_pb2.Timestamp
    expires_at: _timestamp_pb2.Timestamp
    created_by: str
    def __init__(self, policy_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., tags: _Optional[_Mapping[str, str]] = ..., rules: _Optional[_Iterable[_Union[PolicyRule, _Mapping]]] = ..., scope: _Optional[_Union[PolicyScope, _Mapping]] = ..., status: _Optional[_Union[PolicyStatus, str]] = ..., enforcement: _Optional[_Union[EnforcementLevel, str]] = ..., priority: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., effective_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., created_by: _Optional[str] = ...) -> None: ...

class PolicyRule(_message.Message):
    __slots__ = ("rule_id", "name", "description", "conditions", "actions", "rule_type", "enabled", "priority")
    RULE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    RULE_TYPE_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    rule_id: str
    name: str
    description: str
    conditions: _containers.RepeatedCompositeFieldContainer[PolicyCondition]
    actions: _containers.RepeatedCompositeFieldContainer[PolicyAction]
    rule_type: RuleType
    enabled: bool
    priority: int
    def __init__(self, rule_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., conditions: _Optional[_Iterable[_Union[PolicyCondition, _Mapping]]] = ..., actions: _Optional[_Iterable[_Union[PolicyAction, _Mapping]]] = ..., rule_type: _Optional[_Union[RuleType, str]] = ..., enabled: bool = ..., priority: _Optional[int] = ...) -> None: ...

class PolicyCondition(_message.Message):
    __slots__ = ("condition_type", "field", "operator", "string_value", "int_value", "float_value", "bool_value", "list_value", "values", "nested_conditions", "logical_operator", "negate")
    CONDITION_TYPE_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    LIST_VALUE_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    NESTED_CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    LOGICAL_OPERATOR_FIELD_NUMBER: _ClassVar[int]
    NEGATE_FIELD_NUMBER: _ClassVar[int]
    condition_type: ConditionType
    field: str
    operator: ConditionOperator
    string_value: str
    int_value: int
    float_value: float
    bool_value: bool
    list_value: _struct_pb2.ListValue
    values: _containers.RepeatedScalarFieldContainer[str]
    nested_conditions: _containers.RepeatedCompositeFieldContainer[PolicyCondition]
    logical_operator: LogicalOperator
    negate: bool
    def __init__(self, condition_type: _Optional[_Union[ConditionType, str]] = ..., field: _Optional[str] = ..., operator: _Optional[_Union[ConditionOperator, str]] = ..., string_value: _Optional[str] = ..., int_value: _Optional[int] = ..., float_value: _Optional[float] = ..., bool_value: bool = ..., list_value: _Optional[_Union[_struct_pb2.ListValue, _Mapping]] = ..., values: _Optional[_Iterable[str]] = ..., nested_conditions: _Optional[_Iterable[_Union[PolicyCondition, _Mapping]]] = ..., logical_operator: _Optional[_Union[LogicalOperator, str]] = ..., negate: bool = ...) -> None: ...

class PolicyAction(_message.Message):
    __slots__ = ("action_type", "parameters", "message", "severity", "terminal")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    TERMINAL_FIELD_NUMBER: _ClassVar[int]
    action_type: ActionType
    parameters: _containers.ScalarMap[str, str]
    message: str
    severity: SeverityLevel
    terminal: bool
    def __init__(self, action_type: _Optional[_Union[ActionType, str]] = ..., parameters: _Optional[_Mapping[str, str]] = ..., message: _Optional[str] = ..., severity: _Optional[_Union[SeverityLevel, str]] = ..., terminal: bool = ...) -> None: ...

class PolicyScope(_message.Message):
    __slots__ = ("workflow_ids", "phases", "roles", "model_ids", "tool_names", "apply_to_all")
    WORKFLOW_IDS_FIELD_NUMBER: _ClassVar[int]
    PHASES_FIELD_NUMBER: _ClassVar[int]
    ROLES_FIELD_NUMBER: _ClassVar[int]
    MODEL_IDS_FIELD_NUMBER: _ClassVar[int]
    TOOL_NAMES_FIELD_NUMBER: _ClassVar[int]
    APPLY_TO_ALL_FIELD_NUMBER: _ClassVar[int]
    workflow_ids: _containers.RepeatedScalarFieldContainer[str]
    phases: _containers.RepeatedScalarFieldContainer[ExecutionPhase]
    roles: _containers.RepeatedScalarFieldContainer[str]
    model_ids: _containers.RepeatedScalarFieldContainer[str]
    tool_names: _containers.RepeatedScalarFieldContainer[str]
    apply_to_all: bool
    def __init__(self, workflow_ids: _Optional[_Iterable[str]] = ..., phases: _Optional[_Iterable[_Union[ExecutionPhase, str]]] = ..., roles: _Optional[_Iterable[str]] = ..., model_ids: _Optional[_Iterable[str]] = ..., tool_names: _Optional[_Iterable[str]] = ..., apply_to_all: bool = ...) -> None: ...

class EvaluationResult(_message.Message):
    __slots__ = ("policy_id", "decision", "matched_rules", "actions", "message", "metadata", "evaluated_at", "evaluation_duration_ms", "context")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    POLICY_ID_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    MATCHED_RULES_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    EVALUATED_AT_FIELD_NUMBER: _ClassVar[int]
    EVALUATION_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    policy_id: str
    decision: EvaluationDecision
    matched_rules: _containers.RepeatedCompositeFieldContainer[RuleMatch]
    actions: _containers.RepeatedCompositeFieldContainer[PolicyAction]
    message: str
    metadata: _containers.ScalarMap[str, str]
    evaluated_at: _timestamp_pb2.Timestamp
    evaluation_duration_ms: int
    context: EvaluationContext
    def __init__(self, policy_id: _Optional[str] = ..., decision: _Optional[_Union[EvaluationDecision, str]] = ..., matched_rules: _Optional[_Iterable[_Union[RuleMatch, _Mapping]]] = ..., actions: _Optional[_Iterable[_Union[PolicyAction, _Mapping]]] = ..., message: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., evaluated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., evaluation_duration_ms: _Optional[int] = ..., context: _Optional[_Union[EvaluationContext, _Mapping]] = ...) -> None: ...

class RuleMatch(_message.Message):
    __slots__ = ("rule_id", "rule_name", "matched_conditions", "priority")
    RULE_ID_FIELD_NUMBER: _ClassVar[int]
    RULE_NAME_FIELD_NUMBER: _ClassVar[int]
    MATCHED_CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    rule_id: str
    rule_name: str
    matched_conditions: _containers.RepeatedScalarFieldContainer[str]
    priority: int
    def __init__(self, rule_id: _Optional[str] = ..., rule_name: _Optional[str] = ..., matched_conditions: _Optional[_Iterable[str]] = ..., priority: _Optional[int] = ...) -> None: ...

class EvaluationContext(_message.Message):
    __slots__ = ("tenant_id", "workflow_id", "envelope_id", "user_id", "user_roles", "phase", "model_id", "tool_names", "input_text", "output_text", "attributes", "timestamp")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    ENVELOPE_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ROLES_FIELD_NUMBER: _ClassVar[int]
    PHASE_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    TOOL_NAMES_FIELD_NUMBER: _ClassVar[int]
    INPUT_TEXT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TEXT_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    workflow_id: str
    envelope_id: str
    user_id: str
    user_roles: _containers.RepeatedScalarFieldContainer[str]
    phase: ExecutionPhase
    model_id: str
    tool_names: _containers.RepeatedScalarFieldContainer[str]
    input_text: str
    output_text: str
    attributes: _containers.ScalarMap[str, str]
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, tenant_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., envelope_id: _Optional[str] = ..., user_id: _Optional[str] = ..., user_roles: _Optional[_Iterable[str]] = ..., phase: _Optional[_Union[ExecutionPhase, str]] = ..., model_id: _Optional[str] = ..., tool_names: _Optional[_Iterable[str]] = ..., input_text: _Optional[str] = ..., output_text: _Optional[str] = ..., attributes: _Optional[_Mapping[str, str]] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreatePolicyRequest(_message.Message):
    __slots__ = ("policy",)
    POLICY_FIELD_NUMBER: _ClassVar[int]
    policy: Policy
    def __init__(self, policy: _Optional[_Union[Policy, _Mapping]] = ...) -> None: ...

class CreatePolicyResponse(_message.Message):
    __slots__ = ("policy",)
    POLICY_FIELD_NUMBER: _ClassVar[int]
    policy: Policy
    def __init__(self, policy: _Optional[_Union[Policy, _Mapping]] = ...) -> None: ...

class GetPolicyRequest(_message.Message):
    __slots__ = ("policy_id",)
    POLICY_ID_FIELD_NUMBER: _ClassVar[int]
    policy_id: str
    def __init__(self, policy_id: _Optional[str] = ...) -> None: ...

class GetPolicyResponse(_message.Message):
    __slots__ = ("policy",)
    POLICY_FIELD_NUMBER: _ClassVar[int]
    policy: Policy
    def __init__(self, policy: _Optional[_Union[Policy, _Mapping]] = ...) -> None: ...

class UpdatePolicyRequest(_message.Message):
    __slots__ = ("policy", "update_mask")
    POLICY_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    policy: Policy
    update_mask: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, policy: _Optional[_Union[Policy, _Mapping]] = ..., update_mask: _Optional[_Iterable[str]] = ...) -> None: ...

class UpdatePolicyResponse(_message.Message):
    __slots__ = ("policy",)
    POLICY_FIELD_NUMBER: _ClassVar[int]
    policy: Policy
    def __init__(self, policy: _Optional[_Union[Policy, _Mapping]] = ...) -> None: ...

class DeletePolicyRequest(_message.Message):
    __slots__ = ("policy_id",)
    POLICY_ID_FIELD_NUMBER: _ClassVar[int]
    policy_id: str
    def __init__(self, policy_id: _Optional[str] = ...) -> None: ...

class DeletePolicyResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ListPoliciesRequest(_message.Message):
    __slots__ = ("tenant_id", "status", "rule_type", "page_size", "page_token")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RULE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    status: PolicyStatus
    rule_type: RuleType
    page_size: int
    page_token: str
    def __init__(self, tenant_id: _Optional[str] = ..., status: _Optional[_Union[PolicyStatus, str]] = ..., rule_type: _Optional[_Union[RuleType, str]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListPoliciesResponse(_message.Message):
    __slots__ = ("policies", "next_page_token", "total_count")
    POLICIES_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    policies: _containers.RepeatedCompositeFieldContainer[Policy]
    next_page_token: str
    total_count: int
    def __init__(self, policies: _Optional[_Iterable[_Union[Policy, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class EvaluatePolicyRequest(_message.Message):
    __slots__ = ("policy_id", "context", "dry_run")
    POLICY_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    policy_id: str
    context: EvaluationContext
    dry_run: bool
    def __init__(self, policy_id: _Optional[str] = ..., context: _Optional[_Union[EvaluationContext, _Mapping]] = ..., dry_run: bool = ...) -> None: ...

class EvaluatePolicyResponse(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: EvaluationResult
    def __init__(self, result: _Optional[_Union[EvaluationResult, _Mapping]] = ...) -> None: ...

class EvaluatePoliciesRequest(_message.Message):
    __slots__ = ("policy_ids", "context", "stop_on_deny", "dry_run")
    POLICY_IDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    STOP_ON_DENY_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    policy_ids: _containers.RepeatedScalarFieldContainer[str]
    context: EvaluationContext
    stop_on_deny: bool
    dry_run: bool
    def __init__(self, policy_ids: _Optional[_Iterable[str]] = ..., context: _Optional[_Union[EvaluationContext, _Mapping]] = ..., stop_on_deny: bool = ..., dry_run: bool = ...) -> None: ...

class EvaluatePoliciesResponse(_message.Message):
    __slots__ = ("results", "final_decision", "actions")
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    FINAL_DECISION_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[EvaluationResult]
    final_decision: EvaluationDecision
    actions: _containers.RepeatedCompositeFieldContainer[PolicyAction]
    def __init__(self, results: _Optional[_Iterable[_Union[EvaluationResult, _Mapping]]] = ..., final_decision: _Optional[_Union[EvaluationDecision, str]] = ..., actions: _Optional[_Iterable[_Union[PolicyAction, _Mapping]]] = ...) -> None: ...

class GetEvaluationHistoryRequest(_message.Message):
    __slots__ = ("policy_id", "start_time", "end_time", "decision", "page_size", "page_token")
    POLICY_ID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    policy_id: str
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    decision: EvaluationDecision
    page_size: int
    page_token: str
    def __init__(self, policy_id: _Optional[str] = ..., start_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., decision: _Optional[_Union[EvaluationDecision, str]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class GetEvaluationHistoryResponse(_message.Message):
    __slots__ = ("evaluations", "next_page_token", "total_count")
    EVALUATIONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    evaluations: _containers.RepeatedCompositeFieldContainer[EvaluationResult]
    next_page_token: str
    total_count: int
    def __init__(self, evaluations: _Optional[_Iterable[_Union[EvaluationResult, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...
