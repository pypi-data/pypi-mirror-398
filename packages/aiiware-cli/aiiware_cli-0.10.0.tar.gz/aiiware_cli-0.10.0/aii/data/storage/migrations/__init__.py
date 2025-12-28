# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.


"""Database migrations for Aii CLI storage"""

# Import migration definitions
from .migrations_001_initial_schema import migration as migration_001_initial_schema
from .migrations_002_enhance_executions import (
    migration as migration_002_enhance_executions,
)
from .migrations_003_add_client_type import migration as migration_003_add_client_type
from .migrations_004_backfill_costs import migration as migration_004_backfill_costs
from .migrations_005_normalize_model_names import (
    migration as migration_005_normalize_model_names,
)

__all__ = [
    "migration_001_initial_schema",
    "migration_002_enhance_executions",
    "migration_003_add_client_type",
    "migration_004_backfill_costs",
    "migration_005_normalize_model_names",
]
