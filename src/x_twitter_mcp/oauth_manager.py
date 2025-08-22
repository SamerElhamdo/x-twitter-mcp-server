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
    
    def get_simple_oauth_url(self) -> str:
        """إنشاء رابط OAuth 2.0 (Authorization Code + PKCE)
        
        Returns:
            str: رابط المصادقة الصحيح
        """
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        try:
            # استخدام Tweepy OAuth 2.0
            oauth2_handler = tweepy.OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes,
                client_secret=self.client_secret or None
            )
            
            # إنشاء رابط المصادقة مع PKCE
            auth_url = oauth2_handler.get_authorization_url(
                state=secrets.token_urlsafe(24),
                code_challenge_method="S256"
            )
            
            # حفظ handler للاستخدام لاحقاً
            self.oauth_states['oauth2_handler'] = oauth2_handler
            
            return auth_url
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def get_public_oauth_url(self) -> str:
        """إنشاء رابط OAuth 2.0 عام للجميع
        
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
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        # إنشاء حالة OAuth
        state = self.generate_oauth_state()
        
        try:
            # استخدام Tweepy OAuth 2.0
            oauth2_handler = tweepy.OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes,
                client_secret=self.client_secret or None
            )
            
            # إنشاء رابط المصادقة مع PKCE
            redirect_url = oauth2_handler.get_authorization_url(
                state=state,
                code_challenge_method="S256"
            )
            
            # حفظ الحالة مع اسم المستخدم
            self.oauth_states[state] = {
                "username": username,
                "timestamp": int(time.time()),
                "oauth2_handler": oauth2_handler
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
            oauth2_handler = tweepy.OAuth2UserHandler(
                client_id=account.api_key,  # client_id
                redirect_uri=self.redirect_uri,
                scope=self.scopes,
                client_secret=account.api_secret  # client_secret
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
        if state not in self.oauth_states:
            return {
                "success": False,
                "error": "حالة OAuth غير صالحة"
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
            
            access_token = access_token = token_data.get("access_token")
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

# إنشاء مدير OAuth عام
oauth_manager = TwitterOAuthManager()
