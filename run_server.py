#!/usr/bin/env python3
"""
Twitter MCP Server Runner - OAuth 2.0

تشغيل الخادم الرئيسي مع دعم OAuth 2.0
"""

import sys
import os
import argparse
import uvicorn

# إضافة المجلد الحالي إلى Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.x_twitter_mcp.config import get_settings
from src.x_twitter_mcp.database import db_manager

def main():
    """الدالة الرئيسية لتشغيل الخادم"""
    parser = argparse.ArgumentParser(description="Twitter MCP Server - OAuth 2.0")
    parser.add_argument("--host", help="عنوان الخادم (افتراضي: 127.0.0.1)")
    parser.add_argument("--port", type=int, help="منفذ الخادم (افتراضي: 8000)")
    parser.add_argument("--debug", action="store_true", help="تفعيل وضع التطوير")
    parser.add_argument("--reload", action="store_true", help="إعادة التحميل التلقائي")
    
    args = parser.parse_args()
    
    # الحصول على الإعدادات
    settings = get_settings()
    
    # تطبيق المعاملات الممررة
    if args.host:
        settings.host = args.host
    if args.port:
        settings.port = args.port
    if args.debug:
        settings.debug = True
    
    # إنشاء قاعدة البيانات
    print("🗄️  إنشاء قاعدة البيانات...")
    try:
        db_manager.create_tables()
        print("✅ تم إنشاء قاعدة البيانات بنجاح")
    except Exception as e:
        print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
        sys.exit(1)
    
    # التحقق من إعدادات OAuth
    print("🔐 التحقق من إعدادات OAuth 2.0...")
    if not settings.validate_oauth_config():
        print("⚠️  تحذير: TWITTER_CLIENT_ID غير محدد")
        print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        print("📖 راجع README.md للحصول على تعليمات الإعداد")
    else:
        print("✅ تم التحقق من إعدادات OAuth 2.0")
    
    # عرض معلومات الخادم
    print("\n" + "="*60)
    print("🚀 Twitter MCP Server - OAuth 2.0")
    print("="*60)
    print(f"✅ الخادم يعمل على http://{settings.host}:{settings.port}")
    print(f"🌐 الصفحة الرئيسية: http://{settings.host}:{settings.port}/")
    print(f"📖 واجهة API: http://{settings.host}:{settings.port}/docs")
    print(f"🔐 صفحة المصادقة: http://{settings.host}:{settings.port}/auth")
    print(f"🗄️  قاعدة البيانات: {settings.database_url}")
    print(f"🔧 البيئة: {settings.environment}")
    print(f"🐛 وضع التطوير: {'مفعل' if settings.debug else 'معطل'}")
    print("="*60)
    print("💡 اضغط Ctrl+C لإيقاف الخادم")
    print("="*60 + "\n")
    
    # تشغيل الخادم
    try:
        uvicorn.run(
            "src.x_twitter_mcp.server:app",
            host=settings.host,
            port=settings.port,
            reload=args.reload or settings.debug,
            log_level=settings.get_log_level(),
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل الخادم: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
