#!/usr/bin/env python3
"""
Twitter MCP Server - تشغيل بسيط
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

def signal_handler(signum, frame):
    """معالج إشارات الإيقاف"""
    print(f"\n🛑 تم استلام إشارة {signum}")
    print("⏳ إيقاف الخادم...")
    sys.exit(0)

def main():
    """الدالة الرئيسية"""
    
    # إعداد معالج الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Twitter MCP Server - تشغيل بسيط")
    print("=" * 50)
    print("📊 إعدادات محسنة للأداء")
    print("🔧 إصلاح DeprecationWarning")
    print("⚡ استجابة سريعة")
    print("=" * 50)
    print()
    
    # التحقق من وجود الملفات
    if not Path("run_server.py").exists():
        print("❌ ملف run_server.py غير موجود")
        sys.exit(1)
    
    print("✅ الملفات موجودة")
    print("🚀 بدء تشغيل الخادم...")
    print()
    
    try:
        # تشغيل الخادم
        process = subprocess.Popen(
            ["python", "run_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # انتظار للتأكد من بدء التشغيل
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ الخادم يعمل بنجاح!")
            print("📍 Endpoint: http://127.0.0.1:8000")
            print("📖 واجهة API: http://127.0.0.1:8000/docs")
            print()
            print("⏹️  للإيقاف: اضغط Ctrl+C")
            print()
            
            # مراقبة العملية
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                
                # التحقق من حالة العملية
                if process.poll() is not None:
                    break
                    
        else:
            print("❌ فشل في بدء تشغيل الخادم")
            return_code = process.returncode
            print(f"📊 رمز الإرجاع: {return_code}")
            
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل الخادم: {e}")
    finally:
        # إيقاف العملية
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait()
            print("✅ تم إيقاف الخادم")

if __name__ == "__main__":
    main()
