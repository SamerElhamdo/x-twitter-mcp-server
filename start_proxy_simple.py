#!/usr/bin/env python3
"""
تشغيل بسيط لـ mcp-proxy مع Twitter MCP Server
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

def signal_handler(signum, frame):
    """معالج إشارات الإيقاف"""
    print(f"\n🛑 تم استلام إشارة {signum}")
    print("⏳ إيقاف mcp-proxy...")
    sys.exit(0)

def main():
    """الدالة الرئيسية"""
    
    # إعداد معالج الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 تشغيل mcp-proxy مع Twitter MCP Server")
    print("=" * 50)
    print("📊 إعدادات محسنة للأداء")
    print("🔧 متوافق مع async/await")
    print("⚡ استجابة سريعة")
    print("=" * 50)
    print()
    
    # أوامر mcp-proxy محسنة
    cmd = [
        "mcp-proxy",
        "--host=0.0.0.0",
        "--port=9000",
        "--allow-origin=*",
        "--log-level=warning",
        "--timeout=30",
        "--max-connections=100",
        "--",
        "python", "mcp_server_async.py"
    ]
    
    try:
        print(f"🔧 تشغيل: {' '.join(cmd)}")
        print("📍 Endpoint: http://0.0.0.0:9000/sse")
        print("🌐 في n8n: http://YOUR_IP:9000/sse")
        print()
        print("⏳ انتظار بدء التشغيل...")
        
        # تشغيل mcp-proxy
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # انتظار قليل للتأكد من بدء التشغيل
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ mcp-proxy يعمل بنجاح!")
            print("📱 يمكنك الآن الاتصال من n8n")
            print()
            print("📋 معلومات الاتصال:")
            print("   - Endpoint: http://0.0.0.0:9000/sse")
            print("   - Transport: SSE")
            print("   - Status: نشط")
            print()
            print("⏹️  للإيقاف: اضغط Ctrl+C")
            
            # مراقبة العملية
            while True:
                output = process.stdout.readline()
                if output:
                    # تصفية الرسائل غير الضرورية
                    if any(skip in output for skip in [
                        "WARNING", "Invalid HTTP request", "DeprecationWarning"
                    ]):
                        continue
                    print(output.strip())
                
                # التحقق من حالة العملية
                if process.poll() is not None:
                    break
                    
        else:
            print("❌ فشل في بدء تشغيل mcp-proxy")
            return_code = process.returncode
            print(f"📊 رمز الإرجاع: {return_code}")
            
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف mcp-proxy بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل mcp-proxy: {e}")
    finally:
        # إيقاف العملية
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait()
            print("✅ تم إيقاف mcp-proxy")

if __name__ == "__main__":
    # التحقق من وجود mcp-proxy
    try:
        subprocess.run(["mcp-proxy", "--help"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ mcp-proxy غير مثبت")
        print("💡 قم بتثبيته: pip install mcp-proxy")
        sys.exit(1)
    
    # التحقق من وجود الملف الجديد
    if not Path("mcp_server_async.py").exists():
        print("❌ ملف mcp_server_async.py غير موجود")
        sys.exit(1)
    
    # تشغيل mcp-proxy
    main()
