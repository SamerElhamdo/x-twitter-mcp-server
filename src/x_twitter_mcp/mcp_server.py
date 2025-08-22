#!/usr/bin/env python3
"""
Twitter MCP Server - OAuth 2.0
خادم MCP منفصل يعمل مع mcp-proxy
"""

import asyncio
import logging
from fastmcp import FastMCP

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء خادم FastMCP
server = FastMCP(name="TwitterMCPServer")

# تشغيل الخادم الرئيسي
def run():
    """نقطة الدخول لتشغيل خادم FastMCP مباشرة."""
    logger.info(f"بدء تشغيل {server.name}...")
    logger.info("✅ خادم MCP يعمل ويمكن استخدامه مع mcp-proxy")
    # إرجاع coroutine ليتم انتظاره من قبل المتصل (مثل Claude Desktop)
    return server.run()

if __name__ == "__main__":
    run()
