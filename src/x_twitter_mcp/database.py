from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from typing import Optional, List, Dict, Any
import json

# إنشاء قاعدة البيانات
DATABASE_URL = "sqlite:///./twitter_accounts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# إنشاء جلسة قاعدة البيانات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# إنشاء قاعدة النماذج
Base = declarative_base()

class TwitterAccount(Base):
    """نموذج حساب Twitter - محدث لدعم OAuth 1.0a و OAuth 2.0"""
    __tablename__ = "twitter_accounts"
    
    username = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)  # Twitter User ID (OAuth 2.0)
    api_key = Column(String, nullable=False)
    api_secret = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    access_token_secret = Column(String, nullable=True)  # OAuth 1.0a فقط
    bearer_token = Column(String, nullable=True)  # App-only access
    refresh_token = Column(String, nullable=True)  # OAuth 2.0 فقط
    expires_at = Column(DateTime, nullable=True)  # OAuth 2.0 token expiry
    scopes = Column(Text, nullable=True)  # OAuth 2.0 scopes (JSON string)
    auth_type = Column(String, default="oauth1")  # "oauth1" أو "oauth2"
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        """تحويل النموذج إلى قاموس"""
        return {
            "username": self.username,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "auth_type": self.auth_type,
            "scopes": self.get_scopes_list(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
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
            "bearer_token": self.bearer_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id,
            "auth_type": self.auth_type
        }
    
    def get_scopes_list(self) -> List[str]:
        """الحصول على قائمة السكوبات"""
        if self.scopes:
            try:
                return json.loads(self.scopes)
            except:
                return []
        return []
    
    def set_scopes(self, scopes: List[str]):
        """تعيين السكوبات"""
        self.scopes = json.dumps(scopes) if scopes else None
    
    def is_token_expired(self) -> bool:
        """التحقق من انتهاء صلاحية التوكن"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def copy(self):
        """إنشاء نسخة نظيفة من الكائن"""
        return TwitterAccount(
            username=self.username,
            user_id=self.user_id,
            api_key=self.api_key,
            api_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            bearer_token=self.bearer_token,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
            scopes=self.scopes,
            auth_type=self.auth_type,
            display_name=self.display_name,
            created_at=self.created_at,
            last_used=self.last_used,
            is_active=self.is_active
        )

class DatabaseManager:
    """مدير قاعدة البيانات - محدث لدعم OAuth 2.0"""
    
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
                   access_token: str, access_token_secret: str = "", bearer_token: str = "",
                   display_name: Optional[str] = None, user_id: Optional[str] = None,
                   refresh_token: Optional[str] = None, expires_at: Optional[datetime] = None,
                   scopes: Optional[List[str]] = None, auth_type: str = "oauth1") -> bool:
        """إضافة حساب Twitter جديد - محدث لدعم OAuth 2.0"""
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
                    existing.user_id = user_id or existing.user_id
                    existing.refresh_token = refresh_token or existing.refresh_token
                    existing.expires_at = expires_at or existing.expires_at
                    existing.scopes = json.dumps(scopes) if scopes else existing.scopes
                    existing.auth_type = auth_type
                    existing.display_name = display_name or username
                    existing.last_used = datetime.utcnow()
                    existing.is_active = True
                else:
                    # إنشاء حساب جديد
                    new_account = TwitterAccount(
                        username=username,
                        user_id=user_id,
                        api_key=api_key,
                        api_secret=api_secret,
                        access_token=access_token,
                        access_token_secret=access_token_secret,
                        bearer_token=bearer_token,
                        refresh_token=refresh_token,
                        expires_at=expires_at,
                        scopes=json.dumps(scopes) if scopes else None,
                        auth_type=auth_type,
                        display_name=display_name or username
                    )
                    session.add(new_account)
                
                session.commit()
                return True
        except Exception as e:
            print(f"خطأ في إضافة الحساب: {e}")
            return False
    
    def update_tokens(self, username: str, access_token: str, 
                     refresh_token: Optional[str] = None, expires_at: Optional[datetime] = None) -> bool:
        """تحديث توكنات الحساب"""
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
    
    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على حساب بواسطة Twitter User ID"""
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
                    
                    return {
                        "username": account.username,
                        "user_id": account.user_id,
                        "access_token": account.access_token,
                        "refresh_token": account.refresh_token,
                        "expires_at": account.expires_at,
                        "scopes": account.get_scopes_list(),
                        "auth_type": account.auth_type,
                        "extra": {
                            "user_id": account.user_id,
                            "refresh_token": account.refresh_token,
                            "expires_at": account.expires_at.isoformat() if account.expires_at else None,
                            "scopes": account.get_scopes_list()
                        }
                    }
                
                return None
        except Exception as e:
            print(f"خطأ في الحصول على الحساب بواسطة user_id: {e}")
            return None
    
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
