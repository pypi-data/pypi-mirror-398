# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""v0.9.1 Migration - Backfill costs for existing records with missing pricing"""


import aiosqlite

from ..migration_manager import Migration


async def upgrade(db: aiosqlite.Connection) -> None:
    """
    Backfill costs for existing records where cost_usd is 0.0 but tokens are present.

    This migration fixes records that were created before model pricing was added or
    when provider prefixes caused pricing lookup failures (e.g., "openai:gpt-4.1-mini").

    The migration:
    1. Finds all executions where cost_usd = 0.0 but tokens are present
    2. Recalculates cost using the current pricing model
    3. Updates the cost_usd field

    This is safe to run multiple times - it only updates records with cost_usd = 0.0.
    """

    # Import pricing function
    from ...providers.model_pricing import calculate_cost

    # Get all records with zero cost but non-zero tokens
    async with db.execute(
        """
        SELECT id, model, input_tokens, output_tokens
        FROM executions
        WHERE cost_usd = 0.0
        AND (input_tokens > 0 OR output_tokens > 0)
        AND model IS NOT NULL
        """
    ) as cursor:
        rows = await cursor.fetchall()

    updated_count = 0
    for row in rows:
        record_id = row[0]
        model = row[1]
        input_tokens = row[2] or 0
        output_tokens = row[3] or 0

        # Calculate cost using current pricing
        cost = calculate_cost(model, input_tokens, output_tokens)

        if cost > 0:
            # Update the record
            await db.execute(
                "UPDATE executions SET cost_usd = ? WHERE id = ?", (cost, record_id)
            )
            updated_count += 1

    await db.commit()

    print(f"Backfilled costs for {updated_count} executions")


# Migration definition
migration = Migration(
    version=4,
    name="backfill_costs",
    description="Backfill costs for records with missing pricing (v0.9.1 hotfix)",
    up=upgrade,
)
