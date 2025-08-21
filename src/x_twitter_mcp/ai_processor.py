import re
import time
import json
from typing import Dict, Optional
from .database import db_manager
from .oauth_manager import oauth_manager

class AIProcessor:
    """معالج طلبات AI من n8n"""
    
    def __init__(self):
        self.commands = {
            "add_account": ["أضف", "add", "create", "new", "حساب", "account"],
            "list_accounts": ["عرض", "show", "list", "الحسابات", "accounts", "جميع"],
            "test_account": ["اختبر", "test", "تحقق", "verify", "صحة"],
            "delete_account": ["احذف", "delete", "remove", "حذف", "إزالة"],
            "help": ["مساعدة", "help", "ماذا", "كيف", "أوامر"]
        }
    
    async def process_message(self, message: str, user_id: str = "unknown") -> dict:
        """معالجة رسالة AI وتحديد الإجراء المطلوب"""
        
        message_lower = message.lower()
        
        # تحديد نوع الطلب
        request_type = self._identify_request_type(message_lower)
        
        if request_type == "add_account":
            return await self._handle_add_account(message, user_id)
        elif request_type == "list_accounts":
            return await self._handle_list_accounts(user_id)
        elif request_type == "test_account":
            return await self._handle_test_account(message, user_id)
        elif request_type == "delete_account":
            return await self._handle_delete_account(message, user_id)
        elif request_type == "help":
            return await self._handle_help()
        else:
            return await self._handle_unknown_request(message)
    
    def _identify_request_type(self, message: str) -> str:
        """تحديد نوع الطلب بناءً على الكلمات المفتاحية"""
        for request_type, keywords in self.commands.items():
            if any(keyword in message for keyword in keywords):
                return request_type
        return "unknown"
    
    async def _handle_add_account(self, message: str, user_id: str) -> dict:
        """معالجة طلب إضافة حساب جديد"""
        try:
            # استخراج username
            username_match = re.search(r'@(\w+)', message)
            if not username_match:
                return {
                    "success": False,
                    "action": "add_account",
                    "message": "يرجى تحديد username (مثال: @username)",
                    "timestamp": time.time()
                }
            
            username = username_match.group(1)
            
            # التحقق من عدم وجود الحساب
            existing_account = db_manager.get_account(username)
            if existing_account:
                return {
                    "success": False,
                    "action": "add_account",
                    "message": f"الحساب @{username} موجود بالفعل",
                    "timestamp": time.time()
                }
            
            # إنشاء رابط OAuth
            auth_url = oauth_manager.get_public_oauth_url()
            
            return {
                "success": True,
                "action": "add_account",
                "username": username,
                "auth_url": auth_url,
                "message": f"تم إنشاء رابط المصادقة لـ @{username}. انقر عليه لربط الحساب.",
                "instructions": [
                    "1. انقر على الرابط أدناه",
                    "2. سجل دخولك لـ Twitter",
                    "3. أوافق على الصلاحيات",
                    "4. سيتم ربط الحساب تلقائياً"
                ],
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": "add_account",
                "message": f"فشل في إنشاء رابط المصادقة: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _handle_list_accounts(self, user_id: str) -> dict:
        """معالجة طلب عرض الحسابات"""
        try:
            accounts = db_manager.get_all_accounts()
            
            if not accounts:
                return {
                    "success": True,
                    "action": "list_accounts",
                    "accounts": [],
                    "count": 0,
                    "message": "لا توجد حسابات مرتبطة حالياً",
                    "timestamp": time.time()
                }
            
            account_list = []
            for acc in accounts:
                account_list.append({
                    "username": acc.username,
                    "display_name": acc.display_name or "غير محدد",
                    "status": "نشط" if acc.is_active else "غير نشط",
                    "created_at": acc.created_at.isoformat() if acc.created_at else "غير محدد",
                    "last_used": acc.last_used.isoformat() if acc.last_used else "غير محدد"
                })
            
            return {
                "success": True,
                "action": "list_accounts",
                "accounts": account_list,
                "count": len(accounts),
                "message": f"تم العثور على {len(accounts)} حساب مرتبط",
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": "list_accounts",
                "message": f"فشل في جلب الحسابات: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _handle_test_account(self, message: str, user_id: str) -> dict:
        """معالجة طلب اختبار حساب"""
        try:
            # استخراج username
            username_match = re.search(r'@(\w+)', message)
            if not username_match:
                return {
                    "success": False,
                    "action": "test_account",
                    "message": "يرجى تحديد username (مثال: @username)",
                    "timestamp": time.time()
                }
            
            username = username_match.group(1)
            
            # اختبار الحساب
            is_valid = db_manager.test_credentials(username)
            
            return {
                "success": True,
                "action": "test_account",
                "username": username,
                "is_valid": is_valid,
                "message": f"الحساب @{username} {'صالح ويعمل بشكل طبيعي' if is_valid else 'غير صالح أو غير موجود'}",
                "status": "صالح" if is_valid else "غير صالح",
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": "test_account",
                "message": f"فشل في اختبار الحساب: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _handle_delete_account(self, message: str, user_id: str) -> dict:
        """معالجة طلب حذف حساب"""
        try:
            # استخراج username
            username_match = re.search(r'@(\w+)', message)
            if not username_match:
                return {
                    "success": False,
                    "action": "delete_account",
                    "message": "يرجى تحديد username (مثال: @username)",
                    "timestamp": time.time()
                }
            
            username = username_match.group(1)
            
            # حذف الحساب
            success = db_manager.delete_account(username)
            
            if success:
                return {
                    "success": True,
                    "action": "delete_account",
                    "username": username,
                    "deleted": True,
                    "message": f"تم حذف الحساب @{username} بنجاح",
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "action": "delete_account",
                    "username": username,
                    "deleted": False,
                    "message": f"فشل في حذف الحساب @{username} أو الحساب غير موجود",
                    "timestamp": time.time()
                }
                
        except Exception as e:
            return {
                "success": False,
                "action": "delete_account",
                "message": f"فشل في حذف الحساب: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _handle_help(self) -> dict:
        """معالجة طلب المساعدة"""
        return {
            "success": True,
            "action": "help",
            "message": "يمكنني مساعدتك في إدارة حسابات Twitter:",
            "commands": [
                {
                    "command": "أضف حساب @username",
                    "description": "إنشاء رابط مصادقة لربط حساب جديد"
                },
                {
                    "command": "عرض الحسابات",
                    "description": "عرض جميع الحسابات المرتبطة"
                },
                {
                    "command": "اختبر @username",
                    "description": "اختبار صحة حساب معين"
                },
                {
                    "command": "احذف @username",
                    "description": "حذف حساب معين"
                },
                {
                    "command": "مساعدة",
                    "description": "عرض هذه القائمة"
                }
            ],
            "examples": [
                "أضف حساب @john_doe",
                "عرض جميع الحسابات",
                "اختبر @test_user",
                "احذف @old_account"
            ],
            "timestamp": time.time()
        }
    
    async def _handle_unknown_request(self, message: str) -> dict:
        """معالجة الطلبات غير المفهومة"""
        return {
            "success": False,
            "action": "unknown",
            "message": "لم أفهم طلبك. اكتب 'مساعدة' لمعرفة الأوامر المتاحة.",
            "suggestions": [
                "أضف حساب @username",
                "عرض الحسابات",
                "اختبر @username",
                "احذف @username"
            ],
            "timestamp": time.time()
        }

# إنشاء معالج AI عام
ai_processor = AIProcessor()
