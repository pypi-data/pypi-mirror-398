from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TaskContextStatus(str, Enum):
    """Status of a task context."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ArtifactType(str, Enum):
    """
    Type of artifact stored for a task context.

    - PRACTICE: Best practices and guidelines for executing the task type
    - RULE: Specific rules and constraints to follow
    - PROMPT: Template prompts useful for the task type
    - RESULT: General patterns and learnings from past work (not individual execution results)
    """

    PRACTICE = "practice"
    RULE = "rule"
    PROMPT = "prompt"
    RESULT = "result"


class ArtifactStatus(str, Enum):
    """Status of an artifact."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class TaskContext(Base):
    """
    Represents a reusable task type/category, not an individual task instance.

    Example: "Analyze applicant CV for Python developer" is a TaskContext.
    Individual CV analyses are NOT stored - only the reusable artifacts
    (practices, rules, prompts, learnings) that help with this type of work.
    """

    __tablename__ = "task_contexts"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
        doc="Unique identifier for the task context",
    )
    summary = Column(
        String,
        nullable=False,
        doc="Summary of the task context. Used by agent to identify the task type",
    )
    description = Column(
        Text,
        nullable=False,
        doc="Detailed description of the task context. Used by agent to identify the task type",
    )
    creation_date = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        doc="Timestamp when the task context was created",
    )
    updated_date = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Timestamp when the task context was last updated",
    )
    status = Column(
        String,
        default=TaskContextStatus.ACTIVE.value,
        doc="Current status of the task context",
    )

    # Relationship to artifacts (one task context can have many artifacts of each type)
    artifacts = relationship(
        "Artifact", back_populates="task_context", cascade="all, delete-orphan"
    )


class Artifact(Base):
    """
    Reusable artifact associated with a task context.

    Multiple artifacts of the same type can exist per task context.
    For example, a CV analysis task context might have:
    - 3 practices (general guidelines)
    - 5 rules (specific constraints)
    - 2 prompts (template prompts)
    - 4 results (patterns/learnings from past work)
    """

    __tablename__ = "artifacts"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
        doc="Unique identifier for the artifact",
    )
    summary = Column(
        String,
        nullable=False,
        doc="Summary of the artifact. Used for quick reference",
    )
    content = Column(
        Text,
        nullable=False,
        doc="Full content of the artifact",
    )
    task_context_id = Column(
        String,
        ForeignKey("task_contexts.id"),
        nullable=False,
        doc="Identifier of the associated task context",
    )
    artifact_type = Column(
        String,
        nullable=False,
        doc="Type of the artifact: practice, rule, prompt, result",
    )
    status = Column(
        String,
        default=ArtifactStatus.ACTIVE.value,
        doc="Current status of the artifact",
    )
    archived_at = Column(
        DateTime, nullable=True, doc="Timestamp when the artifact was archived"
    )
    archivation_reason = Column(
        Text, nullable=True, doc="Reason for archiving the artifact"
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        doc="Timestamp when the artifact was created",
    )

    # Relationship to task context
    task_context = relationship("TaskContext", back_populates="artifacts")
