#!/usr/bin/env python3
"""
Entry point for running the Twitter MCP server directly
"""

import sys
import os
import uvicorn

# إضافة المجلد الحالي إلى Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from x_twitter_mcp.server import app
from x_twitter_mcp.config import get_settings

def main():
    """تشغيل الخادم الرئيسي"""
    settings = get_settings()
    
    print("🚀 بدء تشغيل Twitter MCP Server...")
    print(f"✅ الخادم يعمل على http://{settings.host}:{settings.port}")
    print(f"🌐 الصفحة الرئيسية: http://{settings.host}:{settings.port}/")
    print(f"📖 واجهة API: http://{settings.host}:{settings.port}/docs")
    print(f"🔐 صفحة المصادقة: http://{settings.host}:{settings.port}/auth")
    print("\n" + "="*50)
    
    uvicorn.run(
        "x_twitter_mcp.server:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
