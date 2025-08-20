#!/usr/bin/env python3
"""
Entry point for running the Twitter MCP server directly
"""

import sys
import os

# إضافة المجلد الحالي إلى Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from x_twitter_mcp.server import run

if __name__ == "__main__":
    run()
