import os
import secrets
import requests
import time
import json
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import tweepy
from tweepy.auth import OAuth2UserHandler
from .database import db_manager

# تحميل متغيرات البيئة من ملف .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class TwitterOAuthManager:
    """مدير مصادقة OAuth 2.0 لـ Twitter (Authorization Code + PKCE)"""
    
    def __init__(self):
        # OAuth 2.0 credentials
        self.client_id = os.getenv("TWITTER_CLIENT_ID", "")
        self.client_secret = os.getenv("TWITTER_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # OAuth 2.0 scopes
        self.scopes = [
            "tweet.read",
            "tweet.write", 
            "users.read",
            "like.read",
            "like.write",
            "offline.access"
        ]
        
        # قاعدة بيانات للجلسات المؤقتة
        self.oauth_states = {}  # في الإنتاج، استخدم Redis أو قاعدة بيانات
        
        # التحقق من التكوين
        if not self.client_id:
            print("⚠️  تحذير: TWITTER_CLIENT_ID غير محدد")
            print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        
    def generate_oauth_state(self) -> str:
        """إنشاء حالة OAuth عشوائية"""
        state = secrets.token_urlsafe(32)
        return state
    
    def get_simple_oauth_url(self) -> Tuple[str, str]:
        """إنشاء رابط OAuth 2.0 (Authorization Code + PKCE)
        
        Returns:
            Tuple[str, str]: (رابط المصادقة، حالة OAuth)
        """
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        # إنشاء حالة OAuth
        state = self.generate_oauth_state()
        
        try:
            # استخدام Tweepy OAuth 2.0 مع PKCE
            # Twitter API v2 يتطلب PKCE
            oauth2_handler = OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes
            )
            
            # إنشاء رابط المصادقة مع PKCE
            # OAuth2UserHandler يدعم PKCE تلقائياً
            # Twitter API v2 يتطلب PKCE
            auth_url = oauth2_handler.get_authorization_url()
            
            # معلومات تشخيصية للمساعدة في حل المشكلة
            print(f"🔗 رابط المصادقة: {auth_url}")
            print(f"🆔 Client ID: {self.client_id}")
            print(f"🔄 Redirect URI: {self.redirect_uri}")
            print(f"📋 Scopes: {', '.join(self.scopes)}")
            print(f"🔑 State: {state}")
            
            # حفظ الحالة مع username افتراضي
            self.oauth_states[state] = {
                "username": "default_user",
                "timestamp": int(time.time()),
                "oauth2_handler": oauth2_handler
            }
            
            # معلومات تشخيصية
            print(f"💾 تم حفظ state: {state}")
            print(f"👤 للمستخدم: default_user")
            print(f"📊 إجمالي الحالات: {len(self.oauth_states)}")
            print(f"🔑 الحالات المتاحة: {list(self.oauth_states.keys())}")
            
            return auth_url, state
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def get_public_oauth_url(self) -> str:
        """إنشاء رابط OAuth 2.0 عام للجميع
        
        Returns:
            str: رابط المصادقة العام
        """
        # استخدام الرابط الصحيح لحل مشكلة redirect_after_login
        auth_url, state = self.get_simple_oauth_url()
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
        
        # إنشاء حالة OAuth
        state = self.generate_oauth_state()
        
        try:
            # استخدام Tweepy OAuth 2.0 مع PKCE
            oauth2_handler = OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes
            )
            
            # إنشاء رابط المصادقة مع PKCE
            # OAuth2UserHandler يدعم PKCE تلقائياً
            # Twitter API v2 يتطلب PKCE
            redirect_url = oauth2_handler.get_authorization_url()
            
            # معلومات تشخيصية
            print(f"🔗 رابط المصادقة للمستخدم {username}: {redirect_url}")
            print(f"🔑 State: {state}")
            
            # حفظ الحالة مع اسم المستخدم
            self.oauth_states[state] = {
                "username": username,
                "timestamp": int(time.time()),
                "oauth2_handler": oauth2_handler
            }
            
            # معلومات تشخيصية
            print(f"💾 تم حفظ state: {state}")
            print(f"👤 للمستخدم: {username}")
            print(f"📊 إجمالي الحالات: {len(self.oauth_states)}")
            print(f"🔑 الحالات المتاحة: {list(self.oauth_states.keys())}")
            
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
        # هذه الدالة لم تعد مدعومة في OAuth 2.0
        # يمكن إزالتها أو تحديثها لتعمل مع OAuth 2.0
        return {
            "success": False,
            "error": "هذه الدالة لم تعد مدعومة في OAuth 2.0. استخدم handle_callback بدلاً منها."
        }
    
    def create_client_for_user(self, username: str) -> Optional[tweepy.Client]:
        """إنشاء عميل Twitter للمستخدم المحدد
        
        Args:
            username (str): اسم المستخدم
            
        Returns:
            Optional[tweepy.Client]: عميل Twitter أو None إذا فشل
        """
        try:
            # الحصول على الحساب من قاعدة البيانات
            account = db_manager.get_account(username)
            if not account:
                return None
            
            # التحقق من نوع المصادقة
            if account.auth_type == "oauth2":
                # استخدام OAuth 2.0
                client = tweepy.Client(
                    access_token=account.access_token,
                    consumer_key=account.api_key,  # client_id
                    consumer_secret=account.api_secret  # client_secret
                )
                return client
            else:
                # استخدام OAuth 1.0a (للتوافق مع الحسابات القديمة)
                client = tweepy.Client(
                    consumer_key=account.api_key,
                    consumer_secret=account.api_secret,
                    access_token=account.access_token,
                    access_token_secret=account.access_token_secret
                )
                return client
                
        except Exception as e:
            print(f"خطأ في إنشاء عميل Twitter: {e}")
            return None
    
    def refresh_access_token(self, username: str) -> Optional[str]:
        """تجديد access token للمستخدم
        
        Args:
            username (str): اسم المستخدم
            
        Returns:
            Optional[str]: access token الجديد أو None إذا فشل
        """
        try:
            # الحصول على الحساب من قاعدة البيانات
            account = db_manager.get_account(username)
            if not account or account.auth_type != "oauth2":
                return None
            
            if not account.refresh_token:
                return None
            
            # إنشاء OAuth 2.0 handler
            oauth2_handler = OAuth2UserHandler(
                client_id=account.api_key,  # client_id
                redirect_uri=self.redirect_uri,
                scope=self.scopes
            )
            
            # تجديد التوكن
            token_data = oauth2_handler.refresh_token(
                token_url="https://api.twitter.com/2/oauth2/token",
                refresh_token=account.refresh_token
            )
            
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token", account.refresh_token)
            expires_in = token_data.get("expires_in", 0)
            
            # حساب تاريخ انتهاء الصلاحية
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # تحديث قاعدة البيانات
            db_manager.update_tokens(
                username=username,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at
            )
            
            return new_access_token
            
        except Exception as e:
            print(f"خطأ في تجديد access token: {e}")
            return None
    
    def handle_callback(self, state: str, code: str) -> Dict:
        """معالجة callback من Twitter OAuth 2.0
        
        Args:
            state (str): حالة OAuth
            code (str): رمز التفويض من Twitter
            
        Returns:
            Dict: نتيجة المصادقة
        """
        # التحقق من صحة الحالة
        print(f"🔍 البحث عن state: {state}")
        print(f"📋 الحالات المتاحة: {list(self.oauth_states.keys())}")
        print(f"📊 عدد الحالات: {len(self.oauth_states)}")
        
        if state not in self.oauth_states:
            return {
                "success": False,
                "error": f"حالة OAuth غير صالحة. State: {state}, المتاح: {list(self.oauth_states.keys())}"
            }
        
        oauth_data = self.oauth_states[state]
        username = oauth_data["username"]
        oauth2_handler = oauth_data.get("oauth2_handler")
        
        if not oauth2_handler:
            return {
                "success": False,
                "error": "بيانات الحالة غير مكتملة"
            }
        
        try:
            # استخدام OAuth 2.0 handler لإكمال المصادقة
            token_data = oauth2_handler.fetch_token(code=code)
            
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 0)
            
            # حساب تاريخ انتهاء الصلاحية
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # إنشاء عميل Twitter للحصول على معلومات المستخدم
            client = tweepy.Client(access_token=access_token)
            me = client.get_me(user_auth=True)
            
            if not me.data:
                return {
                    "success": False,
                    "error": "فشل في الحصول على معلومات المستخدم"
                }
            
            user_data = me.data
            
            # حفظ الحساب في قاعدة البيانات
            success = db_manager.add_account(
                username=username,
                api_key=self.client_id,  # استخدام client_id كـ api_key للتوافق
                api_secret=self.client_secret or "",
                access_token=access_token,
                access_token_secret="",  # OAuth 2.0 لا يحتاج access_token_secret
                bearer_token="",  # OAuth 2.0 لا يحتاج bearer token
                display_name=user_data.name,
                user_id=str(user_data.id),
                refresh_token=refresh_token,
                expires_at=expires_at,
                scopes=json.dumps(self.scopes),
                auth_type="oauth2"
            )
            
            if success:
                # حذف الحالة المؤقتة
                del self.oauth_states[state]
                
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '{username}' بنجاح",
                    "user_info": {
                        "username": user_data.username,
                        "name": user_data.name,
                        "id": str(user_data.id)
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

# إنشاء نسخة واحدة من مدير المصادقة
oauth_manager = TwitterOAuthManager()
