"""Typed models used across the FinanFut SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field, UUID4

ModelT = TypeVar("ModelT", bound=BaseModel)
BASE_MODEL_CONFIG = ConfigDict(
    from_attributes=True, populate_by_name=True, extra="allow"
)
BASE_MODEL_CONFIG_KWARGS = dict(BASE_MODEL_CONFIG)


class SDKBaseModel(BaseModel):
    model_config = ConfigDict(**BASE_MODEL_CONFIG_KWARGS)


class TokenUsage(SDKBaseModel):
    """Token usage summary for an interaction."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ActionResult(SDKBaseModel):
    """Represents an action returned by FinanFut agents."""

    name: str | None = None
    payload: dict[str, Any | None] = Field(default_factory=dict)


class Answer(SDKBaseModel):
    """Structured answer payload returned by FinanFut Intelligence."""

    content: str | None = None


class IntentResult(SDKBaseModel):
    """Result content for an intent execution."""

    content: str | None = None


class IntentResponse(SDKBaseModel):
    """Metadata for a resolved intent inside ``metadata.intent_responses``."""

    intent: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: IntentResult | None = None
    raw_model_output: Any | None = None


class InteractionResponse(SDKBaseModel):
    """High-level response returned by `/api/v1/interact`."""

    answer: Answer | str | None = None
    actions: list[ActionResult] = Field(default_factory=list)
    tokens: TokenUsage | None = None
    tokens_used: int | None = None
    sandbox: bool | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    intent_responses: list[IntentResponse] = Field(default_factory=list)
    agent_id: str | None = None
    context_used: Any | None = None
    application_agent_id: str | None = None
    application_agent_intent_id: str | None = None
    intent_id: str | None = None
    intent_name: str | None = None
    intent_label: str | None = None
    available_intent_names: list[str] = Field(default_factory=list)
    available_intents: list[Intent] = Field(default_factory=list)
    raw_model_output: Any | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class TabularPreview(SDKBaseModel):
    """Preview rows returned after uploading a CSV."""

    columns: list[str] = Field(default_factory=list)
    rows_sample: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int | None = None
    detected_types: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict, alias="_meta")


class TransientCSVUpload(SDKBaseModel):
    """Transient CSV payload used for previews and downstream transforms."""

    file_name: str | None = None
    mime_type: str | None = None
    content_base64: str | None = Field(default=None, repr=False)
    preview: TabularPreview | None = None


class DataTransformResponse(SDKBaseModel):
    """Structured response returned by the data import transformer."""

    answer: Any | None = None
    response: Any | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[Any] = Field(default_factory=list, alias="_errors")
    meta: dict[str, Any] = Field(default_factory=dict, alias="_meta")
    request_id: str | None = None
    tokens_used: int | None = None
    sandbox: bool | None = None

    @classmethod
    def from_public_api_payload(cls, payload: Mapping[str, Any]) -> "DataTransformResponse":
        """Normalize the public API payload into the SDK response."""

        raw_response: Any = payload.get("response") or payload.get("answer") or payload
        meta = payload.get("meta") if isinstance(payload.get("meta"), Mapping) else {}
        request_id = None
        if isinstance(meta, Mapping):
            request_id = meta.get("request_id") or meta.get("requestId")
        items: list[dict[str, Any]] = []
        errors: list[Any] = []
        result_meta: dict[str, Any] = {}
        if isinstance(raw_response, Mapping):
            items_payload = raw_response.get("items") or raw_response.get("rows")
            if isinstance(items_payload, list):
                items = [item for item in items_payload if isinstance(item, Mapping)]
            errors_payload = raw_response.get("_errors") or raw_response.get("errors")
            if isinstance(errors_payload, list):
                errors = list(errors_payload)
            meta_candidate = raw_response.get("_meta") or raw_response.get("meta")
            if isinstance(meta_candidate, Mapping):
                result_meta = dict(meta_candidate)
        return cls(
            answer=payload.get("answer"),
            response=raw_response,
            items=items,
            errors=errors,
            meta=result_meta,
            request_id=str(request_id) if request_id is not None else None,
            tokens_used=payload.get("tokens_used"),
            sandbox=payload.get("sandbox"),
        )


def build_interaction_response(
    data: Mapping[str, Any], meta: Mapping[str, Any | None] | None = None
) -> InteractionResponse:
    """Create an :class:`InteractionResponse` from backend payloads."""

    safe_meta = dict(meta or {})
    if isinstance(data, Mapping):
        safe_data: dict[str, Any] = dict(data)
    else:
        safe_data = {"answer": data}

    nested_response: Mapping[str, Any | None] | None = None
    for key in ("response", "result"):
        candidate = safe_data.get(key)
        if isinstance(candidate, Mapping):
            nested_response = candidate
            break

    merged_data: dict[str, Any] = dict(safe_data)
    if isinstance(nested_response, Mapping):
        for key, value in nested_response.items():
            if value is None and key in merged_data and merged_data[key] is not None:
                continue
            if value is not None or key not in merged_data:
                merged_data[key] = value

    def _first_not_none(*values: Any) -> Any:
        for value in values:
            if value is not None:
                return value
        return None

    def _first_mapping(*values: Any) -> Mapping[str, Any | None]:
        for value in values:
            if isinstance(value, Mapping):
                return value
        return None

    def _normalize_answer(raw_answer: Any) -> Any:
        if isinstance(raw_answer, Mapping):
            return _model_validate(Answer, raw_answer)
        if raw_answer is None:
            return None
        return _model_validate(Answer, {"content": str(raw_answer)})

    token_payload = _first_not_none(
        merged_data.get("tokens"),
        merged_data.get("token_usage"),
        merged_data.get("tokens_used"),
        safe_meta.get("token_usage"),
        safe_meta.get("tokens"),
        merged_data.get("metadata", {}).get("token_usage")
        if isinstance(merged_data.get("metadata"), Mapping)
        else None,
    )

    request_identifier = _first_not_none(
        merged_data.get("request_id"),
        merged_data.get("requestId"),
        safe_data.get("request_id"),
        safe_data.get("requestId"),
        safe_meta.get("request_id"),
        safe_meta.get("requestId"),
    )

    intent_payload = _first_mapping(
        merged_data.get("intent"),
        safe_data.get("intent"),
        nested_response.get("intent") if isinstance(nested_response, Mapping) else None,
    )
    normalized_intent = normalize_intent_payload(intent_payload) if intent_payload else None

    actions_payload = merged_data.get("actions") or []
    if isinstance(actions_payload, Mapping):
        actions_payload = [actions_payload]
    elif not isinstance(actions_payload, list):
        actions_payload = []

    metadata_payload = _first_mapping(
        merged_data.get("metadata"),
        merged_data.get("meta"),
        safe_meta.get("metadata"),
        safe_meta.get("meta"),
    )
    metadata_payload = metadata_payload if metadata_payload is not None else {}

    available_intents_payload = _first_not_none(
        merged_data.get("available_intents"),
        safe_meta.get("available_intents"),
    )
    available_intents: list[Intent] = []
    if isinstance(available_intents_payload, Mapping):
        available_intents_payload = [available_intents_payload]
    if isinstance(available_intents_payload, list):
        for item in available_intents_payload:
            normalized = normalize_intent_payload(item)
            if normalized is None:
                continue
            available_intents.append(_model_validate(Intent, normalized))

    available_intent_names = _first_not_none(
        merged_data.get("available_intent_names"),
        safe_meta.get("available_intent_names"),
    )
    intent_responses_payload = metadata_payload.get("intent_responses") if isinstance(metadata_payload, Mapping) else None
    intent_responses: list[IntentResponse] = []
    if isinstance(intent_responses_payload, list):
        for item in intent_responses_payload:
            if not isinstance(item, Mapping):
                continue
            intent_responses.append(_model_validate(IntentResponse, item))

    if not available_intent_names:
        names_from_intent_responses = [
            intent_response.intent
            for intent_response in intent_responses
            if intent_response.intent
        ]
        available_intent_names = names_from_intent_responses or [
            intent.name for intent in available_intents if intent.name
        ]

    token_usage_payload = _coerce_token_usage(token_payload)

    tokens_used = None
    if isinstance(token_payload, (int, float)):
        tokens_used = int(token_payload)
    elif isinstance(token_payload, Mapping):
        tokens_used = token_payload.get("total_tokens") or token_payload.get("tokens_used")

    intent_id = _first_not_none(
        merged_data.get("intent_id"),
        merged_data.get("intentId"),
        (normalized_intent or {}).get("intent_id"),
        (normalized_intent or {}).get("id"),
        safe_meta.get("intent_id"),
        safe_meta.get("intentId"),
    )
    application_agent_intent_id = _first_not_none(
        merged_data.get("application_agent_intent_id"),
        merged_data.get("applicationAgentIntentId"),
        (normalized_intent or {}).get("application_agent_intent_id"),
        safe_meta.get("application_agent_intent_id"),
        safe_meta.get("applicationAgentIntentId"),
    )

    application_agent_id = _first_not_none(
        merged_data.get("application_agent_id"),
        merged_data.get("applicationAgentId"),
        (normalized_intent or {}).get("application_agent_id"),
        safe_meta.get("application_agent_id"),
    )

    agent_id = _first_not_none(
        merged_data.get("agent_id"),
        merged_data.get("agentId"),
        safe_meta.get("agent_id"),
        safe_meta.get("agentId"),
    )

    raw_model_output = _first_not_none(
        merged_data.get("raw_model_output"),
        merged_data.get("raw_output"),
        next((item.raw_model_output for item in intent_responses if item.raw_model_output is not None), None),
    )

    return _model_validate(
        InteractionResponse,
        {
            "answer": _normalize_answer(
                _first_not_none(merged_data.get("answer"), safe_data.get("answer"))
            ),
            "actions": actions_payload,
            "tokens": token_usage_payload,
            "tokens_used": tokens_used,
            "sandbox": bool(merged_data.get("sandbox", safe_meta.get("sandbox", False))),
            "request_id": request_identifier,
            "metadata": metadata_payload,
            "intent_responses": intent_responses,
            "agent_id": agent_id,
            "context_used": merged_data.get("context_used")
            or merged_data.get("context"),
            "application_agent_id": application_agent_id,
            "intent_id": intent_id,
            "intent_name": _first_not_none(
                merged_data.get("intent_name"),
                merged_data.get("intentName"),
                (normalized_intent or {}).get("name"),
            ),
            "intent_label": _first_not_none(
                merged_data.get("intent_label"),
                merged_data.get("intentLabel"),
                (normalized_intent or {}).get("label"),
            ),
            "application_agent_intent_id": application_agent_intent_id,
            "available_intent_names": available_intent_names or [],
            "available_intents": available_intents,
            "raw_model_output": raw_model_output,
            "meta": safe_meta,
            "raw": merged_data,
        },
    )


def normalize_intent_payload(item: Any) -> dict[str, Any | None]:
    """Flatten nested intent payloads while preserving metadata values.

    Backend responses sometimes wrap the real intent metadata under an ``intent``
    key. This helper ensures ``name``, ``label`` and identifier fields survive
    the merge even when outer keys are ``null``.
    """

    if not isinstance(item, Mapping):
        return None

    payload: dict[str, Any] = dict(item)
    nested_intent = payload.pop("intent", None)

    merged: dict[str, Any] = {}

    def _set_if_present(key: str, value: Any) -> None:
        if value is not None and key not in merged:
            merged[key] = value

    if isinstance(nested_intent, Mapping):
        for key, value in nested_intent.items():
            if value is not None:
                merged[key] = value

    link_id = (
        payload.get("id")
        or payload.get("application_agent_intent_id")
        or payload.get("applicationAgentIntentId")
    )

    intent_id = (
        (nested_intent.get("intent_id") if isinstance(nested_intent, Mapping) else None)
        or (nested_intent.get("id") if isinstance(nested_intent, Mapping) else None)
        or payload.get("intent_id")
        or payload.get("intentId")
        or payload.get("id")
        or link_id
    )
    _set_if_present("intent_id", intent_id)
    _set_if_present("id", intent_id)

    application_agent_intent_id = (
        (nested_intent.get("application_agent_intent_id") if isinstance(nested_intent, Mapping) else None)
        or payload.get("application_agent_intent_id")
        or payload.get("applicationAgentIntentId")
        or link_id
    )
    _set_if_present("application_agent_intent_id", application_agent_intent_id)

    application_agent_id = (
        (nested_intent.get("application_agent_id") if isinstance(nested_intent, Mapping) else None)
        or payload.get("application_agent_id")
        or payload.get("applicationAgentId")
    )
    _set_if_present("application_agent_id", application_agent_id)

    for source in (payload, nested_intent if isinstance(nested_intent, Mapping) else {}):
        for key, value in source.items():
            if key in {
                "intent_id",
                "intentId",
                "id",
                "application_agent_intent_id",
                "applicationAgentIntentId",
                "intent",
            }:
                continue
            existing = merged.get(key)
            if value is None and existing is not None:
                continue
            if existing is None or value is not None:
                merged[key] = value

    return merged


def _model_validate(model: Type[ModelT], data: Any) -> ModelT:
    """Validate payloads using a Pydantic model."""

    return model.model_validate(data)


def _coerce_token_usage(payload: Any) -> TokenUsage | None:
    if payload is None:
        return None
    if isinstance(payload, Mapping):
        return _model_validate(TokenUsage, payload)
    if isinstance(payload, (int, float)):
        return _model_validate(TokenUsage, {"total_tokens": int(payload)})
    return None


class MemoryRecord(SDKBaseModel):
    """Represents a memory entry."""

    record_id: str | None = None
    content: str
    metadata: dict[str, Any] = Field(
        default_factory=dict, alias="metadata_"
    )


class MemorySettings(SDKBaseModel):
    """Configuration for memory storage."""

    enabled: bool
    retention_days: int | None = None
    max_records: int | None = None


class MemoryQueryResponse(SDKBaseModel):
    """Response payload returned by memory query endpoints."""

    records: list[MemoryRecord] = Field(default_factory=list)
    total: int | None = None


class BillingUsage(SDKBaseModel):
    """Current usage metrics."""

    period: str
    tokens_used: int
    cost: float


class BillingPlan(SDKBaseModel):
    """Generic billing plan descriptor."""

    plan_id: str | None = None
    name: str | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict, alias="metadata_"
    )


class TransactionRecord(SDKBaseModel):
    """Billing transaction entry."""

    transaction_id: str
    amount: float
    currency: str
    created_at: str
    description: str | None = None


class Agent(SDKBaseModel):
    """Agent metadata."""

    agent_id: str
    name: str
    description: str | None = None
    ai_model_id: str | None = None


class Intent(SDKBaseModel):
    """Intent metadata compatible with backend responses."""

    intent_id: str | None = Field(None, alias="id")
    application_agent_intent_id: str | None = None
    application_agent_id: str | None = None
    name: str | None = None
    label: str | None = None
    slug: str | None = None
    code: str | None = None
    description: str | None = None
    enabled: bool | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    default_parameters: dict[str, Any] = Field(default_factory=dict)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


InteractionResponse.model_rebuild()



class Application(SDKBaseModel):
    """Application metadata."""

    application_id: str
    name: str
    status: str


class ApplicationAgent(SDKBaseModel):
    """Application-scoped agent metadata."""

    application_agent_id: UUID4
    application_id: UUID4
    agent_id: UUID4 | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApplicationAgentList(SDKBaseModel):
    """Paginated application agent response payload."""

    items: list[ApplicationAgent] = Field(default_factory=list)
    total: int = 0
    limit: int = 0
    offset: int = 0


class AccessToken(SDKBaseModel):
    """Metadata describing a rotating access token."""

    token_id: str
    description: str | None = None
    created_at: str | None = None
    last_used_at: str | None = None


class AccessTokenCreateRequest(SDKBaseModel):
    """Request payload for creating a new access token."""

    description: str | None = None
    scopes: list[str] = Field(default_factory=list)


class AccessTokenListResponse(SDKBaseModel):
    """Paginated collection of access tokens."""

    items: list[AccessToken] = Field(default_factory=list)
    total: int | None = None


class DocumentFile(SDKBaseModel):
    """Metadata about an uploaded document."""

    id: UUID4
    file_name: str
    mime_type: str | None = None
    status: str
    chunk_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    document_type_id: UUID4 | None = None
    document_type: str | None = None
    document_type_label: str | None = None
    document_type_version: int | None = None
    document_type_strict_validation: bool | None = None
    document_type_embedding_enabled: bool | None = None
    document_type_chunking_strategy: dict[str, Any | None] = None
    latest_processing_id: UUID4 | None = None
    processing_summary: str | None = None
    processing_confidence: float | None = None
    processing_version: int = 0
    classification_metadata: dict[str, Any | None] = None


class DocumentDetail(DocumentFile):
    """Full document payload returned after upload or lookup."""

    text_content: str = ""
    error: str | None = None
    content_base64: str | None = Field(default=None, repr=False)


class DocumentAnswer(SDKBaseModel):
    """Answer payload returned by the document QA endpoint."""

    answer: str
    request_id: UUID4 | None = None


class DocumentType(SDKBaseModel):
    """Descriptor for a pipeline document type."""

    id: UUID4
    name: str
    label: str | None = None
    description: str | None = None
    expected_format: str | None = None
    parse_strategy: str | None = None
    output_contract: dict[str, Any | None] = None
    metadata: dict[str, Any] = Field(
        default_factory=dict, alias="metadata_"
    )
    version: int = 1
    strict_validation: bool | None = None
    embedding_enabled: bool | None = None
    chunking_strategy: dict[str, Any] = Field(default_factory=dict)
    is_active: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentTypeDetail(DocumentType):
    """Detailed descriptor for a document type."""


class ValidationReport(SDKBaseModel):
    """Validation status after running the processing pipeline."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DeclarativeAction(SDKBaseModel):
    """Action emitted by the pipeline for downstream automation."""

    id: UUID4
    processing_record_id: UUID4
    document_id: UUID4
    application_id: UUID4
    name: str
    handler: str
    endpoint: str | None = None
    description: str | None = None
    version: int
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(
        default_factory=dict, alias="metadata_"
    )
    processed_by_agent_id: UUID4 | None = None
    processed_by_agent_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentProcessingRecord(SDKBaseModel):
    """One processing run executed for a document."""

    id: UUID4
    document_id: UUID4
    application_id: UUID4
    document_type_id: UUID4 | None = None
    document_type_version: int | None = None
    status: str
    summary: str | None = None
    confidence: float | None = None
    version: int
    processing_version: int = 1
    metadata: dict[str, Any] = Field(
        default_factory=dict, alias="metadata_"
    )
    parsed_content: dict[str, Any | None] = None
    raw_response: dict[str, Any | None] = None
    error: str | None = None
    processor_agent_id: UUID4 | None = None
    processor_agent_name: str | None = None
    execution_time_ms: int | None = None
    tokens_used: int = 0
    parser_version: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentProcessingResponse(SDKBaseModel):
    """Full payload returned after requesting document processing."""

    record: DocumentProcessingRecord
    parsed_content: dict[str, Any | None] = None
    validation: ValidationReport
    dry_run: bool = False
    action: DeclarativeAction | None = None


class DocumentRunsResponse(SDKBaseModel):
    """Historical processing runs."""

    runs: list[DocumentProcessingRecord] = Field(default_factory=list)


class DocumentParsedResponse(SDKBaseModel):
    """Latest parsed content and associated action."""

    record: DocumentProcessingRecord | None = None
    action: DeclarativeAction | None = None


class ContextDocumentLink(SDKBaseModel):
    """Context document relationship metadata."""

    document_id: UUID4
    position: int | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict, alias="metadata_"
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ContextSummary(SDKBaseModel):
    """High-level summary returned when listing contexts."""

    id: UUID4
    application_id: UUID4
    name: str
    description: str | None = None
    status: str
    metadata: dict[str, Any] = Field(
        default_factory=dict, alias="metadata_"
    )
    document_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ContextDetail(ContextSummary):
    """Context detail including linked documents."""

    documents: list[ContextDocumentLink] = Field(
        default_factory=list, alias="document_links"
    )


class ContextList(SDKBaseModel):
    """Paginated response returned by the contexts API."""

    items: list[ContextSummary] = Field(default_factory=list)
    total: int = 0
    limit: int = 0
    offset: int = 0


class ContextSessionSummary(SDKBaseModel):
    """Summary of a context session."""

    id: UUID4
    name: str
    status: str
    context_id: UUID4 | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ContextSessionMessage(SDKBaseModel):
    """Message captured inside a context session."""

    id: UUID4
    session_id: UUID4
    context_id: UUID4 | None = None
    agent_name: str
    intent: str | None = None
    role: str
    query: str | None = None
    answer: str | None = None
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ContextSessionDetail(ContextSessionSummary):
    """Detailed session with metadata and messages."""

    metadata: dict[str, Any] = Field(default_factory=dict)
    messages: list[ContextSessionMessage] = Field(default_factory=list)


class ContextSessionList(SDKBaseModel):
    """Response returned when listing context sessions."""

    items: list[ContextSessionSummary] = Field(default_factory=list)
