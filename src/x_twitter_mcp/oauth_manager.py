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
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")  # Bearer Token للتطبيق (اختياري)
        self.redirect_uri = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # الصلاحيات المطلوبة (محدثة لتشمل like و bookmark)
        self.scopes = [
            "tweet.read", "tweet.write", 
            "users.read", 
            "offline.access",
            "like.read", "like.write",
            "bookmark.read", "bookmark.write"
        ]
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        
        # قاعدة بيانات للجلسات المؤقتة
        self.oauth_states = {}
        
        # التحقق من التكوين
        if not self.client_id:
            print("⚠️  تحذير: TWITTER_CLIENT_ID غير محدد")
            print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        
    def save_tokens(self, username: str, tokens: dict):
        """حفظ OAuth 2.0 tokens"""
        db_manager.add_account(
            username=username,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            display_name=username
        )
    
    def load_tokens(self, username: str) -> Optional[dict]:
        """تحميل الـ tokens من قاعدة البيانات الرئيسية"""
        account = db_manager.get_account(username)
        if not account:
            print(f"⚠️ لم يتم العثور على الحساب: {username}")
            return None
        
        if not account.access_token:
            print(f"⚠️ Access token فارغ للحساب: {username}")
            return None
            
        return {
            "access_token": account.access_token,
            "refresh_token": account.refresh_token or "",  # قد يكون فارغاً
            "expires_at": int(time.time()) + 7200,  # ساعتان افتراضياً
            "scope": self.scopes
        }
    
    def generate_oauth_state(self) -> str:
        """إنشاء حالة OAuth عشوائية"""
        state = secrets.token_urlsafe(32)
        return state
    
    def _create_oauth_handler(self):
        """إنشاء OAuth2UserHandler - يدعم PKCE والتطبيقات السرية"""
        print(f"🔍 DEBUG: إنشاء OAuth handler...")
        print(f"🔍 DEBUG: client_id: {'موجود' if self.client_id else 'فارغ'}")
        print(f"🔍 DEBUG: client_secret: {'موجود' if self.client_secret else 'فارغ'}")
        print(f"🔍 DEBUG: redirect_uri: {self.redirect_uri}")
        print(f"🔍 DEBUG: scopes: {self.scopes}")
        
        try:
            # للتطبيقات العامة (PKCE): client_secret فارغ أو غير محدد
            # للتطبيقات السرية (Confidential): client_secret محدد
            if self.client_secret:
                # تطبيق سري (Confidential App)
                print(f"🔍 DEBUG: إنشاء Confidential App handler")
                handler = tweepy.OAuth2UserHandler(
                    client_id=self.client_id,
                    redirect_uri=self.redirect_uri,
                    scope=self.scopes,
                    client_secret=self.client_secret
                )
            else:
                # تطبيق عام (Public App with PKCE)
                print(f"🔍 DEBUG: إنشاء Public App (PKCE) handler")
                handler = tweepy.OAuth2UserHandler(
                    client_id=self.client_id,
                    redirect_uri=self.redirect_uri,
                    scope=self.scopes
                    # لا client_secret للـ PKCE
                )
            
            print(f"🔍 DEBUG: تم إنشاء OAuth handler بنجاح")
            return handler
            
        except Exception as e:
            print(f"❌ DEBUG: خطأ في إنشاء OAuth handler: {str(e)}")
            raise
    
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
        
        access_token = tokens["access_token"]
        if not access_token or access_token.strip() == "":
            raise ValueError(f"Access token فارغ أو None للحساب {username}")
        
        # إنشاء Client مع OAuth 2.0 User Access Token
        # للحصول على OAuth 2.0 User Context، نحتاج المعاملات الصحيحة
        try:
            # OAuth 2.0 User Context: في Tweepy 4.x، نستخدم bearer_token للـ OAuth 2.0
            # access_token في Client.__init__() مخصص لـ OAuth 1.0a فقط
            client = tweepy.Client(
                bearer_token=access_token,  # OAuth 2.0 User Access Token كـ bearer_token
                wait_on_rate_limit=True
            )
            
            # حفظ معلومات إضافية للتحديث اليدوي (إذا احتجناها لاحقاً)
            client._refresh_token = tokens.get("refresh_token")
            client._client_id = self.client_id
            client._client_secret = self.client_secret
            
            return client
        except Exception as e:
            raise ValueError(f"فشل في إنشاء Twitter client للحساب {username}: {str(e)}")
    
    def get_simple_oauth_url(self) -> str:
        """إنشاء رابط OAuth 2.0 للمصادقة
        
        Returns:
            str: رابط المصادقة
        """
        print(f"🔍 DEBUG: بدء get_simple_oauth_url")
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        try:
            oauth = self._create_oauth_handler()
            auth_url = oauth.get_authorization_url()
            print(f"🔍 DEBUG: auth_url: {auth_url}")
            
            # استخراج state من الرابط وحفظه
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(auth_url)
            query_params = parse_qs(parsed.query)
            print(f"🔍 DEBUG: query_params من auth_url: {query_params}")
            
            if 'state' in query_params:
                state = query_params['state'][0]
                print(f"🔍 DEBUG: حفظ state في oauth_states: {state}")
                self.oauth_states[state] = {
                    "timestamp": int(time.time()),
                    "oauth_handler": oauth
                }
                print(f"🔍 DEBUG: oauth_states بعد الحفظ: {list(self.oauth_states.keys())}")
            else:
                print(f"❌ DEBUG: لا يوجد state في auth_url!")
            
            return auth_url
            
        except Exception as e:
            print(f"❌ DEBUG: خطأ في get_simple_oauth_url: {str(e)}")
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
        
        try:
            oauth = self._create_oauth_handler()
            redirect_url = oauth.get_authorization_url()
            
            # استخراج state الحقيقي من redirect_url
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(redirect_url)
            query_params = parse_qs(parsed.query)
            
            if 'state' in query_params:
                real_state = query_params['state'][0]
                # حفظ الحالة الحقيقية مع اسم المستخدم
                self.oauth_states[real_state] = {
                    "username": username,
                    "timestamp": int(time.time()),
                    "oauth_handler": oauth
                }
                return redirect_url, real_state
            else:
                raise ValueError("لم يتم العثور على state في رابط المصادقة")
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def handle_public_callback(self, callback_url: str) -> Dict:
        """معالجة callback من Twitter OAuth 2.0 بدون username محدد
        
        Args:
            callback_url (str): الرابط الكامل للـ callback
            
        Returns:
            Dict: نتيجة المصادقة
        """
        print(f"🔍 DEBUG: بدء معالجة callback: {callback_url}")
        try:
            # استخراج state من callback_url
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(callback_url)
            query_params = parse_qs(parsed.query)
            print(f"🔍 DEBUG: معاملات الـ callback: {query_params}")
            
            oauth = None
            if 'state' in query_params:
                state = query_params['state'][0]
                print(f"🔍 DEBUG: state موجود: {state}")
                if state in self.oauth_states:
                    oauth = self.oauth_states[state].get("oauth_handler")
                    print(f"🔍 DEBUG: تم العثور على OAuth handler محفوظ")
                else:
                    print(f"🔍 DEBUG: state غير موجود في oauth_states")
            else:
                print(f"🔍 DEBUG: لا يوجد state في المعاملات")
            
            # استخدام OAuth handler المحفوظ أو إنشاء جديد
            if not oauth:
                print(f"🔍 DEBUG: إنشاء OAuth handler جديد")
                oauth = self._create_oauth_handler()
            
            print(f"🔍 DEBUG: محاولة fetch_token...")
            try:
                print(f"🔍 DEBUG: استدعاء oauth.fetch_token()...")
                tokens = oauth.fetch_token(callback_url)
                print(f"🔍 DEBUG: تم الحصول على tokens: {list(tokens.keys()) if tokens else 'None'}")
                print(f"🔍 DEBUG: نوع tokens: {type(tokens)}")
            except Exception as fetch_error:
                print(f"❌ DEBUG: خطأ في fetch_token: {str(fetch_error)}")
                import traceback
                print(f"❌ DEBUG: تفاصيل خطأ fetch_token:\n{traceback.format_exc()}")
                return {"success": False, "error": f"خطأ في fetch_token: {str(fetch_error)}"}
            
            # إنشاء client للحصول على معلومات المستخدم
            access_token = tokens["access_token"]
            print(f"🔍 DEBUG: access_token نوع: {type(access_token)}, قيمة: {access_token[:20] if access_token else 'None'}...")
            if not access_token:
                return {"success": False, "error": "Access token فارغ من Twitter"}
            
            print(f"🔍 DEBUG: محاولة الحصول على معلومات المستخدم...")
            try:
                # استخدام OAuth 2.0 User Access Token
                print(f"🔍 DEBUG: استدعاء client.get_me() مع OAuth 2.0 User Token...")
                # إنشاء client مع OAuth 2.0 user access token
                user_client = tweepy.Client(bearer_token=access_token)
                me_response = user_client.get_me(user_auth=False)
                print(f"🔍 DEBUG: تم استدعاء client.get_me() بنجاح، نوع الاستجابة: {type(me_response)}")
                
                print(f"🔍 DEBUG: محاولة الوصول لـ .data...")
                user_info = me_response.data
                print(f"🔍 DEBUG: تم الحصول على .data بنجاح، نوع البيانات: {type(user_info)}")
                print(f"🔍 DEBUG: تم الحصول على معلومات المستخدم بنجاح")
            except Exception as user_error:
                print(f"❌ DEBUG: خطأ في الحصول على معلومات المستخدم: {str(user_error)}")
                import traceback
                print(f"❌ DEBUG: تفاصيل الخطأ الكاملة:\n{traceback.format_exc()}")
                return {"success": False, "error": f"خطأ في الحصول على معلومات المستخدم: {str(user_error)}"}
            
            # استخدام username من Twitter
            twitter_username = getattr(user_info, 'username', None)
            if not twitter_username:
                return {
                    "success": False,
                    "error": f"لم يتم العثور على username في معلومات المستخدم. البيانات المتاحة: {user_info}"
                }
            
            # حفظ الـ tokens
            self.save_tokens(twitter_username, tokens)
            
            # حفظ الحساب
            success = db_manager.add_account(
                username=twitter_username,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token", ""),
                display_name=getattr(user_info, 'name', twitter_username)
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '@{twitter_username}' بنجاح",
                    "user_info": {
                        "username": getattr(user_info, 'username', twitter_username),
                        "name": getattr(user_info, 'name', ''),
                        "id": getattr(user_info, 'id', '')
                    },
                    "username": twitter_username
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في حفظ الحساب"
                }
                
        except Exception as e:
            print(f"❌ DEBUG: خطأ في handle_public_callback: {str(e)}")
            print(f"❌ DEBUG: نوع الخطأ: {type(e).__name__}")
            import traceback
            print(f"❌ DEBUG: تفاصيل الخطأ:\n{traceback.format_exc()}")
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
        print(f"🔍 DEBUG: بدء handle_callback - state: {state}")
        print(f"🔍 DEBUG: callback_url: {callback_url}")
        print(f"🔍 DEBUG: oauth_states المتاحة: {list(self.oauth_states.keys())}")
        
        # التحقق من صحة الحالة
        if state not in self.oauth_states:
            print(f"❌ DEBUG: state غير موجود في oauth_states")
            return {
                "success": False,
                "error": "حالة OAuth غير صالحة"
            }
        
        oauth_data = self.oauth_states[state]
        username = oauth_data.get("username")  # استخدام get بدلاً من [] لمنع KeyError
        print(f"🔍 DEBUG: oauth_data: {oauth_data}")
        print(f"🔍 DEBUG: username من oauth_data: {username}")
        
        try:
            # استخدام OAuth handler المحفوظ أو إنشاء جديد
            oauth = oauth_data.get("oauth_handler") or self._create_oauth_handler()
            print(f"🔍 DEBUG: محاولة fetch_token في handle_callback...")
            tokens = oauth.fetch_token(callback_url)
            print(f"🔍 DEBUG: تم الحصول على tokens: {list(tokens.keys()) if tokens else 'None'}")
            
            # إنشاء client للحصول على معلومات المستخدم
            access_token = tokens["access_token"]
            print(f"🔍 DEBUG: access_token نوع: {type(access_token)}, قيمة: {access_token[:20] if access_token else 'None'}...")
            if not access_token:
                return {"success": False, "error": "Access token فارغ من Twitter"}
            
            print(f"🔍 DEBUG: محاولة إنشاء tweepy.Client في handle_callback...")
            try:
                client = tweepy.Client(
                    bearer_token=access_token,
                    consumer_key=None,
                    consumer_secret=None,
                    access_token=None,
                    access_token_secret=None
                )
                print(f"🔍 DEBUG: تم إنشاء Client بنجاح في handle_callback")
            except Exception as client_error:
                print(f"❌ DEBUG: خطأ في إنشاء Client في handle_callback: {str(client_error)}")
                return {"success": False, "error": f"خطأ في إنشاء Twitter Client: {str(client_error)}"}
            
            print(f"🔍 DEBUG: محاولة الحصول على معلومات المستخدم في handle_callback...")
            try:
                # استخدام OAuth 2.0 User Access Token
                user_client = tweepy.Client(bearer_token=tokens["access_token"])
                user_info = user_client.get_me(user_auth=False).data
                print(f"🔍 DEBUG: تم الحصول على معلومات المستخدم بنجاح في handle_callback")
            except Exception as user_error:
                print(f"❌ DEBUG: خطأ في الحصول على معلومات المستخدم في handle_callback: {str(user_error)}")
                return {"success": False, "error": f"خطأ في الحصول على معلومات المستخدم: {str(user_error)}"}
            
            # اشتقاق username من Twitter عند غيابه
            resolved_username = getattr(user_info, 'username', None)
            if not username:
                if not resolved_username:
                    return {
                        "success": False,
                        "error": "تعذر تحديد اسم المستخدم (username) من الحالة أو من Twitter"
                    }
                username = resolved_username
            
            # حفظ الـ tokens
            self.save_tokens(username, tokens)
            
            # حفظ الحساب
            success = db_manager.add_account(
                username=username,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token", ""),
                display_name=getattr(user_info, 'name', username)
            )
            
            if success:
                # حذف الحالة المؤقتة
                del self.oauth_states[state]
                
                return {
                    "success": True,
                    "message": f"تم إضافة الحساب '{username}' بنجاح",
                    "user_info": {
                        "username": getattr(user_info, 'username', username),
                        "name": getattr(user_info, 'name', ''),
                        "id": getattr(user_info, 'id', '')
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في حفظ الحساب"
                }
                
        except Exception as e:
            print(f"❌ DEBUG: خطأ في handle_callback: {str(e)}")
            print(f"❌ DEBUG: نوع الخطأ: {type(e).__name__}")
            import traceback
            print(f"❌ DEBUG: تفاصيل الخطأ:\n{traceback.format_exc()}")
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
            
            # استخدام OAuth 2.0 User Access Token (client مُنشأ بالفعل بـ bearer_token)
            user_info = client.get_me(user_auth=False).data
            return {
                "id": getattr(user_info, 'id', ''),
                "username": getattr(user_info, 'username', ''),
                "name": getattr(user_info, 'name', ''),
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
