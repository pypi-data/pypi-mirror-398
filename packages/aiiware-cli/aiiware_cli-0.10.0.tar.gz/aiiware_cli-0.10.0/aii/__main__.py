# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""AII CLI entry point - enables 'python -m aii' usage"""


import sys

from .main import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
