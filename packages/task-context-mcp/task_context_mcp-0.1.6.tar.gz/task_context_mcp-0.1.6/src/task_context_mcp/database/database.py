from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from task_context_mcp.config.settings import get_settings
from task_context_mcp.database.migrations import run_migrations
from task_context_mcp.database.models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    Base,
    TaskContext,
    TaskContextStatus,
)


class DatabaseManager:
    """Database manager class for handling database operations."""

    def __init__(self):
        self.settings = get_settings()
        Path(self.settings.data_dir).mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(self.settings.database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """
        Create all tables in the database using SQLAlchemy metadata.

        This method is used for:
        - In-memory databases (tests)
        - Fallback when Alembic migrations fail

        For file-based databases, init_db() runs Alembic migrations instead.
        """
        Base.metadata.create_all(bind=self.engine)

    def init_db(self):
        """
        Initialize the database by running migrations.

        Uses Alembic to apply all pending migrations, ensuring the database
        schema is up-to-date with the latest model definitions.
        For in-memory databases, falls back to direct table creation.
        """
        Path(self.settings.data_dir).mkdir(parents=True, exist_ok=True)
        logger.info("Initializing database with migrations...")

        # Check if using in-memory database (common in tests)
        is_memory_db = ":memory:" in str(self.settings.database_url)

        if is_memory_db:
            # For in-memory databases, use direct table creation
            # Alembic migrations don't work well with in-memory SQLite
            logger.debug("Using in-memory database, creating tables directly")
            self.create_tables()
        else:
            try:
                # Run Alembic migrations to ensure schema is up-to-date
                run_migrations()
            except Exception as e:
                logger.warning(
                    f"Migration failed, falling back to direct table creation: {e}"
                )
                # Fallback to direct table creation for backward compatibility
                self.create_tables()

        # Create FTS5 virtual table for full-text search
        with self.engine.connect() as conn:
            conn.execute(
                text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
                    id, summary, content, task_context_id, tokenize='porter'
                );
            """)
            )
            conn.commit()
        logger.info("Database initialization completed")

    @contextmanager
    def get_session(self):
        """Get a database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ==================== Task Context Operations ====================

    def create_task_context(
        self,
        summary: str,
        description: str,
        status: TaskContextStatus = TaskContextStatus.ACTIVE,
    ) -> TaskContext:
        """Create a new task context (reusable task type/category)."""
        logger.info(f"Creating task context: {summary}")
        with self.get_session() as session:
            task_context = TaskContext(
                summary=summary, description=description, status=status.value
            )
            session.add(task_context)
            session.commit()
            session.refresh(task_context)
            logger.info(f"Task context created successfully: {task_context.id}")
            return task_context

    def update_task_context(
        self,
        task_context_id: str,
        summary: str | None = None,
        description: str | None = None,
        status: TaskContextStatus | None = None,
    ) -> TaskContext | None:
        """Update an existing task context."""
        logger.info(f"Updating task context: {task_context_id}")
        with self.get_session() as session:
            task_context = (
                session.query(TaskContext)
                .filter(TaskContext.id == task_context_id)
                .first()
            )
            if task_context:
                if summary is not None:
                    task_context.summary = summary
                if description is not None:
                    task_context.description = description
                if status is not None:
                    task_context.status = status.value
                session.commit()
                session.refresh(task_context)
                logger.info(f"Task context updated successfully: {task_context_id}")
                return task_context
            else:
                logger.warning(f"Task context not found: {task_context_id}")
                return None

    def archive_task_context(self, task_context_id: str) -> TaskContext | None:
        """Archive a task context by setting its status to ARCHIVED."""
        logger.info(f"Archiving task context: {task_context_id}")
        with self.get_session() as session:
            task_context = (
                session.query(TaskContext)
                .filter(TaskContext.id == task_context_id)
                .first()
            )
            if task_context:
                task_context.status = TaskContextStatus.ARCHIVED.value
                session.commit()
                session.refresh(task_context)
                logger.info(f"Task context archived successfully: {task_context_id}")
                return task_context
            else:
                logger.warning(f"Task context not found: {task_context_id}")
                return None

    def get_active_task_contexts(self) -> list[TaskContext]:
        """Get all active task contexts."""
        logger.info("Getting all active task contexts")
        with self.get_session() as session:
            task_contexts = (
                session.query(TaskContext)
                .filter(TaskContext.status == TaskContextStatus.ACTIVE.value)
                .all()
            )
            logger.info(f"Retrieved {len(task_contexts)} active task contexts")
            return task_contexts

    # ==================== Artifact Operations ====================

    def create_artifact(
        self,
        task_context_id: str,
        artifact_type: ArtifactType,
        content: str,
        summary: str,
        status: ArtifactStatus = ArtifactStatus.ACTIVE,
    ) -> Artifact:
        """
        Create a new artifact for a task context.

        Multiple artifacts of the same type can exist per task context.
        Each call creates a NEW artifact (no upsert behavior).
        """
        logger.info(
            f"Creating artifact for task context {task_context_id}, type {artifact_type}"
        )
        with self.get_session() as session:
            artifact = Artifact(
                task_context_id=task_context_id,
                artifact_type=artifact_type.value,
                summary=summary,
                content=content,
                status=status.value,
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            # Insert into FTS5 table
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                    INSERT INTO artifacts_fts (id, summary, content, task_context_id)
                    VALUES (:id, :summary, :content, :task_context_id)
                """),
                    {
                        "id": artifact.id,
                        "summary": artifact.summary,
                        "content": artifact.content,
                        "task_context_id": artifact.task_context_id,
                    },
                )
                conn.commit()
            logger.info(f"Artifact created successfully: {artifact.id}")
            return artifact

    def update_artifact(
        self,
        artifact_id: str,
        summary: str | None = None,
        content: str | None = None,
    ) -> Artifact | None:
        """Update an existing artifact's summary and/or content."""
        logger.info(f"Updating artifact: {artifact_id}")
        with self.get_session() as session:
            artifact = (
                session.query(Artifact).filter(Artifact.id == artifact_id).first()
            )
            if artifact:
                if summary is not None:
                    artifact.summary = summary
                if content is not None:
                    artifact.content = content
                session.commit()
                session.refresh(artifact)
                # Update FTS5 table
                with self.engine.connect() as conn:
                    conn.execute(
                        text("""
                        UPDATE artifacts_fts 
                        SET summary = :summary, content = :content
                        WHERE id = :id
                    """),
                        {
                            "id": artifact.id,
                            "summary": artifact.summary,
                            "content": artifact.content,
                        },
                    )
                    conn.commit()
                logger.info(f"Artifact updated successfully: {artifact_id}")
                return artifact
            else:
                logger.warning(f"Artifact not found: {artifact_id}")
                return None

    def archive_artifact(
        self, artifact_id: str, reason: str | None = None
    ) -> Artifact | None:
        """Archive an artifact by setting its status to ARCHIVED."""
        logger.info(f"Archiving artifact: {artifact_id}")
        with self.get_session() as session:
            artifact = (
                session.query(Artifact).filter(Artifact.id == artifact_id).first()
            )
            if artifact:
                artifact.status = ArtifactStatus.ARCHIVED.value
                artifact.archived_at = datetime.now(timezone.utc)
                artifact.archivation_reason = reason
                session.commit()
                session.refresh(artifact)
                # Remove from FTS5 table
                with self.engine.connect() as conn:
                    conn.execute(
                        text("DELETE FROM artifacts_fts WHERE id = :id"),
                        {"id": artifact_id},
                    )
                    conn.commit()
                logger.info(f"Artifact archived successfully: {artifact_id}")
                return artifact
            else:
                logger.warning(f"Artifact not found: {artifact_id}")
                return None

    def get_artifacts_for_task_context(
        self,
        task_context_id: str,
        artifact_types: list[ArtifactType] | None = None,
        status: ArtifactStatus | None = None,
    ) -> list[Artifact]:
        """Get artifacts for a task context, optionally filtered by type and status."""
        logger.info(f"Getting artifacts for task context: {task_context_id}")
        with self.get_session() as session:
            query = session.query(Artifact).filter(
                Artifact.task_context_id == task_context_id
            )
            if artifact_types:
                query = query.filter(
                    Artifact.artifact_type.in_([t.value for t in artifact_types])
                )
            if status is not None:
                query = query.filter(Artifact.status == status.value)
            results = query.order_by(Artifact.created_at.desc()).all()
            logger.info(
                f"Retrieved {len(results)} artifacts for task context {task_context_id}"
            )
            return results

    def search_artifacts(self, query: str, limit: int = 10) -> list:
        """Search artifacts using full-text search."""
        logger.info(f"Searching artifacts with query: {query}")
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT id, summary, content, task_context_id, rank
                FROM artifacts_fts
                WHERE artifacts_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
            """),
                {"query": query, "limit": limit},
            )
            rows = result.fetchall()
            logger.info(f"Found {len(rows)} matching artifacts")
            return rows


# Global instance for convenience
db_manager = DatabaseManager()
