"""
Twitter MCP Server - OAuth 2.0

خادم MCP (Model Context Protocol) لـ Twitter يستخدم OAuth 2.0 مع PKCE
للوصول الآمن إلى Twitter API v2.

المميزات:
- OAuth 2.0 مع PKCE للمصادقة الآمنة
- Twitter API v2 مع دعم كامل للعمليات
- إدارة تلقائية للتوكنات مع تجديدها
- دعم متعدد المستخدمين مع سياق منفصل لكل مستخدم
- واجهة MCP موحدة للتكامل مع أدوات AI
"""

__version__ = "2.0.0"
__author__ = "Twitter MCP Team"
__description__ = "Twitter MCP Server with OAuth 2.0 support"

# استيراد المكونات الرئيسية
from .oauth_manager import oauth_manager, TwitterOAuth2Manager
from .twitter_client import twitter_helper, TwitterClientHelper
from .database import db_manager, DatabaseManager, TwitterAccount
from .auth_api import auth_app
from .mcp_server import server as mcp_server

__all__ = [
    "oauth_manager",
    "TwitterOAuth2Manager", 
    "twitter_helper",
    "TwitterClientHelper",
    "db_manager",
    "DatabaseManager",
    "TwitterAccount",
    "auth_app",
    "mcp_server"
]