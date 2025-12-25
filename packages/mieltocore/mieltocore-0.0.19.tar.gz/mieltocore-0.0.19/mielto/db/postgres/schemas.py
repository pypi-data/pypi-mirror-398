"""Table schemas and related utils used by the PostgresDb class"""

from typing import Any

try:
    from sqlalchemy.types import JSON, BigInteger, Boolean, Date, String
    from sqlalchemy.dialects.postgresql import JSONB
except ImportError:
    raise ImportError("`sqlalchemy` not installed. Please install it using `pip install sqlalchemy`")

SESSION_TABLE_SCHEMA = {
    "session_id": {"type": String, "nullable": False},
    "session_type": {"type": String, "nullable": False, "index": True},
    "agent_id": {"type": String, "nullable": True},
    "team_id": {"type": String, "nullable": True},
    "workflow_id": {"type": String, "nullable": True},
    "user_id": {"type": String, "nullable": True},
    "session_data": {"type": JSON, "nullable": True},
    "agent_data": {"type": JSON, "nullable": True},
    "team_data": {"type": JSON, "nullable": True},
    "workflow_data": {"type": JSON, "nullable": True},
    "metadata": {"type": JSON, "nullable": True},
    "runs": {"type": JSON, "nullable": True},
    "summary": {"type": JSON, "nullable": True},
    "workspace_id": {"type": String, "nullable": True, "index": True},
    "created_at": {"type": BigInteger, "nullable": False, "index": True},
    "updated_at": {"type": BigInteger, "nullable": True},
    "_unique_constraints": [
        {
            "name": "uq_session_id",
            "columns": ["session_id"],
        },
    ],
    "_indexes": [
        {
            "name": "idx_sessions_workspace_type",
            "columns": ["workspace_id", "session_type"],
        },
        {
            "name": "idx_sessions_workspace_user",
            "columns": ["workspace_id", "user_id"],
        },
        {
            "name": "idx_sessions_agent_id",
            "columns": ["agent_id"],
        },
        {
            "name": "idx_sessions_team_id",
            "columns": ["team_id"],
        },
        {
            "name": "idx_sessions_workflow_id",
            "columns": ["workflow_id"],
        },
    ],
}

MEMORY_TABLE_SCHEMA = {
    "memory_id": {"type": String, "primary_key": True, "nullable": False},
    "memory": {"type": JSON, "nullable": False},
    "memory_type": {"type": String, "nullable": True},
    "input": {"type": String, "nullable": True},
    "agent_id": {"type": String, "nullable": True},
    "team_id": {"type": String, "nullable": True},
    "user_id": {"type": String, "nullable": True, "index": True},
    "topics": {"type": JSON, "nullable": True},
    "facts": {"type": JSON, "nullable": True},
    "updated_at": {"type": BigInteger, "nullable": True, "index": True},
    "workspace_id": {"type": String, "nullable": True, "index": True},
    "metadata": {"type": JSON, "nullable": True},
    "_indexes": [
        {
            "name": "idx_memories_workspace_user",
            "columns": ["workspace_id", "user_id"],
        },
        {
            "name": "idx_memories_workspace_type",
            "columns": ["workspace_id", "memory_type"],
        }
    ],
}

EVAL_TABLE_SCHEMA = {
    "run_id": {"type": String, "primary_key": True, "nullable": False},
    "eval_type": {"type": String, "nullable": False},
    "eval_data": {"type": JSON, "nullable": False},
    "eval_input": {"type": JSON, "nullable": False},
    "name": {"type": String, "nullable": True},
    "agent_id": {"type": String, "nullable": True},
    "team_id": {"type": String, "nullable": True},
    "workflow_id": {"type": String, "nullable": True},
    "model_id": {"type": String, "nullable": True},
    "model_provider": {"type": String, "nullable": True},
    "evaluated_component_name": {"type": String, "nullable": True},
    "workspace_id": {"type": String, "nullable": True, "index": True},
    "created_at": {"type": BigInteger, "nullable": False, "index": True},
    "updated_at": {"type": BigInteger, "nullable": True},
    "_indexes": [
        {
            "name": "idx_evals_workspace_type",
            "columns": ["workspace_id", "eval_type"],
        },
        {
            "name": "idx_evals_workspace_agent",
            "columns": ["workspace_id", "agent_id"],
        },
        {
            "name": "idx_evals_workspace_team",
            "columns": ["workspace_id", "team_id"],
        },
        {
            "name": "idx_evals_workspace_workflow",
            "columns": ["workspace_id", "workflow_id"],
        },
        {
            "name": "idx_evals_agent_id",
            "columns": ["agent_id"],
        },
        {
            "name": "idx_evals_team_id",
            "columns": ["team_id"],
        },
        {
            "name": "idx_evals_workflow_id",
            "columns": ["workflow_id"],
        },
        {
            "name": "idx_evals_model_id",
            "columns": ["model_id"],
        },
    ],
}

KNOWLEDGE_TABLE_SCHEMA = {
    "id": {"type": String, "primary_key": True, "nullable": False},
    "name": {"type": String, "nullable": False},
    "description": {"type": String, "nullable": False},
    "file_data": {"type": JSONB, "nullable": True},
    "metadata": {"type": JSON, "nullable": True},
    "content_hash": {"type": String, "nullable": True},
    "type": {"type": String, "nullable": True},
    "size": {"type": BigInteger, "nullable": True},
    "linked_to": {"type": String, "nullable": True},
    "config": {"type": JSON, "nullable": True},
    "access_count": {"type": BigInteger, "nullable": True},
    "status": {"type": String, "nullable": True},
    "sync_status": {"type": String, "nullable": True},
    "definition": {"type": JSON, "nullable": True},
    "status_message": {"type": String, "nullable": True},
    "created_at": {"type": BigInteger, "nullable": True, "index": True},
    "updated_at": {"type": BigInteger, "nullable": True},
    "external_id": {"type": String, "nullable": True},
    "collection_id": {"type": String, "nullable": True},
    "workspace_id": {"type": String, "nullable": True, "index": True},
    "_indexes": [
        {
            "name": "idx_knowledge_workspace_collection",
            "columns": ["workspace_id", "collection_id"],
        },
        {
            "name": "idx_knowledge_collection_id",
            "columns": ["collection_id"],
        },
        {
            "name": "idx_knowledge_external_id",
            "columns": ["external_id"],
        },
    ],
}

METRICS_TABLE_SCHEMA = {
    "id": {"type": String, "primary_key": True, "nullable": False},
    "agent_runs_count": {"type": BigInteger, "nullable": False, "default": 0},
    "team_runs_count": {"type": BigInteger, "nullable": False, "default": 0},
    "workflow_runs_count": {"type": BigInteger, "nullable": False, "default": 0},
    "agent_sessions_count": {"type": BigInteger, "nullable": False, "default": 0},
    "team_sessions_count": {"type": BigInteger, "nullable": False, "default": 0},
    "workflow_sessions_count": {"type": BigInteger, "nullable": False, "default": 0},
    "users_count": {"type": BigInteger, "nullable": False, "default": 0},
    "token_metrics": {"type": JSON, "nullable": False, "default": {}},
    "model_metrics": {"type": JSON, "nullable": False, "default": {}},
    "date": {"type": Date, "nullable": False, "index": True},
    "aggregation_period": {"type": String, "nullable": False},
    "workspace_id": {"type": String, "nullable": True, "index": True},
    "created_at": {"type": BigInteger, "nullable": False},
    "updated_at": {"type": BigInteger, "nullable": True},
    "completed": {"type": Boolean, "nullable": False, "default": False},
    "_unique_constraints": [
        {
            "name": "uq_metrics_date_period",
            "columns": ["date", "aggregation_period"],
        }
    ],
    "_indexes": [
        {
            "name": "idx_metrics_workspace_date",
            "columns": ["workspace_id", "date"],
        },
        {
            "name": "idx_metrics_workspace_period",
            "columns": ["workspace_id", "aggregation_period"],
        },
        {
            "name": "idx_metrics_workspace_completed",
            "columns": ["workspace_id", "completed"],
        },
    ],
}


def get_table_schema_definition(table_type: str) -> dict[str, Any]:
    """
    Get the expected schema definition for the given table.

    Args:
        table_type (str): The type of table to get the schema for.

    Returns:
        Dict[str, Any]: Dictionary containing column definitions for the table
    """
    schemas = {
        "sessions": SESSION_TABLE_SCHEMA,
        "evals": EVAL_TABLE_SCHEMA,
        "metrics": METRICS_TABLE_SCHEMA,
        "memories": MEMORY_TABLE_SCHEMA,
        "knowledge": KNOWLEDGE_TABLE_SCHEMA,
    }

    schema = schemas.get(table_type, {})
    if not schema:
        raise ValueError(f"Unknown table type: {table_type}")

    return schema  # type: ignore[return-value]
