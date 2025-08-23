from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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

class TwitterAccount(Base):
    """نموذج حساب Twitter - OAuth 2.0 فقط"""
    __tablename__ = "twitter_accounts"
    
    username = Column(String, primary_key=True, index=True)
    # OAuth 2.0 tokens فقط
    access_token = Column(String, nullable=False)  # Bearer token
    refresh_token = Column(String, nullable=True)
    # معلومات إضافية
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # حقول OAuth 1.0a - للتوافق مع قاعدة البيانات الموجودة (ستكون فارغة)
    api_key = Column(String, nullable=True, default="")
    api_secret = Column(String, nullable=True, default="")
    access_token_secret = Column(String, nullable=True, default="")
    bearer_token = Column(String, nullable=True)  # نسخة من access_token
    
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
        """الحصول على OAuth 2.0 tokens"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token
        }
    
    def copy(self):
        """إنشاء نسخة نظيفة من الكائن"""
        return TwitterAccount(
            username=self.username,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            display_name=self.display_name,
            created_at=self.created_at,
            last_used=self.last_used,
            is_active=self.is_active,
            # حقول التوافق
            api_key="",
            api_secret="",
            access_token_secret="",
            bearer_token=self.access_token
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
    
    def add_account(self, username: str, access_token: str, refresh_token: Optional[str] = None,
                   display_name: Optional[str] = None, 
                   # حقول OAuth 1.0a للتوافق (ستُتجاهل)
                   api_key: str = "", api_secret: str = "", 
                   access_token_secret: str = "", bearer_token: str = "") -> bool:
        """إضافة حساب Twitter جديد"""
        try:
            with self.get_session() as session:
                # التحقق من وجود الحساب
                existing = session.query(TwitterAccount).filter(
                    TwitterAccount.username == username
                ).first()
                
                if existing:
                    # تحديث الحساب الموجود
                    existing.access_token = access_token or ""
                    existing.refresh_token = refresh_token or ""
                    existing.display_name = display_name or username
                    existing.last_used = datetime.utcnow()
                    existing.is_active = True
                    # حقول التوافق - ضمان عدم وجود None
                    existing.api_key = ""
                    existing.api_secret = ""
                    existing.access_token_secret = ""
                    existing.bearer_token = access_token or ""
                else:
                    # إنشاء حساب جديد
                    new_account = TwitterAccount(
                        username=username,
                        access_token=access_token or "",
                        refresh_token=refresh_token or "",
                        display_name=display_name or username,
                        # حقول التوافق - ضمان عدم وجود None
                        api_key="",
                        api_secret="",
                        access_token_secret="",
                        bearer_token=access_token or ""
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
                    
                    # التأكد من عدم وجود قيم None في الحقول المهمة
                    if account.access_token is None:
                        account.access_token = ""
                    if account.refresh_token is None:
                        account.refresh_token = ""
                    if account.api_key is None:
                        account.api_key = ""
                    if account.api_secret is None:
                        account.api_secret = ""
                    if account.access_token_secret is None:
                        account.access_token_secret = ""
                    if account.bearer_token is None:
                        account.bearer_token = account.access_token or ""
                    
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
            # استخدام oauth_manager للاختبار مع OAuth 2.0
            from .oauth_manager import oauth_manager
            user_info = oauth_manager.get_user_info(username)
            return user_info is not None
            
        except Exception as e:
            print(f"خطأ في اختبار المفاتيح: {e}")
            return False

# إنشاء مدير قاعدة البيانات العام
db_manager = DatabaseManager()

# إنشاء الجداول عند استيراد الملف
db_manager.create_tables()
