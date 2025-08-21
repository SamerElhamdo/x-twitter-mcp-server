#!/usr/bin/env python3
"""
Twitter MCP Server - تشغيل سريع وشامل
"""

import subprocess
import sys
import time
import signal
import threading
from pathlib import Path

def signal_handler(signum, frame):
    """معالج إشارات الإيقاف"""
    print(f"\n🛑 تم استلام إشارة {signum}")
    print("⏳ إيقاف جميع الخوادم...")
    sys.exit(0)

def run_server(name, cmd, delay=0):
    """تشغيل خادم مع تأخير اختياري"""
    time.sleep(delay)
    try:
        print(f"🚀 بدء تشغيل {name}...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # انتظار للتأكد من بدء التشغيل
        time.sleep(2)
        
        if process.poll() is None:
            print(f"✅ {name} يعمل بنجاح!")
            return process
        else:
            print(f"❌ فشل في بدء تشغيل {name}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في تشغيل {name}: {e}")
        return None

def monitor_process(name, process):
    """مراقبة عملية مع تصفية الرسائل"""
    if not process:
        return
        
    while True:
        output = process.stdout.readline()
        if output:
            # تصفية الرسائل غير الضرورية
            if any(skip in output for skip in [
                "WARNING", "Invalid HTTP request", "DeprecationWarning"
            ]):
                continue
            print(f"[{name}] {output.strip()}")
        
        # التحقق من حالة العملية
        if process.poll() is not None:
            print(f"⚠️ {name} توقف")
            break

def main():
    """الدالة الرئيسية"""
    
    # إعداد معالج الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Twitter MCP Server - تشغيل سريع وشامل")
    print("=" * 50)
    print("📊 إعدادات محسنة للأداء السريع")
    print("🔧 إصلاح DeprecationWarning")
    print("⚡ تحسين الاستجابة")
    print("🔇 تقليل warnings غير الضرورية")
    print("=" * 50)
    print()
    
    # التحقق من وجود الملفات
    if not Path("run_server.py").exists():
        print("❌ ملف run_server.py غير موجود")
        sys.exit(1)
    
    # تشغيل MCP Server
    mcp_process = run_server(
        "MCP Server",
        ["python", "run_server.py"]
    )
    
    if not mcp_process:
        print("❌ فشل في بدء MCP Server")
        sys.exit(1)
    
    # انتظار قليل
    time.sleep(3)
    
    # تشغيل mcp-proxy
    proxy_process = run_server(
        "MCP Proxy",
        [
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
    )
    
    if not proxy_process:
        print("❌ فشل في بدء MCP Proxy")
        mcp_process.terminate()
        sys.exit(1)
    
    print()
    print("🎉 جميع الخوادم تعمل بنجاح!")
    print("=" * 50)
    print("📋 معلومات الاتصال:")
    print("   - MCP Server: http://localhost:8000")
    print("   - MCP Proxy SSE: http://localhost:9000/sse")
    print("   - في n8n: http://YOUR_IP:9000/sse")
    print("=" * 50)
    print()
    print("⏹️  للإيقاف: اضغط Ctrl+C")
    print()
    
    # بدء مراقبة العمليات في خيوط منفصلة
    mcp_thread = threading.Thread(
        target=monitor_process, 
        args=("MCP", mcp_process),
        daemon=True
    )
    proxy_thread = threading.Thread(
        target=monitor_process, 
        args=("PROXY", proxy_process),
        daemon=True
    )
    
    mcp_thread.start()
    proxy_thread.start()
    
    try:
        # انتظار انتهاء العمليات
        while mcp_process.poll() is None and proxy_process.poll() is None:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخوادم بواسطة المستخدم")
    finally:
        # إيقاف العمليات
        if mcp_process.poll() is None:
            mcp_process.terminate()
            mcp_process.wait()
            print("✅ تم إيقاف MCP Server")
            
        if proxy_process.poll() is None:
            proxy_process.terminate()
            proxy_process.wait()
            print("✅ تم إيقاف MCP Proxy")

if __name__ == "__main__":
    main()
