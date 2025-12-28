# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""v0.9.0 Migration - Enhance executions table for model intelligence & analytics"""


import aiosqlite

from ..migration_manager import Migration


async def upgrade(db: aiosqlite.Connection) -> None:
    """
    Enhance executions table with model intelligence and analytics fields.

    This migration adds:
    - execution_id: Unique identifier for each execution
    - model: LLM model used (e.g., "gpt-4o", "claude-3.5-sonnet")
    - provider: LLM provider (e.g., "openai", "anthropic", "google")
    - function_category: Category of function (e.g., "content", "code")
    - error_code: Error code if execution failed
    - error_message: Error message if execution failed
    - time_to_first_token_ms: Latency to first token (TTFT)
    - total_execution_time_ms: Total execution time in milliseconds
    - input_tokens: Number of input tokens sent
    - output_tokens: Number of output tokens received
    - cost_usd: Estimated cost in USD
    - session_id: Session identifier
    - user_id: User identifier (for multi-user support)
    """

    # Check if this is a fresh database (no executions table yet)
    async with db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='executions'"
    ) as cursor:
        table_exists = await cursor.fetchone() is not None

    if not table_exists:
        # Fresh install - create new table with all fields
        await db.executescript(
            """
            CREATE TABLE executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE NOT NULL,
                timestamp TIMESTAMP NOT NULL,

                -- Function info
                function_name TEXT NOT NULL,
                function_category TEXT,

                -- Model info
                model TEXT,
                provider TEXT,

                -- Execution status
                success BOOLEAN DEFAULT FALSE,
                error_code TEXT,
                error_message TEXT,

                -- Performance metrics
                time_to_first_token_ms INTEGER,
                total_execution_time_ms INTEGER,

                -- Token usage
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,

                -- Context (all optional - not all executions have chat context)
                chat_id TEXT,
                session_id TEXT,
                user_id TEXT,

                -- Legacy fields (for backward compatibility)
                parameters TEXT DEFAULT '{}',
                result TEXT DEFAULT '{}'
            );

            -- Indexes for analytics queries
            CREATE INDEX idx_executions_timestamp ON executions (timestamp DESC);
            CREATE INDEX idx_executions_model ON executions (model);
            CREATE INDEX idx_executions_provider ON executions (provider);
            CREATE INDEX idx_executions_function_name ON executions (function_name);
            CREATE INDEX idx_executions_function_category ON executions (function_category);
            CREATE INDEX idx_executions_success ON executions (success);
            CREATE INDEX idx_executions_chat_id ON executions (chat_id);

            -- Composite indexes for common queries
            CREATE INDEX idx_executions_model_timestamp ON executions (model, timestamp DESC);
            CREATE INDEX idx_executions_model_function ON executions (model, function_name);
            CREATE INDEX idx_executions_category_timestamp ON executions (function_category, timestamp DESC);
            """
        )
    else:
        # Existing database - add new columns (SQLite doesn't support adding multiple columns at once)
        # We'll add them one by one, and handle the case where they might already exist

        new_columns = [
            ("execution_id", "TEXT"),
            ("model", "TEXT"),
            ("provider", "TEXT"),
            ("function_category", "TEXT"),
            ("error_code", "TEXT"),
            ("error_message", "TEXT"),
            ("time_to_first_token_ms", "INTEGER"),
            ("total_execution_time_ms", "INTEGER"),
            ("input_tokens", "INTEGER DEFAULT 0"),
            ("output_tokens", "INTEGER DEFAULT 0"),
            ("cost_usd", "REAL DEFAULT 0.0"),
            ("session_id", "TEXT"),
            ("user_id", "TEXT"),
        ]

        # Check existing columns
        async with db.execute("PRAGMA table_info(executions)") as cursor:
            existing_columns = {row[1] for row in await cursor.fetchall()}

        # Add missing columns
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                await db.execute(
                    f"ALTER TABLE executions ADD COLUMN {column_name} {column_type}"
                )

        # Add indexes (CREATE INDEX IF NOT EXISTS is safe to run multiple times)
        await db.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_executions_timestamp ON executions (timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_executions_model ON executions (model);
            CREATE INDEX IF NOT EXISTS idx_executions_provider ON executions (provider);
            CREATE INDEX IF NOT EXISTS idx_executions_function_name ON executions (function_name);
            CREATE INDEX IF NOT EXISTS idx_executions_function_category ON executions (function_category);
            CREATE INDEX IF NOT EXISTS idx_executions_success ON executions (success);

            -- Composite indexes for common queries
            CREATE INDEX IF NOT EXISTS idx_executions_model_timestamp ON executions (model, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_executions_model_function ON executions (model, function_name);
            CREATE INDEX IF NOT EXISTS idx_executions_category_timestamp ON executions (function_category, timestamp DESC);
            """
        )


# Migration definition
migration = Migration(
    version=2,
    name="enhance_executions",
    description="Add model intelligence and analytics fields to executions table (v0.9.0)",
    up=upgrade,
)
