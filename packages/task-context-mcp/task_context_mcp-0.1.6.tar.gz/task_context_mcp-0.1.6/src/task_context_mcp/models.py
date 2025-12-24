from typing import List, Optional

from pydantic import BaseModel, Field


# Pydantic models for tool parameters
class TaskContextCreateRequest(BaseModel):
    """Request model for creating a new task context."""

    summary: str = Field(
        ...,
        description="Summary of the task context (task type) - max 200 chars",
    )
    description: str = Field(
        ...,
        description="Detailed description of the task context - max 1000 chars",
    )


class ArtifactCreateRequest(BaseModel):
    """Request model for creating an artifact."""

    task_context_id: str = Field(
        ..., description="ID of the task context this artifact belongs to"
    )
    artifact_type: str = Field(
        ..., description="Type of artifact: 'practice', 'rule', 'prompt', 'result'"
    )
    summary: str = Field(
        ...,
        description="Summary of the artifact - max 200 chars",
    )
    content: str = Field(
        ...,
        description="Full content of the artifact - max 4000 chars",
    )


class ArtifactUpdateRequest(BaseModel):
    """Request model for updating an artifact."""

    artifact_id: str = Field(..., description="ID of the artifact to update")
    summary: Optional[str] = Field(
        None,
        description="New summary for the artifact - max 200 chars",
    )
    content: Optional[str] = Field(
        None,
        description="New content for the artifact - max 4000 chars",
    )


class ArtifactArchiveRequest(BaseModel):
    """Request model for archiving an artifact."""

    artifact_id: str = Field(..., description="ID of the artifact to archive")
    reason: Optional[str] = Field(None, description="Reason for archiving the artifact")


class GetArtifactsRequest(BaseModel):
    """Request model for getting artifacts for a task context."""

    task_context_id: str = Field(..., description="ID of the task context")
    artifact_types: Optional[List[str]] = Field(
        None, description="Types of artifacts to retrieve"
    )
    include_archived: bool = Field(
        False, description="Whether to include archived artifacts"
    )


class SearchArtifactsRequest(BaseModel):
    """Request model for searching artifacts."""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Maximum number of results to return")
