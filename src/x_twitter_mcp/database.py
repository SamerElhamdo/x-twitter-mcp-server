from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime
import os
from typing import Optional, List
import json

# إنشاء قاعدة البيانات
DATABASE_URL = "sqlite:///./twitter_accounts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# إنشاء جلسة قاعدة البيانات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# إنشاء قاعدة النماذج
Base = declarative_base()

class OAuthState(Base):
    """نموذج حالة OAuth"""
    __tablename__ = "oauth_states"
    
    state = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    oauth2_handler_data = Column(String, nullable=True)  # JSON string for handler data
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # انتهاء الصلاحية بعد 10 دقائق
    
    def to_dict(self):
        """تحويل النموذج إلى قاموس"""
        return {
            "state": self.state,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }

class TwitterAccount(Base):
    """نموذج حساب Twitter"""
    __tablename__ = "twitter_accounts"
    
    username = Column(String, primary_key=True, index=True)
    api_key = Column(String, nullable=False)  # Twitter API Key (Consumer Key)
    api_secret = Column(String, nullable=False)  # Twitter API Secret (Consumer Secret)
    access_token = Column(String, nullable=False)  # OAuth 2.0 Access Token
    access_token_secret = Column(String, nullable=False)  # OAuth 1.0a Access Token Secret (للتوافق)
    bearer_token = Column(String, nullable=False)  # Bearer Token
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # حقول OAuth 2.0 الجديدة
    user_id = Column(String, nullable=True)  # Twitter User ID
    refresh_token = Column(String, nullable=True)  # OAuth 2.0 Refresh Token
    expires_at = Column(DateTime, nullable=True)  # تاريخ انتهاء Access Token
    scopes = Column(String, nullable=True)  # نطاقات OAuth 2.0 (JSON string)
    auth_type = Column(String, default="oauth2")  # نوع المصادقة: oauth1 أو oauth2
    
    def to_dict(self):
        """تحويل النموذج إلى قاموس"""
        return {
            "username": self.username,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active
        }
    
    def get_credentials(self):
        """الحصول على مفاتيح المصادقة (بدون عرضها)"""
        return {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "access_token": self.access_token,
            "access_token_secret": self.access_token_secret,
            "bearer_token": self.bearer_token
        }
    
    def copy(self):
        """إنشاء نسخة نظيفة من الكائن"""
        return TwitterAccount(
            username=self.username,
            api_key=self.api_key,
            api_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            bearer_token=self.bearer_token,
            display_name=self.display_name,
            created_at=self.created_at,
            last_used=self.last_used,
            is_active=self.is_active
        )

class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """الحصول على جلسة قاعدة البيانات"""
        return self.SessionLocal()
    
    def add_account(self, username: str, api_key: str, api_secret: str, 
                   access_token: str, access_token_secret: str, bearer_token: str,
                   display_name: Optional[str] = None, user_id: Optional[str] = None,
                   refresh_token: Optional[str] = None, expires_at: Optional[datetime] = None,
                   scopes: Optional[str] = None, auth_type: str = "oauth2") -> bool:
        """إضافة حساب Twitter جديد"""
        try:
            with self.get_session() as session:
                # التحقق من وجود الحساب
                existing = session.query(TwitterAccount).filter(
                    TwitterAccount.username == username
                ).first()
                
                if existing:
                    # تحديث الحساب الموجود
                    existing.api_key = api_key
                    existing.api_secret = api_secret
                    existing.access_token = access_token
                    existing.access_token_secret = access_token_secret
                    existing.bearer_token = bearer_token
                    existing.display_name = display_name or username
                    existing.user_id = user_id
                    existing.refresh_token = refresh_token
                    existing.expires_at = expires_at
                    existing.scopes = scopes
                    existing.auth_type = auth_type
                    existing.last_used = datetime.utcnow()
                    existing.is_active = True
                else:
                    # إنشاء حساب جديد
                    new_account = TwitterAccount(
                        username=username,
                        api_key=api_key,
                        api_secret=api_secret,
                        access_token=access_token,
                        access_token_secret=access_token_secret,
                        bearer_token=bearer_token,
                        display_name=display_name or username,
                        user_id=user_id,
                        refresh_token=refresh_token,
                        expires_at=expires_at,
                        scopes=scopes,
                        auth_type=auth_type
                    )
                    session.add(new_account)
                
                session.commit()
                return True
        except Exception as e:
            print(f"خطأ في إضافة الحساب: {e}")
            return False
    
    def get_account(self, username: str) -> Optional[TwitterAccount]:
        """الحصول على حساب Twitter"""
        try:
            with self.get_session() as session:
                account = session.query(TwitterAccount).filter(
                    TwitterAccount.username == username,
                    TwitterAccount.is_active == True
                ).first()
                
                if account:
                    # تحديث آخر استخدام
                    account.last_used = datetime.utcnow()
                    session.commit()
                    
                    # إرجاع نسخة نظيفة من الكائن
                    return account.copy()
                
                return None
        except Exception as e:
            print(f"خطأ في الحصول على الحساب: {e}")
            return None
    
    def get_all_accounts(self) -> List[TwitterAccount]:
        """الحصول على جميع الحسابات النشطة"""
        try:
            with self.get_session() as session:
                accounts = session.query(TwitterAccount).filter(
                    TwitterAccount.is_active == True
                ).all()
                
                # إرجاع نسخ نظيفة من الكائنات
                return [account.copy() for account in accounts]
        except Exception as e:
            print(f"خطأ في الحصول على الحسابات: {e}")
            return []
    
    def delete_account(self, username: str) -> bool:
        """حذف حساب Twitter"""
        try:
            with self.get_session() as session:
                account = session.query(TwitterAccount).filter(
                    TwitterAccount.username == username
                ).first()
                
                if account:
                    session.delete(account)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"خطأ في حذف الحساب: {e}")
            return False
    
    def deactivate_account(self, username: str) -> bool:
        """إلغاء تفعيل حساب Twitter"""
        try:
            with self.get_session() as session:
                account = session.query(TwitterAccount).filter(
                    TwitterAccount.username == username
                ).first()
                
                if account:
                    account.is_active = False
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"خطأ في إلغاء تفعيل الحساب: {e}")
            return False
    
    def get_by_user_id(self, user_id: str) -> Optional[TwitterAccount]:
        """الحصول على حساب Twitter بواسطة User ID"""
        try:
            with self.get_session() as session:
                account = session.query(TwitterAccount).filter(
                    TwitterAccount.user_id == user_id,
                    TwitterAccount.is_active == True
                ).first()
                
                if account:
                    # تحديث آخر استخدام
                    account.last_used = datetime.utcnow()
                    session.commit()
                    return account.copy()
                
                return None
        except Exception as e:
            print(f"خطأ في الحصول على الحساب بواسطة User ID: {e}")
            return None
    
    def save_oauth_state(self, state: str, username: str, oauth2_handler_data: str = None) -> bool:
        """حفظ حالة OAuth في قاعدة البيانات"""
        try:
            with self.get_session() as session:
                # حذف الحالات المنتهية الصلاحية
                from datetime import datetime, timedelta
                expired_time = datetime.utcnow() - timedelta(minutes=10)
                session.query(OAuthState).filter(
                    OAuthState.expires_at < expired_time
                ).delete()
                
                # حفظ الحالة الجديدة
                oauth_state = OAuthState(
                    state=state,
                    username=username,
                    oauth2_handler_data=oauth2_handler_data,
                    expires_at=datetime.utcnow() + timedelta(minutes=10)
                )
                session.add(oauth_state)
                session.commit()
                return True
        except Exception as e:
            print(f"خطأ في حفظ حالة OAuth: {e}")
            return False
    
    def get_oauth_state(self, state: str) -> Optional[OAuthState]:
        """الحصول على حالة OAuth من قاعدة البيانات"""
        try:
            with self.get_session() as session:
                oauth_state = session.query(OAuthState).filter(
                    OAuthState.state == state,
                    OAuthState.expires_at > datetime.utcnow()
                ).first()
                return oauth_state
        except Exception as e:
            print(f"خطأ في الحصول على حالة OAuth: {e}")
            return None
    
    def delete_oauth_state(self, state: str) -> bool:
        """حذف حالة OAuth من قاعدة البيانات"""
        try:
            with self.get_session() as session:
                session.query(OAuthState).filter(
                    OAuthState.state == state
                ).delete()
                session.commit()
                return True
        except Exception as e:
            print(f"خطأ في حذف حالة OAuth: {e}")
            return False
    
    def update_tokens(self, username: str, access_token: str, 
                     refresh_token: Optional[str] = None, expires_at: Optional[datetime] = None) -> bool:
        """تحديث توكنات OAuth 2.0"""
        try:
            with self.get_session() as session:
                account = session.query(TwitterAccount).filter(
                    TwitterAccount.username == username
                ).first()
                
                if account:
                    account.access_token = access_token
                    if refresh_token:
                        account.refresh_token = refresh_token
                    if expires_at:
                        account.expires_at = expires_at
                    account.last_used = datetime.utcnow()
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"خطأ في تحديث التوكنات: {e}")
            return False
    
    def test_credentials(self, username: str) -> bool:
        """اختبار صحة مفاتيح المصادقة"""
        try:
            account = self.get_account(username)
            if not account:
                return False
            
            # استيراد tweepy هنا لتجنب التبعيات الدائرية
            import tweepy
            
            # اختبار الاتصال
            client = tweepy.Client(
                consumer_key=account.api_key,
                consumer_secret=account.api_secret,
                access_token=account.access_token,
                access_token_secret=account.access_token_secret,
                bearer_token=account.bearer_token
            )
            
            # محاولة الحصول على معلومات المستخدم
            user = client.get_me()
            return user.data is not None
            
        except Exception as e:
            print(f"خطأ في اختبار المفاتيح: {e}")
            return False

# إنشاء مدير قاعدة البيانات العام
db_manager = DatabaseManager()

# إنشاء الجداول عند استيراد الملف
db_manager.create_tables()
