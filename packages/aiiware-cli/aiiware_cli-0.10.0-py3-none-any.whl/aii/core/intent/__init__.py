# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Intent recognition components"""

from .models import IntentTemplate
from .recognizer import IntentRecognizer

__all__ = ["IntentRecognizer", "IntentTemplate"]
