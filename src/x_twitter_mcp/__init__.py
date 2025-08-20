"""
X (Twitter) MCP Server with Local Database Authentication

A Model Context Protocol (MCP) server for interacting with Twitter (X) via AI tools.
This server stores Twitter API credentials locally and allows you to use only username
in your requests for enhanced security and convenience.

Features:
- Local SQLite database for credential storage
- Web API interface for account management
- Username-only authentication for daily use
- Complete Twitter API v2 implementation
"""

__version__ = "0.2.0"
__author__ = "Rafal Janicki"
__email__ = "rafal@kult.io"

from .server import run

__all__ = ["run"]