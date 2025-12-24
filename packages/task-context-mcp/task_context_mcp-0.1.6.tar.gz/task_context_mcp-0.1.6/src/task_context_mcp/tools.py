from typing import Annotated, List, Optional

from pydantic import Field

from task_context_mcp.database import db_manager
from task_context_mcp.database.models import ArtifactStatus, ArtifactType
from task_context_mcp.server import mcp

# Default artifact types to retrieve (excludes RESULT type)
DEFAULT_ARTIFACT_TYPES = [
    ArtifactType.PRACTICE,
    ArtifactType.RULE,
    ArtifactType.PROMPT,
]


# MCP Tools
@mcp.tool
def get_active_task_contexts() -> str:
    """
    Start here for every task.

    Lists active task contexts (reusable task TYPES, not task instances).

    Next steps:
    - If a context matches: call get_artifacts_for_task_context(task_context_id)
    - If no context matches: call create_task_context(summary, description)
    """
    try:
        task_contexts = db_manager.get_active_task_contexts()

        if not task_contexts:
            return """No active task contexts found.

Next step:
- Call create_task_context(summary, description) to create a new task type.
- Then call create_artifact(...) to add initial rules/practices/prompts before doing work."""

        result = "Active Task Contexts:\n\n"
        for tc in task_contexts:
            result += f"ID: {tc.id}\n"
            result += f"Summary: {tc.summary}\n"
            result += f"Description: {tc.description}\n"
            result += f"Created: {tc.creation_date}\n"
            result += f"Updated: {tc.updated_date}\n"
            result += "---\n"

        result += "\nNext step:\n"
        result += "- If a context matches: call get_artifacts_for_task_context(task_context_id)\n"
        result += "- If none match: call create_task_context(summary, description)\n"

        return result

    except Exception as e:
        return f"Error getting active task contexts: {str(e)}"


@mcp.tool
def create_task_context(
    summary: Annotated[
        str,
        Field(
            description="Summary of the task context (task type) - max 200 chars, English only"
        ),
    ],
    description: Annotated[
        str,
        Field(
            description="Detailed description of the task context - max 1000 chars, English only"
        ),
    ],
) -> str:
    """
    Create a new task context (task type) when no match exists.

    Use for categories (e.g., "CV analysis for Python dev"), not specific instances.

    Constraints:
    - English only
    - summary <= 200 chars
    - description <= 1000 chars

    Next step: create initial guidance with create_artifact() before doing task work.
    """
    try:
        # Validation is handled by Pydantic models in the MCP layer
        task_context = db_manager.create_task_context(
            summary=summary, description=description
        )

        return f"""Task context created:
ID: {task_context.id}
Summary: {task_context.summary}
Description: {task_context.description}

    Next steps:
    - Call create_artifact(...) to add initial rules/practices/prompts before doing work.
    - During work: create/update/archive artifacts as you learn.
    - Before finishing: call reflect_and_update_artifacts(task_context_id, learnings)."""

    except Exception as e:
        return f"Error creating task context: {str(e)}"


@mcp.tool
def get_artifacts_for_task_context(
    task_context_id: Annotated[str, Field(description="ID of the task context")],
    artifact_types: Annotated[
        Optional[List[str]],
        Field(
            description="Types of artifacts to retrieve (optional, defaults to all except 'result')"
        ),
    ] = None,
    include_archived: Annotated[
        bool, Field(description="Whether to include archived artifacts")
    ] = False,
) -> str:
    """
    Load artifacts for a task context.

    Call this after you select or create a task context and before doing work.
    Re-call when you start a new phase or need to confirm guidance.

    Notes:
    - Defaults to practice/rule/prompt (excludes result)
    - Set include_archived=True only when you need historical context
    """
    try:
        # Convert string types to ArtifactType enums
        # Default to all types except RESULT
        if artifact_types is None:
            artifact_type_enums = DEFAULT_ARTIFACT_TYPES
        else:
            try:
                artifact_type_enums = [ArtifactType(t) for t in artifact_types]
            except ValueError as e:
                return f"Invalid artifact type: {str(e)}. Must be one of: {[t.value for t in ArtifactType]}"

        status = None if include_archived else ArtifactStatus.ACTIVE

        artifacts = db_manager.get_artifacts_for_task_context(
            task_context_id=task_context_id,
            artifact_types=artifact_type_enums,
            status=status,
        )

        if not artifacts:
            status_msg = " (including archived)" if include_archived else ""
            return f"""No artifacts found for task context {task_context_id}{status_msg}.

Next step:
- Call create_artifact(...) to add initial rules/practices/prompts before doing work."""

        result = f"Artifacts for task context {task_context_id}:\n\n"
        for artifact in artifacts:
            result += f"ID: {artifact.id}\n"
            result += f"Type: {artifact.artifact_type}\n"
            result += f"Summary: {artifact.summary}\n"
            result += f"Content:\n{artifact.content}\n"
            result += f"Status: {artifact.status}\n"
            if artifact.archived_at is not None:
                result += f"Archived At: {artifact.archived_at}\n"
                result += f"Archive Reason: {artifact.archivation_reason}\n"
            result += f"Created: {artifact.created_at}\n"
            result += "---\n"

        result += "\nNext steps:\n"
        result += "- Use these artifacts to guide execution.\n"
        result += "- If you learn something new: create_artifact(...) immediately.\n"
        result += "- If guidance is wrong/incomplete: update_artifact(...) or archive_artifact(...).\n"
        result += "- Before finishing: reflect_and_update_artifacts(task_context_id, learnings).\n"

        return result

    except Exception as e:
        return f"Error getting artifacts for task context: {str(e)}"


@mcp.tool
def create_artifact(
    task_context_id: Annotated[
        str, Field(description="ID of the task context this artifact belongs to")
    ],
    artifact_type: Annotated[
        str,
        Field(description="Type of artifact: 'practice', 'rule', 'prompt', 'result'"),
    ],
    summary: Annotated[
        str,
        Field(description="Summary of the artifact - max 200 chars, English only"),
    ],
    content: Annotated[
        str,
        Field(
            description="Full content of the artifact - max 4000 chars, English only"
        ),
    ],
) -> str:
    """
    Create a new artifact to capture reusable guidance.

    Create immediately when you discover a pattern, constraint, mistake, or useful template.
    If similar guidance might already exist, call search_artifacts() first; prefer update_artifact() over near-duplicates.

    Constraints:
    - English only
    - summary <= 200 chars
    - content <= 4000 chars
    - No PII, no task-instance specifics; focus on WHAT/WHY

    Types: practice (guidelines), rule (constraints), prompt (templates), result (generalizable learnings).
    """
    try:
        # Validate artifact_type
        if artifact_type not in [t.value for t in ArtifactType]:
            return f"Invalid artifact type: {artifact_type}. Must be one of: {[t.value for t in ArtifactType]}"

        # Validation for length and language is handled by Pydantic models in the MCP layer

        artifact = db_manager.create_artifact(
            task_context_id=task_context_id,
            artifact_type=ArtifactType(artifact_type),
            summary=summary,
            content=content,
        )

        return f"""Artifact created:
ID: {artifact.id}
Type: {artifact.artifact_type}
Summary: {artifact.summary}

    Next steps:
    - Continue work using this guidance.
    - Before finishing: call reflect_and_update_artifacts(task_context_id, learnings)."""

    except Exception as e:
        return f"Error creating artifact: {str(e)}"


@mcp.tool
def update_artifact(
    artifact_id: Annotated[str, Field(description="ID of the artifact to update")],
    summary: Annotated[
        Optional[str],
        Field(description="New summary for the artifact - max 200 chars, English only"),
    ] = None,
    content: Annotated[
        Optional[str],
        Field(
            description="New content for the artifact - max 4000 chars, English only"
        ),
    ] = None,
) -> str:
    """
    Update an artifact when existing guidance is incomplete, wrong, or needs refinement.

    Use immediately when you learn something better or user feedback indicates a correction.
    Prefer updating over creating duplicates.

    Constraints:
    - English only
    - summary <= 200 chars
    - content <= 4000 chars
    - No PII, no task-instance specifics; focus on WHAT/WHY

    Provide summary and/or content.
    """
    try:
        if summary is None and content is None:
            return "Error: At least one of 'summary' or 'content' must be provided."

        artifact = db_manager.update_artifact(
            artifact_id=artifact_id, summary=summary, content=content
        )

        if artifact:
            return f"""Artifact updated:
ID: {artifact.id}
Summary: {artifact.summary}

Next steps:
- Continue work with the updated guidance.
- Before finishing: reflect_and_update_artifacts(task_context_id, learnings)."""
        else:
            return f"Artifact not found: {artifact_id}"

    except Exception as e:
        return f"Error updating artifact: {str(e)}"


@mcp.tool
def archive_artifact(
    artifact_id: Annotated[str, Field(description="ID of the artifact to archive")],
    reason: Annotated[
        Optional[str],
        Field(description="Reason for archiving the artifact (recommended)"),
    ] = None,
) -> str:
    """
    Archive an artifact that is incorrect, misleading, or outdated.

    Prefer creating a replacement first, then archive the old artifact.
    Provide a reason when possible.
    """
    try:
        artifact = db_manager.archive_artifact(artifact_id=artifact_id, reason=reason)

        if artifact:
            return f"""Artifact archived:
ID: {artifact.id}
Reason: {artifact.archivation_reason}

Next steps:
- If you still need guidance for this case, create a replacement artifact.
- Before finishing: reflect_and_update_artifacts(task_context_id, learnings)."""
        else:
            return f"Artifact not found: {artifact_id}"

    except Exception as e:
        return f"Error archiving artifact: {str(e)}"


@mcp.tool
def search_artifacts(
    query: Annotated[str, Field(description="Search query")],
    limit: Annotated[
        int, Field(description="Maximum number of results to return")
    ] = 10,
) -> str:
    """
    Full-text search across artifacts.

    Use this before creating new artifacts to avoid duplicates.
    Returns results ranked by relevance.
    """
    try:
        if not query or not query.strip():
            return "Error: Search query cannot be empty."

        results = db_manager.search_artifacts(query=query, limit=limit)

        if not results:
            return f"No artifacts found matching query: '{query}'"

        result = f"Search results for '{query}' (limit: {limit}):\n\n"
        for row in results:
            artifact_id, summary, content, task_context_id, rank = row
            result += f"Artifact ID: {artifact_id}\n"
            result += f"Task Context ID: {task_context_id}\n"
            result += f"Summary: {summary}\n"
            result += f"Content Preview: {content[:200]}{'...' if len(content) > 200 else ''}\n"
            result += f"Relevance Rank: {rank}\n"
            result += "---\n"

        return result

    except Exception as e:
        return f"Error searching artifacts: {str(e)}"


@mcp.tool
def reflect_and_update_artifacts(
    task_context_id: Annotated[
        str, Field(description="ID of the task context used for this work")
    ],
    learnings: Annotated[
        str,
        Field(
            description="What you learned during task execution (mistakes found, corrections made, patterns discovered, etc.)"
        ),
    ],
) -> str:
    """
    Reflection checkpoint.

    Call before declaring a task complete, and after corrections or user feedback.
    This returns the current artifacts and prompts you to create/update/archive as needed.
    """
    try:
        # Get current artifacts for this task context (excluding result type)
        artifacts = db_manager.get_artifacts_for_task_context(
            task_context_id=task_context_id,
            artifact_types=DEFAULT_ARTIFACT_TYPES,
            status=ArtifactStatus.ACTIVE,
        )

        result = f"""Reflection checkpoint (task context: {task_context_id})

Learnings:
{learnings}

Active artifacts ({len(artifacts)}):
"""

        if artifacts:
            for artifact in artifacts:
                result += f"\n- [{artifact.artifact_type}] {artifact.summary} (ID: {artifact.id})"
        else:
            result += "\n- (none)"

        result += """

Required actions:
1) For new learnings: call create_artifact(...)
2) For corrections: call update_artifact(...)
3) For obsolete guidance: call archive_artifact(...)

Next step: call the appropriate artifact tool(s) now.
"""

        return result

    except Exception as e:
        return f"Error during reflection: {str(e)}"
