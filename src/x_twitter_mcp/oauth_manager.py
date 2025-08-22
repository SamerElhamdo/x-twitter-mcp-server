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
        
        # تحديد redirect URI بناءً على البيئة
        self.redirect_uri = self._get_redirect_uri()
        
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
        # تخزين حالات OAuth في قاعدة البيانات
        
        # التحقق من التكوين
        if not self.client_id:
            print("⚠️  تحذير: TWITTER_CLIENT_ID غير محدد")
            print("💡 تأكد من إعداد ملف .env أو متغيرات البيئة")
        
        print(f"🌐 [OAuth Manager] Redirect URI: {self.redirect_uri}")
    
    def _get_redirect_uri(self) -> str:
        """تحديد redirect URI بناءً على البيئة"""
        # أولاً، تحقق من متغير البيئة
        env_redirect = os.getenv("TWITTER_REDIRECT_URI")
        if env_redirect:
            return env_redirect
        
        # إذا لم يكن محدد، استخدم الدومين أو localhost
        host = os.getenv("HOST", "127.0.0.1")
        port = os.getenv("PORT", "8000")
        
        # إذا كان HOST = 0.0.0.0، استخدم localhost
        if host == "0.0.0.0":
            host = "127.0.0.1"
        
        # تحقق من وجود دومين
        domain = os.getenv("DOMAIN")
        if domain:
            return f"https://{domain}/auth/callback"
        
        # استخدم localhost
        return f"http://{host}:{port}/auth/callback"
        
    def generate_oauth_state(self) -> str:
        """إنشاء حالة OAuth عشوائية"""
        state = secrets.token_urlsafe(32)
        return state
    
    def get_simple_oauth_url(self) -> Tuple[str, str]:
        """إنشاء رابط OAuth 2.0 (Authorization Code + PKCE)
        
        Returns:
            Tuple[str, str]: (رابط المصادقة، حالة OAuth)
        """
        print(f"🚀 [get_simple_oauth_url] بدء إنشاء رابط المصادقة")
        print(f"🚀 [get_simple_oauth_url] Client ID: {self.client_id}")
        print(f"🚀 [get_simple_oauth_url] Redirect URI: {self.redirect_uri}")
        
        if not self.client_id:
            raise ValueError("TWITTER_CLIENT_ID غير محدد. يرجى إعداده في ملف .env")
        
        try:
            # استخدام Tweepy OAuth 2.0 مع PKCE
            # Twitter API v2 يتطلب PKCE
            # client_secret اختياري - لا نحتاجه إلا إذا كان confidential client
            oauth2_handler = OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes
            )
            
            # إنشاء رابط المصادقة مع PKCE
            # OAuth2UserHandler يدعم PKCE تلقائياً
            # Twitter API v2 يتطلب PKCE
            auth_url = oauth2_handler.get_authorization_url()
            
            # استخدم state الذي ولّده tweepy
            # المشكلة: oauth2_handler.state يعيد دالة، نحتاج القيمة الفعلية
            state = None
            code_verifier = None
            
            # محاولة استخراج state و code_verifier من oauth2_handler
            for attr in ["oauth2_session", "_client", "code_verifier"]:
                try:
                    obj = getattr(oauth2_handler, attr)
                    if obj:
                        # محاولة الحصول على state
                        if state is None:
                            state = getattr(obj, "state", None)
                            if callable(state):
                                state = state()  # استدعاء الدالة
                        
                        # محاولة الحصول على code_verifier
                        if code_verifier is None:
                            code_verifier = getattr(obj, "code_verifier", None)
                            if isinstance(code_verifier, str) and len(code_verifier) >= 43:
                                break
                except Exception as e:
                    print(f"⚠️  [get_simple_oauth_url] فشل في استخراج {attr}: {e}")
                    continue
            
            # إذا لم نجد state، استخدم generate_oauth_state
            if not state or callable(state):
                print(f"⚠️  [get_simple_oauth_url] فشل في الحصول على state من Tweepy، استخدام generate_oauth_state")
                state = self.generate_oauth_state()
            
            if not state:
                raise ValueError("فشل في إنشاء state")
            
            # معلومات تشخيصية
            print(f"🔗 رابط المصادقة: {auth_url}")
            print(f"🆔 Client ID: {self.client_id}")
            print(f"🔄 Redirect URI: {self.redirect_uri}")
            print(f"📋 Scopes: {', '.join(self.scopes)}")
            print(f"🔑 State (من Tweepy): {state}")
            print(f"🔐 Code Verifier: {code_verifier[:20] + '...' if code_verifier else 'غير موجود'}")
            
            # حفظ الحالة في قاعدة البيانات
            from .database import db_manager
            
            # تحويل oauth2_handler إلى بيانات قابلة للتخزين
            # تأكد من أن جميع البيانات قابلة للتسلسل JSON
            handler_data = {
                "client_id": str(oauth2_handler.client_id) if oauth2_handler.client_id else "",
                "redirect_uri": str(oauth2_handler.redirect_uri) if oauth2_handler.redirect_uri else "",
                "scope": list(oauth2_handler.scope) if hasattr(oauth2_handler, 'scope') and callable(getattr(oauth2_handler, 'scope', None)) else (oauth2_handler.scope if oauth2_handler.scope else []),
                "state": str(state) if state else "",
                "code_verifier": str(code_verifier) if code_verifier else ""
            }
            
            # معلومات تشخيصية إضافية
            print(f"🔍 [get_simple_oauth_url] نوع scope: {type(oauth2_handler.scope)}")
            print(f"🔍 [get_simple_oauth_url] قيمة scope: {oauth2_handler.scope}")
            print(f"🔍 [get_simple_oauth_url] handler_data: {handler_data}")
            
            # حفظ في قاعدة البيانات
            print(f"💾 [get_simple_oauth_url] محاولة حفظ state: {state}")
            save_result = db_manager.save_oauth_state(state, "default_user", json.dumps(handler_data))
            print(f"💾 [get_simple_oauth_url] نتيجة الحفظ: {save_result}")
            
            if save_result:
                print(f"✅ [get_simple_oauth_url] تم حفظ state في قاعدة البيانات: {state}")
                print(f"👤 [get_simple_oauth_url] للمستخدم: default_user")
                print(f"🔐 [get_simple_oauth_url] Code Verifier محفوظ: {code_verifier is not None}")
            else:
                print(f"❌ [get_simple_oauth_url] فشل في حفظ state في قاعدة البيانات")
            
            return auth_url, state
            
        except Exception as e:
            raise ValueError(f"خطأ في إنشاء رابط المصادقة: {str(e)}")
    
    def get_public_oauth_url(self) -> Tuple[str, str]:
        """إنشاء رابط OAuth 2.0 عام للجميع
        
        Returns:
            Tuple[str, str]: (رابط المصادقة، حالة OAuth)
        """
        print(f"🚀 [get_public_oauth_url] بدء إنشاء رابط عام...")
        # استخدام الرابط الصحيح لحل مشكلة redirect_after_login
        auth_url, state = self.get_simple_oauth_url()
        print(f"🚀 [get_public_oauth_url] تم إنشاء رابط: {auth_url[:50]}...")
        print(f"🚀 [get_public_oauth_url] State: {state}")
        return auth_url, state
    
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
            # استخدام Tweepy OAuth 2.0 مع PKCE
            # client_secret اختياري - لا نحتاجه إلا إذا كان confidential client
            oauth2_handler = OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes
            )
            
            # إنشاء رابط المصادقة مع PKCE
            # OAuth2UserHandler يدعم PKCE تلقائياً
            # Twitter API v2 يتطلب PKCE
            redirect_url = oauth2_handler.get_authorization_url()
            
            # استخدم state الذي ولّده tweepy
            # المشكلة: oauth2_handler.state يعيد دالة، نحتاج القيمة الفعلية
            state = None
            code_verifier = None
            
            # محاولة استخراج state و code_verifier من oauth2_handler
            for attr in ["oauth2_session", "_client", "code_verifier"]:
                try:
                    obj = getattr(oauth2_handler, attr)
                    if obj:
                        # محاولة الحصول على state
                        if state is None:
                            state = getattr(obj, "state", None)
                            if callable(state):
                                state = state()  # استدعاء الدالة
                        
                        # محاولة الحصول على code_verifier
                        if code_verifier is None:
                            code_verifier = getattr(obj, "code_verifier", None)
                            if isinstance(code_verifier, str) and len(code_verifier) >= 43:
                                break
                except Exception as e:
                    print(f"⚠️  [get_authorization_url] فشل في استخراج {attr}: {e}")
                    continue
            
            # إذا لم نجد state، استخدم generate_oauth_state
            if not state or callable(state):
                print(f"⚠️  [get_authorization_url] فشل في الحصول على state من Tweepy، استخدام generate_oauth_state")
                state = self.generate_oauth_state()
            
            if not state:
                raise ValueError("فشل في إنشاء state")
            
            # معلومات تشخيصية
            print(f"🔗 رابط المصادقة للمستخدم {username}: {redirect_url}")
            print(f"🔑 State (من Tweepy): {state}")
            print(f"🔐 Code Verifier: {code_verifier[:20] + '...' if code_verifier else 'غير موجود'}")
            
            # حفظ الحالة مع اسم المستخدم في قاعدة البيانات
            from .database import db_manager
            
            # تحويل oauth2_handler إلى بيانات قابلة للتخزين
            # تأكد من أن جميع البيانات قابلة للتسلسل JSON
            handler_data = {
                "client_id": str(oauth2_handler.client_id) if oauth2_handler.client_id else "",
                "redirect_uri": str(oauth2_handler.redirect_uri) if oauth2_handler.redirect_uri else "",
                "scope": list(oauth2_handler.scope) if hasattr(oauth2_handler, 'scope') and callable(getattr(oauth2_handler, 'scope', None)) else (oauth2_handler.scope if oauth2_handler.scope else []),
                "state": str(state) if state else "",
                "code_verifier": str(code_verifier) if code_verifier else ""
            }
            
            # معلومات تشخيصية إضافية
            print(f"🔍 [get_authorization_url] نوع scope: {type(oauth2_handler.scope)}")
            print(f"🔍 [get_authorization_url] قيمة scope: {oauth2_handler.scope}")
            print(f"🔍 [get_authorization_url] handler_data: {handler_data}")
            
            # حفظ في قاعدة البيانات
            if db_manager.save_oauth_state(state, username, json.dumps(handler_data)):
                print(f"💾 [get_authorization_url] تم حفظ state في قاعدة البيانات: {state}")
                print(f"👤 [get_authorization_url] للمستخدم: {username}")
                print(f"🔐 [get_authorization_url] Code Verifier محفوظ: {code_verifier is not None}")
            else:
                print(f"❌ [get_authorization_url] فشل في حفظ state في قاعدة البيانات")
            
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
                # استخدام OAuth 2.0 - لا نحتاج consumer_key/secret
                client = tweepy.Client(
                    access_token=account.access_token
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
        # التحقق من صحة الحالة من قاعدة البيانات
        print(f"🔍 [handle_callback] بدء معالجة callback")
        print(f"🔍 [handle_callback] البحث عن state: {state}")
        print(f"🔍 [handle_callback] رمز التفويض: {code}")
        
        # الحصول على الحالة من قاعدة البيانات
        from .database import db_manager
        
        print(f"🔍 [handle_callback] البحث عن state في قاعدة البيانات: {state}")
        print(f"↩️ [callback] redirect_uri_used={self.redirect_uri}")
        
        oauth_state = db_manager.get_oauth_state(state)
        
        if not oauth_state:
            print(f"❌ [handle_callback] State غير موجود أو منتهي الصلاحية: {state}")
            
            # محاولة معرفة ما حدث - البحث عن جميع الحالات
            print(f"🔍 [handle_callback] البحث عن جميع الحالات في قاعدة البيانات...")
            all_states = db_manager.get_all_oauth_states()
            print(f"📊 [handle_callback] إجمالي الحالات في قاعدة البيانات: {len(all_states)}")
            
            for state_obj in all_states:
                print(f"📋 [handle_callback] حالة موجودة: '{state_obj.state}' - مستخدم: {state_obj.username} - تاريخ: {state_obj.created_at}")
            
            return {
                "success": False,
                "error": f"حالة OAuth غير صالحة أو منتهية الصلاحية. State: {state}"
            }
        
        print(f"✅ [handle_callback] تم العثور على state: {state}")
        print(f"👤 [handle_callback] المستخدم: {oauth_state.username}")
        print(f"⏰ [handle_callback] تاريخ انتهاء الصلاحية: {oauth_state.expires_at}")
        
        # استخراج البيانات المحفوظة
        try:
            handler_data = json.loads(oauth_state.oauth2_handler_data) if oauth_state.oauth2_handler_data else {}
            code_verifier = handler_data.get("code_verifier")
            
            if not code_verifier:
                print(f"❌ [handle_callback] code_verifier غير محفوظ للـ state: {state}")
                return {
                    "success": False,
                    "error": "code_verifier غير محفوظ للـ state"
                }
            
            print(f"✅ [handle_callback] تم العثور على code_verifier: {code_verifier[:20]}...")
            
        except Exception as e:
            print(f"❌ [handle_callback] فشل في استخراج البيانات المحفوظة: {e}")
            return {
                "success": False,
                "error": f"فشل في استخراج البيانات المحفوظة: {str(e)}"
            }
        
        username = oauth_state.username
        
        try:
            # استخدام POST يدوي بدلاً من fetch_token
            # هذا يضمن استخدام code_verifier الصحيح
            import requests
            
            print(f"🔄 [handle_callback] بدء تبادل الكود مع Twitter...")
            print(f"🔗 [handle_callback] Endpoint: https://api.twitter.com/2/oauth2/token")
            print(f"🔑 [handle_callback] Code: {code}")
            print(f"🔐 [handle_callback] Code Verifier: {code_verifier[:20]}...")
            print(f"🔄 [handle_callback] Redirect URI: {self.redirect_uri}")
            
            token_resp = requests.post(
                "https://api.twitter.com/2/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "code_verifier": code_verifier
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_resp.status_code != 200:
                print(f"❌ [handle_callback] فشل في تبادل الكود: {token_resp.status_code}")
                print(f"❌ [handle_callback] Response: {token_resp.text}")
                return {
                    "success": False,
                    "error": f"فشل في تبادل الكود: {token_resp.status_code} - {token_resp.text}"
                }
            
            print(f"✅ [handle_callback] تم تبادل الكود بنجاح!")
            token_data = token_resp.json()
            
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
                db_manager.delete_oauth_state(state)
                
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
        # يتم تنظيف الحالات المنتهية الصلاحية تلقائياً في قاعدة البيانات
        # عند حفظ حالة جديدة
        print("🧹 تم تنظيف الحالات المنتهية الصلاحية من قاعدة البيانات")

# إنشاء نسخة واحدة من مدير المصادقة
oauth_manager = TwitterOAuthManager()
