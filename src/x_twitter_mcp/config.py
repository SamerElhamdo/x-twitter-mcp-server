import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, ConfigDict
except ImportError:
    # Fallback for older versions
    from pydantic import BaseSettings, Field, ConfigDict

class Settings(BaseSettings):
    """إعدادات النظام - محدث لـ OAuth 2.0"""
    
    # إعدادات الخادم
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # إعدادات Twitter OAuth 2.0
    twitter_client_id: str = Field(default="", env="TWITTER_CLIENT_ID")
    twitter_client_secret: str = Field(default="", env="TWITTER_CLIENT_SECRET")
    twitter_redirect_uri: str = Field(default="", env="TWITTER_REDIRECT_URI")
    
    # إعدادات قاعدة البيانات
    database_url: str = Field(default="sqlite:///./twitter_accounts.db", env="DATABASE_URL")
    
    # إعدادات الأمان
    secret_key: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
    
    # إعدادات OAuth 2.0
    oauth_state_expire_seconds: int = Field(default=3600, env="OAUTH_STATE_EXPIRE_SECONDS")  # ساعة واحدة
    
    # إعدادات البيئة
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # إعدادات إضافية (للتوافق مع الكود القديم)
    twitter_api_key: str = Field(default="", env="TWITTER_API_KEY")
    twitter_api_secret: str = Field(default="", env="TWITTER_API_SECRET")
    api_secret_key: str = Field(default="", env="API_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # تكوين Pydantic
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # تجاهل المتغيرات الإضافية
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # تعيين redirect URI افتراضي إذا لم يتم تحديده
        if not self.twitter_redirect_uri:
            self.twitter_redirect_uri = f"http://{self.host}:{self.port}/auth/callback"
    
    def validate_oauth_config(self) -> bool:
        """التحقق من صحة إعدادات OAuth 2.0"""
        return bool(self.twitter_client_id)
    
    def get_oauth_config(self) -> dict:
        """الحصول على إعدادات OAuth 2.0"""
        return {
            "client_id": self.twitter_client_id,
            "client_secret": self.twitter_client_secret,
            "redirect_uri": self.twitter_redirect_uri,
            "host": self.host,
            "port": self.port
        }
    
    def is_production(self) -> bool:
        """التحقق من كون البيئة إنتاجية"""
        try:
            return self.environment.lower() == "production"
        except:
            return False
    
    def get_log_level(self) -> str:
        """الحصول على مستوى التسجيل - مبسط وآمن"""
        return "DEBUG"  # دائماً DEBUG للتطوير

# إنشاء كائن الإعدادات العام
_settings = None

def get_settings() -> Settings:
    """الحصول على إعدادات النظام (Singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# للتوافق مع الكود القديم
config = get_settings()
