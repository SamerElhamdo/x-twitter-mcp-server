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

# استيراد المكونات الرئيسية - تجنب الاستيراد الدائري
from .auth_api import auth_app

__all__ = [
    "auth_app"
]