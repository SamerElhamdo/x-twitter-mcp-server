import os
import secrets
import requests
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import tweepy
from .database import db_manager

# تحميل متغيرات البيئة من ملف .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class TwitterOAuthManager:
    """مدير مصادقة OAuth لـ Twitter"""
    
    def __init__(self):
        # يجب تعيين هذه المتغيرات في البيئة أو ملف التكوين
        self.client_id = os.getenv("TWITTER_CLIENT_ID", "")
        self.client_secret = os.getenv("TWITTER_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # قاعدة بيانات للجلسات المؤقتة
        self.oauth_states = {}  # في الإنتاج، استخدم Redis أو قاعدة بيانات
        
        # Twitter OAuth endpoints
        self.authorization_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        
        # التحقق من التكوين
        if not self.client_id or not self.client_secret:
            print("⚠️  تحذير: TWITTER_CLIENT_ID أو TWITTER_CLIENT_SECRET غير محدد")
            print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        
    def generate_oauth_state(self) -> str:
        """إنشاء حالة OAuth عشوائية"""
        state = secrets.token_urlsafe(32)
        return state
    
    def get_public_oauth_url(self) -> str:
        """إنشاء رابط OAuth عام للجميع
        
        Returns:
            str: رابط المصادقة العام
        """
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        # معاملات المصادقة العامة
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "tweet.read tweet.write users.read follows.read offline.access",
            "code_challenge_method": "S256",
            "code_challenge": self._generate_code_challenge()
        }
        
        # إنشاء رابط المصادقة العام
        auth_url = f"{self.authorization_url}?{urlencode(params)}"
        return auth_url
    
    def get_authorization_url(self, username: str) -> Tuple[str, str]:
        """إنشاء رابط المصادقة لـ Twitter مع username محدد
        
        Args:
            username (str): اسم المستخدم المطلوب
            
        Returns:
            Tuple[str, str]: (رابط المصادقة، حالة OAuth)
        """
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        if not self.client_secret:
            raise ValueError("TWITTER_CLIENT_SECRET غير محدد. يرجى إعداده في ملف .env")
        
        # إنشاء حالة OAuth
        state = self.generate_oauth_state()
        
        # حفظ الحالة مع اسم المستخدم
        self.oauth_states[state] = {
            "username": username,
            "timestamp": int(os.time())
        }
        
        # معاملات المصادقة
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "tweet.read tweet.write users.read follows.read offline.access",
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": self._generate_code_challenge()
        }
        
        # إنشاء رابط المصادقة
        auth_url = f"{self.authorization_url}?{urlencode(params)}"
        
        return auth_url, state
    
    def handle_public_callback(self, code: str) -> Dict:
        """معالجة callback من Twitter OAuth بدون username محدد
        
        Args:
            code (str): رمز المصادقة من Twitter
            
        Returns:
            Dict: نتيجة المصادقة
        """
        try:
            # استبدال رمز المصادقة بـ access token
            token_response = self._exchange_code_for_token(code)
            
            if not token_response.get("access_token"):
                return {
                    "success": False,
                    "error": "فشل في الحصول على access token"
                }
            
            # الحصول على معلومات المستخدم
            user_info = self._get_user_info(token_response["access_token"])
            
            # استخدام username من Twitter
            twitter_username = user_info.get("username", "")
            if not twitter_username:
                return {
                    "success": False,
                    "error": "لم يتم العثور على username في معلومات المستخدم"
                }
            
            # حفظ الحساب في قاعدة البيانات
            success = db_manager.add_account(
                username=twitter_username,
                api_key=self.client_id,
                api_secret=self.client_secret,
                access_token=token_response["access_token"],
                access_token_secret="",  # OAuth 2.0 لا يستخدم access_token_secret
                bearer_token=token_response.get("access_token", ""),
                display_name=user_info.get("name", twitter_username)
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '@{twitter_username}' بنجاح",
                    "user_info": user_info,
                    "username": twitter_username
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في حفظ الحساب"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في المصادقة: {str(e)}"
            }
    
    def handle_callback(self, code: str, state: str) -> Dict:
        """معالجة callback من Twitter OAuth مع username محدد
        
        Args:
            code (str): رمز المصادقة من Twitter
            state (str): حالة OAuth
            
        Returns:
            Dict: نتيجة المصادقة
        """
        # التحقق من صحة الحالة
        if state not in self.oauth_states:
            return {
                "success": False,
                "error": "حالة OAuth غير صالحة"
            }
        
        oauth_data = self.oauth_states[state]
        username = oauth_data["username"]
        
        try:
            # استبدال رمز المصادقة بـ access token
            token_response = self._exchange_code_for_token(code)
            
            if not token_response.get("access_token"):
                return {
                    "success": False,
                    "error": "فشل في الحصول على access token"
                }
            
            # الحصول على معلومات المستخدم
            user_info = self._get_user_info(token_response["access_token"])
            
            # حفظ الحساب في قاعدة البيانات
            success = db_manager.add_account(
                username=username,
                api_key=self.client_id,
                api_secret=self.client_secret,
                access_token=token_response["access_token"],
                access_token_secret="",  # OAuth 2.0 لا يستخدم access_token_secret
                bearer_token=token_response.get("access_token", ""),
                display_name=user_info.get("name", username)
            )
            
            if success:
                # حذف الحالة المؤقتة
                del self.oauth_states[state]
                
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '{username}' بنجاح",
                    "user_info": user_info
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في حفظ الحساب"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في المصادقة: {str(e)}"
            }
    
    def _generate_code_challenge(self) -> str:
        """إنشاء code challenge لـ PKCE"""
        # في الإنتاج، استخدم مكتبة مناسبة لـ PKCE
        import hashlib
        import base64
        
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # حفظ code_verifier مع الحالة
        return code_challenge
    
    def _exchange_code_for_token(self, code: str) -> Dict:
        """استبدال رمز المصادقة بـ access token"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self._get_basic_auth()}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(self.token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"فشل في استبدال الرمز: {response.text}")
    
    def _get_basic_auth(self) -> str:
        """إنشاء Basic Auth header"""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded
    
    def _get_user_info(self, access_token: str) -> Dict:
        """الحصول على معلومات المستخدم من Twitter"""
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(
            "https://api.twitter.com/2/users/me",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {})
        else:
            raise Exception(f"فشل في الحصول على معلومات المستخدم: {response.text}")
    
    def get_public_auth_url(self, username: str) -> str:
        """إنشاء رابط مصادقة عام للمستخدمين
        
        Args:
            username (str): اسم المستخدم المطلوب
            
        Returns:
            str: رابط المصادقة العام
        """
        auth_url, _ = self.get_authorization_url(username)
        return auth_url
    
    def cleanup_expired_states(self):
        """تنظيف الحالات المنتهية الصلاحية"""
        import time
        current_time = int(time.time())
        expired_states = []
        
        for state, data in self.oauth_states.items():
            if current_time - data["timestamp"] > 3600:  # ساعة واحدة
                expired_states.append(state)
        
        for state in expired_states:
            del self.oauth_states[state]

# إنشاء مدير OAuth عام
oauth_manager = TwitterOAuthManager()
