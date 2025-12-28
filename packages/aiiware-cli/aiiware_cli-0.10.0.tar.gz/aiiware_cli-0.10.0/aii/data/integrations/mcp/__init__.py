# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP (Model Context Protocol) Integration

This package provides MCP Host functionality for AII, enabling connection
to multiple MCP servers for enhanced tool and resource access.

Architecture:
- AII acts as an MCP Host
- Contains an MCP Client Manager
- Connects to multiple MCP Servers (filesystem, GitHub, PostgreSQL, etc.)

Key Components:
- defaults.py: Built-in default server configurations
- config_loader.py: Configuration loading with priority system
- client_manager.py: Multi-server connection management
- models.py: Aii-specific data models

MCP Specification: https://modelcontextprotocol.io/specification/2025-06-18
Python SDK: https://github.com/modelcontextprotocol/python-sdk
"""

__version__ = "0.4.8"
