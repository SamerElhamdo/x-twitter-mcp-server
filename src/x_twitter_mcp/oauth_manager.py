import os
import time
import secrets
import tweepy
from typing import Optional, Dict, Tuple
from .database import db_manager

# تحميل متغيرات البيئة من ملف .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class TwitterOAuthManager:
    """مدير مصادقة OAuth 2.0 لـ Twitter API v2"""
    
    def __init__(self):
        # متغيرات OAuth 2.0
        self.client_id = os.getenv("TWITTER_CLIENT_ID", "")
        self.client_secret = os.getenv("TWITTER_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # الصلاحيات المطلوبة
        self.scopes = ["tweet.read", "tweet.write", "users.read", "offline.access"]
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        
        # قاعدة بيانات للجلسات المؤقتة
        self.oauth_states = {}
        
        # التحقق من التكوين
        if not self.client_id:
            print("⚠️  تحذير: TWITTER_CLIENT_ID غير محدد")
            print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        
    def save_tokens(self, username: str, tokens: dict):
        """حفظ الـ tokens في قاعدة البيانات الرئيسية"""
        account = db_manager.get_account(username)
        if account:
            db_manager.add_account(
                username=username,
                api_key=account.api_key,
                api_secret=account.api_secret,
                access_token=tokens["access_token"],
                access_token_secret=account.access_token_secret,
                bearer_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                display_name=account.display_name
            )
    
    def load_tokens(self, username: str) -> Optional[dict]:
        """تحميل الـ tokens من قاعدة البيانات الرئيسية"""
        account = db_manager.get_account(username)
        if account and account.refresh_token:
            return {
                "access_token": account.access_token,
                "refresh_token": account.refresh_token,
                "expires_at": int(time.time()) + 7200,  # ساعتان افتراضياً
                "scope": self.scopes
            }
        return None
    
    def generate_oauth_state(self) -> str:
        """إنشاء حالة OAuth عشوائية"""
        state = secrets.token_urlsafe(32)
        return state
    
    def _create_oauth_handler(self):
        """إنشاء OAuth2UserHandler"""
        return tweepy.OAuth2UserHandler(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scopes,
            client_secret=self.client_secret
        )
    
    def get_client(self, username: str) -> Optional[tweepy.Client]:
        """إنشاء Twitter client مع auto-refresh للـ tokens"""
        tokens = self.load_tokens(username)
        if not tokens:
            return None
        
        # التحقق من انتهاء صلاحية الـ token وتحديثه إذا لزم الأمر
        if tokens["expires_at"] <= time.time() + 60 and tokens.get("refresh_token"):
            try:
                oauth = self._create_oauth_handler()
                new_tokens = oauth.refresh_token(
                    self.token_url,
                    refresh_token=tokens["refresh_token"]
                )
                self.save_tokens(username, new_tokens)
                tokens = self.load_tokens(username)
            except Exception as e:
                print(f"خطأ في تحديث الـ token: {str(e)}")
                return None
        
        return tweepy.Client(tokens["access_token"])
    
    def get_simple_oauth_url(self) -> str:
        """إنشاء رابط OAuth 2.0 للمصادقة
        
        Returns:
            str: رابط المصادقة
        """
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        try:
            oauth = self._create_oauth_handler()
            auth_url = oauth.get_authorization_url()
            
            # استخراج state من الرابط وحفظه
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(auth_url)
            query_params = parse_qs(parsed.query)
            if 'state' in query_params:
                state = query_params['state'][0]
                self.oauth_states[state] = {
                    "timestamp": int(time.time()),
                    "oauth_handler": oauth
                }
            
            return auth_url
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def get_public_oauth_url(self) -> str:
        """إنشاء رابط OAuth 2.0 عام للجميع
        
        Returns:
            str: رابط المصادقة العام
        """
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
            oauth = self._create_oauth_handler()
            redirect_url = oauth.get_authorization_url()
            
            # حفظ الحالة مع اسم المستخدم
            self.oauth_states[state] = {
                "username": username,
                "timestamp": int(time.time()),
                "oauth_handler": oauth
            }
            
            return redirect_url, state
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def handle_public_callback(self, callback_url: str) -> Dict:
        """معالجة callback من Twitter OAuth 2.0 بدون username محدد
        
        Args:
            callback_url (str): الرابط الكامل للـ callback
            
        Returns:
            Dict: نتيجة المصادقة
        """
        try:
            # استخراج state من callback_url
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(callback_url)
            query_params = parse_qs(parsed.query)
            
            oauth = None
            if 'state' in query_params:
                state = query_params['state'][0]
                if state in self.oauth_states:
                    oauth = self.oauth_states[state].get("oauth_handler")
            
            # استخدام OAuth handler المحفوظ أو إنشاء جديد
            if not oauth:
                oauth = self._create_oauth_handler()
            
            tokens = oauth.fetch_token(callback_url)
            
            # إنشاء client للحصول على معلومات المستخدم
            client = tweepy.Client(tokens["access_token"])
            user_info = client.get_me(user_auth=True).data
            
            # استخدام username من Twitter
            twitter_username = user_info.username
            if not twitter_username:
                return {
                    "success": False,
                    "error": "لم يتم العثور على username في معلومات المستخدم"
                }
            
            # حفظ الـ tokens
            self.save_tokens(twitter_username, tokens)
            
            # حفظ الحساب في قاعدة البيانات القديمة للتوافق
            success = db_manager.add_account(
                username=twitter_username,
                api_key="",  # OAuth 2.0 لا يستخدم API key
                api_secret="",
                access_token=tokens["access_token"],
                access_token_secret=tokens.get("refresh_token", ""),
                bearer_token=tokens["access_token"],
                display_name=user_info.name or twitter_username
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '@{twitter_username}' بنجاح",
                    "user_info": {
                        "username": user_info.username,
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
    
    def handle_callback(self, callback_url: str, state: str) -> Dict:
        """معالجة callback من Twitter OAuth 2.0 مع username محدد
        
        Args:
            callback_url (str): الرابط الكامل للـ callback
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
            # استخدام OAuth handler المحفوظ أو إنشاء جديد
            oauth = oauth_data.get("oauth_handler") or self._create_oauth_handler()
            tokens = oauth.fetch_token(callback_url)
            
            # إنشاء client للحصول على معلومات المستخدم
            client = tweepy.Client(tokens["access_token"])
            user_info = client.get_me(user_auth=True).data
            
            # حفظ الـ tokens
            self.save_tokens(username, tokens)
            
            # حفظ الحساب في قاعدة البيانات القديمة للتوافق
            success = db_manager.add_account(
                username=username,
                api_key="",  # OAuth 2.0 لا يستخدم API key
                api_secret="",
                access_token=tokens["access_token"],
                access_token_secret=tokens.get("refresh_token", ""),
                bearer_token=tokens["access_token"],
                display_name=user_info.name or username
            )
            
            if success:
                # حذف الحالة المؤقتة
                del self.oauth_states[state]
                
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '{username}' بنجاح",
                    "user_info": {
                        "username": user_info.username,
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
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """الحصول على معلومات المستخدم باستخدام OAuth 2.0
        
        Args:
            username (str): اسم المستخدم
            
        Returns:
            Optional[Dict]: معلومات المستخدم أو None
        """
        try:
            client = self.get_client(username)
            if not client:
                return None
            
            user_info = client.get_me(user_auth=True).data
            return {
                "id": user_info.id,
                "username": user_info.username,
                "name": user_info.name,
                "verified": getattr(user_info, 'verified', False)
            }
        except Exception as e:
            print(f"خطأ في الحصول على معلومات المستخدم: {str(e)}")
            return None
    
    def cleanup_expired_states(self):
        """تنظيف الحالات المنتهية الصلاحية"""
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
