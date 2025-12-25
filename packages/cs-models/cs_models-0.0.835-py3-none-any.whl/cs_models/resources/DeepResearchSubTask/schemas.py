"""Schemas for Deep Research SubTasks."""
from marshmallow import Schema, fields, validate

from .models import SubTaskStatusEnum, SubTaskTypeEnum


class DeepResearchSubTaskResourceSchema(Schema):
    """Schema for DeepResearchSubTaskModel."""

    not_blank = validate.Length(min=1, error="Field cannot be blank")

    id = fields.Integer(dump_only=True)
    session_id = fields.Integer(required=True)

    # Task identification
    sequence_number = fields.Integer(required=True)
    task_type = fields.Enum(SubTaskTypeEnum, by_value=True)
    task_label = fields.String(allow_none=True)

    # Task specification
    specification = fields.String(required=True)
    focus_question = fields.String(allow_none=True)
    entities = fields.String(allow_none=True)
    search_scope = fields.String(allow_none=True)
    expected_output_format = fields.String(allow_none=True)
    time_range_start = fields.DateTime(allow_none=True)
    time_range_end = fields.DateTime(allow_none=True)

    # Execution status
    status = fields.Enum(SubTaskStatusEnum, by_value=True)
    lambda_request_id = fields.String(allow_none=True)
    started_at = fields.DateTime(allow_none=True)
    completed_at = fields.DateTime(allow_none=True)

    # Dependencies
    depends_on = fields.String(allow_none=True)
    priority = fields.Integer(allow_none=True)

    # Results
    result_s3_key = fields.String(allow_none=True)
    result_summary = fields.String(allow_none=True)
    citations_count = fields.Integer(allow_none=True)
    documents_analyzed = fields.Integer(allow_none=True)

    # Quality metrics
    confidence_score = fields.Float(allow_none=True)
    relevance_score = fields.Float(allow_none=True)
    coverage_score = fields.Float(allow_none=True)

    # Execution metrics
    execution_time_ms = fields.Integer(allow_none=True)
    tokens_used = fields.Integer(allow_none=True)
    search_queries_count = fields.Integer(allow_none=True)

    # Error handling
    error_message = fields.String(allow_none=True)
    error_type = fields.String(allow_none=True)
    retry_count = fields.Integer(allow_none=True)

    # Timestamps
    is_deleted = fields.Boolean(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class DeepResearchSubTaskSpecSchema(Schema):
    """Schema for subtask specification object."""

    focus_question = fields.String(required=True)
    entities = fields.List(fields.Dict(), allow_none=True)
    search_scope = fields.List(fields.String(), allow_none=True)
    output_format = fields.String(allow_none=True)
    expected_fields = fields.List(fields.String(), allow_none=True)
    max_documents = fields.Integer(allow_none=True)
    time_range = fields.List(fields.String(), allow_none=True)
    retrieval_hints = fields.Dict(allow_none=True)


class DeepResearchSubTaskCreateSchema(Schema):
    """Schema for creating a subtask."""

    session_id = fields.Integer(required=True)
    sequence_number = fields.Integer(required=True)
    task_type = fields.Enum(SubTaskTypeEnum, by_value=True, required=True)
    task_label = fields.String(allow_none=True)
    specification = fields.Nested(DeepResearchSubTaskSpecSchema, required=True)
    depends_on = fields.List(fields.Integer(), allow_none=True)
    priority = fields.Integer(allow_none=True)
