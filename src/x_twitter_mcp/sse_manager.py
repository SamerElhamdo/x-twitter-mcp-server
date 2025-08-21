import asyncio
import json
import time
from typing import Dict, List, Optional, Set
from fastapi import HTTPException
from .database import db_manager
from .oauth_manager import oauth_manager

class SSEManager:
    """مدير Server-Sent Events للتواصل مع AI Agent"""
    
    def __init__(self):
        self.active_connections: Set[str] = set()
        self.connection_data: Dict[str, dict] = {}
        self.last_accounts_count = 0
        
    async def event_stream(self, connection_id: str, api_key: str):
        """دفق الأحداث للـ AI Agent"""
        try:
            # إضافة الاتصال للقائمة النشطة
            self.active_connections.add(connection_id)
            self.connection_data[connection_id] = {
                "api_key": api_key,
                "connected_at": time.time(),
                "last_activity": time.time()
            }
            
            # إرسال رسالة ترحيب
            yield f"data: {json.dumps({'type': 'connection', 'message': 'تم الاتصال بنجاح', 'connection_id': connection_id})}\n\n"
            
            # مراقبة التغييرات في قاعدة البيانات
            while connection_id in self.active_connections:
                try:
                    # فحص التغييرات في الحسابات
                    current_accounts = db_manager.get_all_accounts()
                    current_count = len(current_accounts)
                    
                    if current_count != self.last_accounts_count:
                        # إرسال تحديث
                        yield f"data: {json.dumps({'type': 'accounts_update', 'count': current_count, 'accounts': [acc.username for acc in current_accounts]})}\n\n"
                        self.last_accounts_count = current_count
                    
                    # تحديث آخر نشاط
                    if connection_id in self.connection_data:
                        self.connection_data[connection_id]["last_activity"] = time.time()
                    
                    # انتظار قبل الفحص التالي
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    # إرسال خطأ
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    await asyncio.sleep(10)  # انتظار أطول في حالة الخطأ
                    
        except asyncio.CancelledError:
            # إلغاء الاتصال
            yield f"data: {json.dumps({'type': 'disconnect', 'message': 'تم قطع الاتصال'})}\n\n"
        finally:
            # تنظيف الاتصال
            self.remove_connection(connection_id)
    
    def remove_connection(self, connection_id: str):
        """إزالة اتصال من القائمة النشطة"""
        if connection_id in self.active_connections:
            self.active_connections.remove(connection_id)
        if connection_id in self.connection_data:
            del self.connection_data[connection_id]
    
    def get_connection_info(self) -> dict:
        """الحصول على معلومات الاتصالات النشطة"""
        return {
            "active_connections": len(self.active_connections),
            "connections": [
                {
                    "id": conn_id,
                    "connected_at": data["connected_at"],
                    "last_activity": data["last_activity"],
                    "api_key": data["api_key"][:8] + "..."  # إخفاء جزء من API key
                }
                for conn_id, data in self.connection_data.items()
            ]
        }
    
    def broadcast_message(self, message: dict):
        """إرسال رسالة لجميع الاتصالات النشطة"""
        # في التنفيذ الحقيقي، ستقوم بإرسال الرسالة لجميع الاتصالات
        # هنا نطبع الرسالة للتوضيح
        print(f"Broadcasting message: {message}")

# إنشاء مدير SSE عام
sse_manager = SSEManager()
