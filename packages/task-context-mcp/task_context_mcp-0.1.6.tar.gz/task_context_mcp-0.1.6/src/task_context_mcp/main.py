"""
Task Context MCP Server

An MCP server for managing task contexts and artifacts to enable AI agents
to autonomously manage and improve execution processes for repetitive task types.

Task contexts represent reusable task categories (e.g., "CV analysis for Python developers"),
not individual task instances. Artifacts store general practices, rules, prompts, and
learnings that can be applied to any instance of that task type.
"""

from task_context_mcp.config.logging import setup_logging
from task_context_mcp.database.database import db_manager
from task_context_mcp.server import mcp
import task_context_mcp.tools  # noqa: F401 to register tools



def run():
    # Initialize logging
    setup_logging()

    # Initialize database
    db_manager.init_db()

    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run()
