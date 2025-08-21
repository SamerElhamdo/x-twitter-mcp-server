#!/usr/bin/env python3
"""
Twitter MCP Server Runner - محسن للأداء السريع
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# إضافة المسار للوحدات
sys.path.insert(0, str(Path(__file__).parent / "src"))

# إعدادات logging محسنة
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_server.log')
    ]
)

# إيقاف warnings غير الضرورية
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

async def main():
    """الدالة الرئيسية"""
    try:
        from x_twitter_mcp.server import run
        
        print("🚀 بدء تشغيل Twitter MCP Server...")
        print("📊 إعدادات محسنة للأداء السريع")
        print("🔧 إصلاح DeprecationWarning")
        print("⚡ تحسين الاستجابة")
        print()
        
        # تشغيل الخادم
        await run()
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل الخادم: {e}")
        logging.error(f"خطأ في التشغيل: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # إعدادات Python محسنة
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    
    # تشغيل الخادم
    asyncio.run(main())
