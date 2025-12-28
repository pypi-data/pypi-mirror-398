# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""v0.9.1 Migration - Normalize model names (strip provider prefix)"""


import aiosqlite

from ..migration_manager import Migration


async def upgrade(db: aiosqlite.Connection) -> None:
    """
    Normalize model names by stripping provider prefix.

    This migration ensures consistent model names in the database by removing
    provider prefixes (e.g., "openai:gpt-4.1-mini" -> "gpt-4.1-mini").

    Benefits:
    - Consistent display in analytics
    - Cleaner model names
    - Provider info already available in separate column
    """

    # Get all records with provider prefix in model name
    async with db.execute(
        """
        SELECT id, model
        FROM executions
        WHERE model LIKE '%:%'
        """
    ) as cursor:
        rows = await cursor.fetchall()

    updated_count = 0
    for row in rows:
        record_id = row[0]
        model = row[1]

        # Strip provider prefix
        if ":" in model:
            clean_model = model.split(":")[-1]

            # Update the record
            await db.execute(
                "UPDATE executions SET model = ? WHERE id = ?", (clean_model, record_id)
            )
            updated_count += 1

    await db.commit()

    print(f"Normalized {updated_count} model names (stripped provider prefix)")


# Migration definition
migration = Migration(
    version=5,
    name="normalize_model_names",
    description="Strip provider prefix from model names for consistent display (v0.9.1)",
    up=upgrade,
)
