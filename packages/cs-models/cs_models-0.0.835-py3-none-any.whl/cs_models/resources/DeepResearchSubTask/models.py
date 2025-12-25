"""Models for Deep Research SubTasks - Individual research agents."""
import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship

from ...database import Base


class SubTaskStatusEnum(enum.Enum):
    """Status enum for deep research subtasks."""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class SubTaskTypeEnum(enum.Enum):
    """Type enum for research dimensions."""
    EFFICACY = "EFFICACY"
    SAFETY = "SAFETY"
    PRICING = "PRICING"
    COMPETITIVE = "COMPETITIVE"
    PIPELINE = "PIPELINE"
    REGULATORY = "REGULATORY"
    COMMERCIAL = "COMMERCIAL"
    CLINICAL_TRIAL = "CLINICAL_TRIAL"
    MECHANISM = "MECHANISM"
    EPIDEMIOLOGY = "EPIDEMIOLOGY"
    MARKET_ACCESS = "MARKET_ACCESS"
    KOL = "KOL"
    CUSTOM = "CUSTOM"


class DeepResearchSubTaskModel(Base):
    """
    Model for Deep Research SubTasks.

    Each subtask represents an independent research agent that executes
    with a fresh context window. Subtasks do not communicate with each
    other - all coordination flows through the main orchestrator.
    """

    __tablename__ = "deep_research_subtasks"

    id = Column(Integer, primary_key=True)

    # Parent session
    session_id = Column(
        Integer,
        ForeignKey("deep_research_sessions.id"),
        nullable=False,
    )

    # Task identification
    sequence_number = Column(Integer, nullable=False, default=0)
    task_type = Column(
        "task_type",
        Enum(SubTaskTypeEnum),
        default=SubTaskTypeEnum.CUSTOM,
        nullable=False,
    )
    task_label = Column(String(256), nullable=True)

    # Task specification (JSON)
    specification = Column(Text, nullable=False)  # JSON with focus_question, entities, etc.
    focus_question = Column(Text, nullable=True)  # Denormalized for quick access
    entities = Column(Text, nullable=True)  # JSON array of entity objects
    search_scope = Column(Text, nullable=True)  # JSON array: ["PUBLICATION", "CLINICAL_TRIAL"]
    expected_output_format = Column(String(50), nullable=True)  # structured, narrative, table_row
    time_range_start = Column(DateTime, nullable=True)
    time_range_end = Column(DateTime, nullable=True)

    # Execution status
    status = Column(
        "status",
        Enum(SubTaskStatusEnum),
        default=SubTaskStatusEnum.PENDING,
        nullable=False,
    )
    lambda_request_id = Column(String(256), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Dependencies (for sequential tasks)
    depends_on = Column(Text, nullable=True)  # JSON array of subtask IDs
    priority = Column(Integer, nullable=True, default=1)

    # Results
    result_s3_key = Column(String(512), nullable=True)
    result_summary = Column(Text, nullable=True)  # Brief summary of findings
    citations_count = Column(Integer, nullable=True, default=0)
    documents_analyzed = Column(Integer, nullable=True, default=0)

    # Quality metrics
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0
    relevance_score = Column(Float, nullable=True)  # 0.0 - 1.0
    coverage_score = Column(Float, nullable=True)  # How well the question was answered

    # Execution metrics
    execution_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    search_queries_count = Column(Integer, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    retry_count = Column(Integer, nullable=True, default=0)

    # Soft delete and timestamps
    is_deleted = Column(Boolean, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.utcnow(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    # ORM Relationships
    session = relationship(
        "DeepResearchSessionModel",
        back_populates="subtasks",
    )

