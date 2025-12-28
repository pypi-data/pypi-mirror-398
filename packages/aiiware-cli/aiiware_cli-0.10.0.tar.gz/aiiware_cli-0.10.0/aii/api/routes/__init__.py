# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""API route handlers."""


from .execute import router as execute_router
from .functions import router as functions_router
from .status import router as status_router
from .models import router as models_router
from .stats import router as stats_router  # v0.9.0

__all__ = ["execute_router", "functions_router", "status_router", "models_router", "stats_router"]
