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
    """مدير مصادقة OAuth 1.0a لـ Twitter (مثل التطبيق الذي يعمل)"""
    
    def __init__(self):
        # استخدام API Key و API Secret مباشرة
        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.redirect_uri = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # قاعدة بيانات للجلسات المؤقتة
        self.oauth_states = {}  # في الإنتاج، استخدم Redis أو قاعدة بيانات
        
        # التحقق من التكوين
        if not self.api_key or not self.api_secret:
            print("⚠️  تحذير: TWITTER_API_KEY أو TWITTER_API_SECRET غير محدد")
            print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        
    def generate_oauth_state(self) -> str:
        """إنشاء حالة OAuth عشوائية"""
        state = secrets.token_urlsafe(32)
        return state
    
    def get_simple_oauth_url(self) -> str:
        """إنشاء رابط OAuth 1.0a (مثل التطبيق الذي يعمل)
        
        Returns:
            str: رابط المصادقة الصحيح
        """
        if not self.api_key:
            raise ValueError("TWITTER_API_KEY غير محدد. يرجى إعداده في ملف .env")
        
        if not self.api_secret:
            raise ValueError("TWITTER_API_SECRET غير محدد. يرجى إعداده في ملف .env")
        
        try:
            # استخدام Tweepy OAuth 1.0a (مثل التطبيق الذي يعمل)
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            redirect_url = auth.get_authorization_url()
            
            # حفظ request_token للاستخدام لاحقاً
            self.oauth_states['request_token'] = auth.request_token
            
            return redirect_url
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def get_public_oauth_url(self) -> str:
        """إنشاء رابط OAuth 1.0a عام للجميع
        
        Returns:
            str: رابط المصادقة العام
        """
        # استخدام الرابط الصحيح لحل مشكلة redirect_after_login
        return self.get_simple_oauth_url()
    
    def get_authorization_url(self, username: str) -> Tuple[str, str]:
        """إنشاء رابط المصادقة لـ Twitter مع username محدد
        
        Args:
            username (str): اسم المستخدم المطلوب
            
        Returns:
            Tuple[str, str]: (رابط المصادقة، حالة OAuth)
        """
        if not self.api_key:
            raise ValueError("TWITTER_API_KEY غير محدد. يرجى إعداده في ملف .env")
        
        if not self.api_secret:
            raise ValueError("TWITTER_API_SECRET غير محدد. يرجى إعداده في ملف .env")
        
        # إنشاء حالة OAuth
        state = self.generate_oauth_state()
        
        try:
            # استخدام Tweepy OAuth 1.0a
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            redirect_url = auth.get_authorization_url()
            
            # حفظ الحالة مع اسم المستخدم
            self.oauth_states[state] = {
                "username": username,
                "timestamp": int(os.time()),
                "request_token": auth.request_token
            }
            
            return redirect_url, state
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def handle_public_callback(self, oauth_token: str, oauth_verifier: str) -> Dict:
        """معالجة callback من Twitter OAuth 1.0a بدون username محدد
        
        Args:
            oauth_token (str): رمز OAuth من Twitter
            oauth_verifier (str): رمز التحقق من Twitter
            
        Returns:
            Dict: نتيجة المصادقة
        """
        try:
            # استخدام Tweepy للحصول على access token
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.request_token = {'oauth_token': oauth_token, 'oauth_token_secret': oauth_verifier}
            
            # الحصول على access token
            auth.get_access_token(oauth_verifier)
            
            # إنشاء API client للحصول على معلومات المستخدم
            api = tweepy.API(auth, wait_on_rate_limit=True)
            user_info = api.verify_credentials()
            
            # استخدام username من Twitter
            twitter_username = user_info.screen_name
            if not twitter_username:
                return {
                    "success": False,
                    "error": "لم يتم العثور على username في معلومات المستخدم"
                }
            
            # حفظ الحساب في قاعدة البيانات
            success = db_manager.add_account(
                username=twitter_username,
                api_key=self.api_key,
                api_secret=self.api_secret,
                access_token=auth.access_token,
                access_token_secret=auth.access_token_secret,
                bearer_token="",  # OAuth 1.0a لا يستخدم bearer_token
                display_name=user_info.name or twitter_username
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '@{twitter_username}' بنجاح",
                    "user_info": {
                        "username": user_info.screen_name,
                        "name": user_info.name,
                        "id": user_info.id
                    },
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
    
    def handle_callback(self, oauth_token: str, oauth_verifier: str, state: str) -> Dict:
        """معالجة callback من Twitter OAuth 1.0a مع username محدد
        
        Args:
            oauth_token (str): رمز OAuth من Twitter
            oauth_verifier (str): رمز التحقق من Twitter
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
            # استخدام Tweepy للحصول على access token
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.request_token = {'oauth_token': oauth_token, 'oauth_token_secret': oauth_verifier}
            
            # الحصول على access token
            auth.get_access_token(oauth_verifier)
            
            # إنشاء API client للحصول على معلومات المستخدم
            api = tweepy.API(auth, wait_on_rate_limit=True)
            user_info = api.verify_credentials()
            
            # حفظ الحساب في قاعدة البيانات
            success = db_manager.add_account(
                username=username,
                api_key=self.api_key,
                api_secret=self.api_secret,
                access_token=auth.access_token,
                access_token_secret=auth.access_token_secret,
                bearer_token="",  # OAuth 1.0a لا يستخدم bearer_token
                display_name=user_info.name or username
            )
            
            if success:
                # حذف الحالة المؤقتة
                del self.oauth_states[state]
                
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '{username}' بنجاح",
                    "user_info": {
                        "username": user_info.screen_name,
                        "name": user_info.name,
                        "id": user_info.id
                    }
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
    
    def cleanup_expired_states(self):
        """تنظيف الحالات المنتهية الصلاحية"""
        import time
        current_time = int(time.time())
        expired_states = []
        
        for state, data in self.oauth_states.items():
            if isinstance(data, dict) and "timestamp" in data:
                if current_time - data["timestamp"] > 3600:  # ساعة واحدة
                    expired_states.append(state)
        
        for state in expired_states:
            del self.oauth_states[state]

# إنشاء مدير OAuth عام
oauth_manager = TwitterOAuthManager()
