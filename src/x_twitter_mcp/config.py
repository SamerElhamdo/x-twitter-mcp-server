import os
from typing import Optional

class Config:
    """إعدادات النظام"""
    
    # إعدادات الخادم
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    
    # إعدادات Twitter OAuth
    TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID", "")
    TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET", "")
    TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI", f"http://{HOST}:{PORT}/auth/callback")
    
    # إعدادات قاعدة البيانات
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./twitter_accounts.db")
    
    # إعدادات الأمان
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # إعدادات OAuth
    OAUTH_STATE_EXPIRE_SECONDS = int(os.getenv("OAUTH_STATE_EXPIRE_SECONDS", "3600"))  # ساعة واحدة
    
    @classmethod
    def validate_oauth_config(cls) -> bool:
        """التحقق من صحة إعدادات OAuth"""
        return bool(cls.TWITTER_CLIENT_ID and cls.TWITTER_CLIENT_SECRET)
    
    @classmethod
    def get_oauth_config(cls) -> dict:
        """الحصول على إعدادات OAuth"""
        return {
            "client_id": cls.TWITTER_CLIENT_ID,
            "client_secret": cls.TWITTER_CLIENT_SECRET,
            "redirect_uri": cls.TWITTER_REDIRECT_URI,
            "host": cls.HOST,
            "port": cls.PORT
        }

# إنشاء كائن التكوين العام
config = Config()
