from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone
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

def get_utc_now():
    """الحصول على الوقت الحالي في UTC"""
    return datetime.now(timezone.utc)

class TwitterAccount(Base):
    """نموذج حساب Twitter"""
    __tablename__ = "twitter_accounts"
    
    username = Column(String, primary_key=True, index=True)
    api_key = Column(String, nullable=False)
    api_secret = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    access_token_secret = Column(String, nullable=False)
    bearer_token = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    last_used = Column(DateTime, default=get_utc_now)
    is_active = Column(Boolean, default=True)
    
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
                   display_name: Optional[str] = None) -> bool:
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
                    existing.last_used = get_utc_now()
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
                        display_name=display_name or username
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
                    account.last_used = get_utc_now()
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
