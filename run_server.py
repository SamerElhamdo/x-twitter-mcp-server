#!/usr/bin/env python3
"""
Simple script to run the Twitter MCP server
"""

import sys
import os

# إضافة مجلد src إلى Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from x_twitter_mcp.server import run
    print("🚀 بدء تشغيل Twitter MCP Server...")
    run()
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    print("💡 تأكد من تثبيت المتطلبات: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ خطأ في التشغيل: {e}")
    sys.exit(1)
