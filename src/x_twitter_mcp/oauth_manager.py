import os
import time
import secrets
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import tweepy
from .database import db_manager

# تحميل متغيرات البيئة من ملف .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class TwitterOAuth2Manager:
    """مدير مصادقة Twitter OAuth 2.0 (Authorization Code + PKCE) بنمط User Context"""
    
    def __init__(self):
        self.client_id = os.getenv("TWITTER_CLIENT_ID", "")
        self.client_secret = os.getenv("TWITTER_CLIENT_SECRET", "")  # اختياري مع PKCE
        self.redirect_uri = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/auth/callback")
        self.scopes = [
            "tweet.read", "tweet.write", "users.read",
            "like.read", "like.write", "offline.access"
        ]
        
        # التحقق من التكوين
        if not self.client_id:
            print("⚠️  تحذير: TWITTER_CLIENT_ID غير محدد")
            print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        
        # قاعدة بيانات للجلسات المؤقتة (في الإنتاج، استخدم Redis أو قاعدة بيانات)
        self._states: Dict[str, Dict] = {}
        
    def generate_state(self) -> str:
        """إنشاء حالة OAuth عشوائية"""
        return secrets.token_urlsafe(24)
    
    def get_authorization_url(self, username: Optional[str] = None) -> Tuple[str, str]:
        """إنشاء رابط التفويض OAuth 2.0 + state
        
        Args:
            username (str, optional): اسم المستخدم المطلوب (للتتبع)
            
        Returns:
            Tuple[str, str]: (رابط التفويض، حالة OAuth)
        """
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        state = self.generate_state()
        
        try:
            # استخدام Tweepy OAuth 2.0 User Handler
            oauth2_user_handler = tweepy.OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes,
                client_secret=self.client_secret or None,  # إن وجد
            )
            
            # إنشاء رابط التفويض مع PKCE
            auth_url = oauth2_user_handler.get_authorization_url(
                state=state, 
                code_challenge_method="S256"
            )
            
            # حفظ الـ handler مؤقتًا (يحتوي code_verifier داخليًا)
            self._states[state] = {
                "username": username,
                "timestamp": int(time.time()),
                "handler": oauth2_user_handler,
            }
            
            return auth_url, state
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط التفويض: {str(e)}")
    
    def get_public_oauth_url(self) -> str:
        """إنشاء رابط OAuth 2.0 عام للجميع"""
        auth_url, _ = self.get_authorization_url()
        return auth_url
    
    def handle_callback(self, state: str, code: str) -> Dict:
        """معالجة callback من Twitter OAuth 2.0
        
        Args:
            state (str): حالة OAuth
            code (str): رمز التفويض من Twitter
            
        Returns:
            Dict: نتيجة المصادقة
        """
        # التحقق من صحة الحالة
        if state not in self._states:
            return {
                "success": False,
                "error": "حالة OAuth غير صالحة أو منتهية الصلاحية"
            }
        
        oauth_data = self._states[state]
        username = oauth_data.get("username")
        oauth2_user_handler = oauth_data["handler"]
        
        try:
            # تبادل الـ code إلى توكنات
            token_data = oauth2_user_handler.fetch_token(code=code)
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 0)
            expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
            
            if not access_token:
                return {
                    "success": False,
                    "error": "فشل في الحصول على access token"
                }
            
            # إنشاء عميل v2 بسياق المستخدم
            client = tweepy.Client(
                access_token=access_token,
                consumer_key=os.getenv("TWITTER_API_KEY", None),          # اختياري
                consumer_secret=os.getenv("TWITTER_API_SECRET", None),    # اختياري
            )
            
            # الحصول على معلومات المستخدم الموثَّق
            me = client.get_me(user_auth=True)
            if not me.data:
                return {
                    "success": False,
                    "error": "فشل في الحصول على معلومات المستخدم"
                }
            
            user = me.data
            user_id = str(user.id)
            twitter_username = user.username
            display_name = user.name or twitter_username
            
            # استخدام username من Twitter إذا لم يتم تحديده
            final_username = username or twitter_username
            
            # حفظ الحساب في قاعدة البيانات
            success = db_manager.add_account(
                username=final_username,
                user_id=user_id,
                api_key=os.getenv("TWITTER_API_KEY", ""),
                api_secret=os.getenv("TWITTER_API_SECRET", ""),
                access_token=access_token,
                access_token_secret="",  # غير مستخدم في OAuth 2.0
                bearer_token="",         # غير مطلوب هنا
                refresh_token=refresh_token,
                expires_at=expires_at,
                scopes=self.scopes,
                auth_type="oauth2",
                display_name=display_name
            )
            
            if success:
                # حذف الحالة المؤقتة
                del self._states[state]
                
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '@{final_username}' بنجاح",
                    "user_info": {
                        "username": twitter_username,
                        "name": display_name,
                        "id": user_id
                    },
                    "username": final_username
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
    
    def handle_public_callback(self, code: str) -> Dict:
        """معالجة callback عام من Twitter OAuth 2.0 بدون username محدد"""
        # إنشاء state مؤقت للاستخدام
        temp_state = self.generate_state()
        self._states[temp_state] = {
            "username": None,
            "timestamp": int(time.time()),
            "handler": None  # سيتم إنشاؤه لاحقاً
        }
        
        return self.handle_callback(temp_state, code)
    
    def refresh_access_token(self, username: str) -> Optional[str]:
        """تجديد access token للمستخدم عند انتهاء صلاحيته
        
        Args:
            username (str): اسم المستخدم
            
        Returns:
            Optional[str]: access token الجديد أو None في حالة الفشل
        """
        try:
            # الحصول على معلومات الحساب
            account = db_manager.get_account(username)
            if not account or not account.refresh_token:
                return None
            
            # إنشاء OAuth2 handler جديد
            oauth2_user_handler = tweepy.OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes,
                client_secret=self.client_secret or None,
            )
            
            # تجديد التوكن
            token_data = oauth2_user_handler.refresh_token(
                token_url="https://api.twitter.com/2/oauth2/token",
                refresh_token=account.refresh_token
            )
            
            access_token = token_data["access_token"]
            new_refresh_token = token_data.get("refresh_token", account.refresh_token)
            expires_in = token_data.get("expires_in", 0)
            expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
            
            # تحديث التوكنات في قاعدة البيانات
            db_manager.update_tokens(
                username=username,
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at
            )
            
            return access_token
            
        except Exception as e:
            print(f"خطأ في تجديد التوكن: {e}")
            return None
    
    def get_valid_access_token(self, username: str) -> Optional[str]:
        """الحصول على access token صالح (مع تجديده تلقائياً إذا انتهت صلاحيته)"""
        account = db_manager.get_account(username)
        if not account:
            return None
        
        # التحقق من انتهاء الصلاحية
        if account.is_token_expired() and account.refresh_token:
            new_token = self.refresh_access_token(username)
            if new_token:
                return new_token
        
        return account.access_token
    
    def create_client_for_user(self, username: str) -> Optional[tweepy.Client]:
        """إنشاء Tweepy Client لمستخدم محدد مع تجديد التوكن تلقائياً"""
        access_token = self.get_valid_access_token(username)
        if not access_token:
            return None
        
        return tweepy.Client(
            access_token=access_token,
            consumer_key=os.getenv("TWITTER_API_KEY", None),
            consumer_secret=os.getenv("TWITTER_API_SECRET", None),
        )
    
    def cleanup_expired_states(self):
        """تنظيف الحالات المنتهية الصلاحية"""
        current_time = int(time.time())
        expired_states = []
        
        for state, data in self._states.items():
            if current_time - data["timestamp"] > 3600:  # ساعة واحدة
                expired_states.append(state)
        
        for state in expired_states:
            del self._states[state]

# إنشاء مدير OAuth 2.0 عام
oauth_manager = TwitterOAuth2Manager()
