# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Wizard step implementations.

Each step in the setup wizard is implemented as a subclass of WizardStep.
"""

from aii.cli.setup.steps.base import WizardStep, StepResult

__all__ = ["WizardStep", "StepResult"]
