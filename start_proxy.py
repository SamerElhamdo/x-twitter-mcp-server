#!/usr/bin/env python3
"""
تشغيل mcp-proxy مع الخادم المحدث
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
    
    print("🚀 Twitter MCP Server - mcp-proxy")
    print("=" * 50)
    print("🔧 خادم MCP async محدث")
    print("⚡ متوافق مع mcp-proxy")
    print("🌐 SSE endpoint للاتصال بـ n8n")
    print("=" * 50)
    print()
    
    # التحقق من وجود الملفات
    if not Path("mcp_server_async.py").exists():
        print("❌ ملف mcp_server_async.py غير موجود")
        sys.exit(1)
    
    print("✅ الملفات موجودة")
    print("🚀 بدء تشغيل mcp-proxy...")
    print()
    
    try:
        # تشغيل mcp-proxy مع الخادم الجديد
        process = subprocess.Popen([
            "mcp-proxy",
            "--host=0.0.0.0",
            "--port=9000",
            "--allow-origin=*",
            "--",
            "python",
            "mcp_server_async.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        
        # انتظار للتأكد من بدء التشغيل
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ mcp-proxy يعمل بنجاح!")
            print("📍 Endpoint: http://0.0.0.0:9000")
            print("🌐 SSE: http://0.0.0.0:9000/sse")
            print("📱 في n8n: http://YOUR_IP:9000/sse")
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
    main()
