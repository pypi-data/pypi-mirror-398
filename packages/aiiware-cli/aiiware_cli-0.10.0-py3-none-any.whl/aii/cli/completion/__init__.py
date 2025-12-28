# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Shell completion functionality for aii CLI.

This module provides tab completion for bash, zsh, and fish shells.
"""

from .generator import CompletionGenerator, CompletionSpec
from .installer import CompletionInstaller

__all__ = ["CompletionGenerator", "CompletionSpec", "CompletionInstaller"]
