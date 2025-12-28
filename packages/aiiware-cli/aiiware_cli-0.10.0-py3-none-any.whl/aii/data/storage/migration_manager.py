# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Database Migration Manager - Version-controlled schema migrations"""


import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Awaitable

import aiosqlite


logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Represents a single database migration"""

    version: int
    name: str
    up: Callable[[aiosqlite.Connection], Awaitable[None]]
    description: str = ""


class MigrationManager:
    """Manages database schema migrations with version tracking"""

    def __init__(self, db_path: Path):
        """
        Initialize migration manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.migrations: list[Migration] = []
        self._initialized = False

    def register_migration(self, migration: Migration) -> None:
        """
        Register a migration.

        Args:
            migration: Migration to register
        """
        self.migrations.append(migration)
        # Keep migrations sorted by version
        self.migrations.sort(key=lambda m: m.version)

    async def initialize(self) -> None:
        """Initialize migration tracking table"""
        if self._initialized:
            return

        async with aiosqlite.connect(str(self.db_path)) as db:
            # Create schema_migrations table if it doesn't exist
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT DEFAULT ''
                )
                """
            )
            await db.commit()

        self._initialized = True
        logger.debug(f"Migration manager initialized for {self.db_path}")

    async def get_current_version(self) -> int:
        """
        Get current schema version.

        Returns:
            Current version number (0 if no migrations applied)
        """
        await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT MAX(version) as version FROM schema_migrations"
            ) as cursor:
                row = await cursor.fetchone()
                version = row[0] if row and row[0] is not None else 0

        logger.debug(f"Current schema version: {version}")
        return version

    async def get_applied_migrations(self) -> list[dict]:
        """
        Get list of applied migrations.

        Returns:
            List of migration records
        """
        await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT version, name, applied_at, description
                FROM schema_migrations
                ORDER BY version ASC
                """
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_pending_migrations(self) -> list[Migration]:
        """
        Get list of pending migrations.

        Returns:
            List of migrations not yet applied
        """
        current_version = await self.get_current_version()
        pending = [m for m in self.migrations if m.version > current_version]
        logger.debug(f"Found {len(pending)} pending migrations")
        return pending

    async def migrate(self) -> dict:
        """
        Apply all pending migrations.

        Returns:
            Dict with migration results (applied count, current version)
        """
        await self.initialize()

        pending = await self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations")
            return {
                "applied": 0,
                "current_version": await self.get_current_version(),
                "status": "up_to_date",
            }

        applied_count = 0
        for migration in pending:
            try:
                await self._apply_migration(migration)
                applied_count += 1
                logger.info(
                    f"Applied migration {migration.version}: {migration.name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to apply migration {migration.version}: {migration.name} - {e}"
                )
                # Stop on first failure
                raise

        current_version = await self.get_current_version()
        logger.info(f"Migrations complete. Current version: {current_version}")

        return {
            "applied": applied_count,
            "current_version": current_version,
            "status": "success",
        }

    async def _apply_migration(self, migration: Migration) -> None:
        """
        Apply a single migration in a transaction.

        Args:
            migration: Migration to apply
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Start transaction
            await db.execute("BEGIN TRANSACTION")

            try:
                # Run migration
                await migration.up(db)

                # Record migration
                await db.execute(
                    """
                    INSERT INTO schema_migrations (version, name, description)
                    VALUES (?, ?, ?)
                    """,
                    (migration.version, migration.name, migration.description),
                )

                # Commit transaction
                await db.commit()
                logger.debug(f"Migration {migration.version} committed successfully")

            except Exception as e:
                # Rollback on error
                await db.rollback()
                logger.error(f"Migration {migration.version} rolled back: {e}")
                raise

    async def is_migration_applied(self, version: int) -> bool:
        """
        Check if a specific migration has been applied.

        Args:
            version: Migration version to check

        Returns:
            True if migration is applied
        """
        await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE version = ?",
                (version,),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0 if row else False

    async def get_migration_info(self) -> dict:
        """
        Get comprehensive migration status information.

        Returns:
            Dict with current version, applied migrations, pending migrations
        """
        await self.initialize()

        current_version = await self.get_current_version()
        applied = await self.get_applied_migrations()
        pending = await self.get_pending_migrations()

        return {
            "current_version": current_version,
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_migrations": applied,
            "pending_migrations": [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                }
                for m in pending
            ],
            "total_migrations": len(self.migrations),
        }
