#!/usr/bin/env python3
"""
Twitter MCP Server - OAuth 2.0
خادم MCP منفصل يعمل مع mcp-proxy
"""

import asyncio
import logging
from fastmcp import FastMCP
import tweepy
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .database import db_manager
from .oauth_manager import oauth_manager
from .twitter_client import twitter_helper

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء خادم FastMCP
server = FastMCP(name="TwitterMCPServer")

def initialize_twitter_clients(username: str) -> tuple[tweepy.Client, tweepy.API]:
    """تهيئة عملاء Twitter API باستخدام البيانات المخزنة."""
    
    # الحصول على الحساب من قاعدة البيانات
    account = db_manager.get_account(username)
    if not account:
        raise ValueError(f"الحساب '{username}' غير موجود أو غير نشط. يرجى إضافته أولاً عبر واجهة API المصادقة.")
    
    # التحقق من صحة المفاتيح
    if not db_manager.test_credentials(username):
        raise ValueError(f"مفاتيح المصادقة للحساب '{username}' غير صحيحة. يرجى تحديثها.")
    
    # تهيئة عميل v2 API
    twitter_client = tweepy.Client(
        consumer_key=account.api_key,
        consumer_secret=account.api_secret,
        access_token=account.access_token,
        access_token_secret=account.access_token_secret,
        bearer_token=account.bearer_token
    )

    # تهيئة v1.1 API للملفات والعمليات غير المدعومة في v2
    auth = tweepy.OAuth1UserHandler(
        consumer_key=account.api_key,
        consumer_secret=account.api_secret,
        access_token=account.access_token,
        access_token_secret=account.access_token_secret
    )
    twitter_v1_api = tweepy.API(auth)

    return twitter_client, twitter_v1_api

# إعداد حدود المعدل
RATE_LIMITS = {
    "tweet_actions": {"limit": 300, "window": timedelta(minutes=15)},
    "dm_actions": {"limit": 1000, "window": timedelta(minutes=15)},
    "follow_actions": {"limit": 400, "window": timedelta(hours=24)},
    "like_actions": {"limit": 1000, "window": timedelta(hours=24)}
}

# تتبع حدود المعدل في الذاكرة (استخدم Redis في الإنتاج)
rate_limit_counters = defaultdict(lambda: {"count": 0, "reset_time": datetime.now()})

def check_rate_limit(action_type: str) -> bool:
    """التحقق من أن العملية ضمن حدود المعدل."""
    config = RATE_LIMITS.get(action_type)
    if not config:
        return True  # لا يوجد حد محدد
    counter = rate_limit_counters[action_type]
    now = datetime.now()
    if now >= counter["reset_time"]:
        counter["count"] = 0
        counter["reset_time"] = now + config["window"]
    if counter["count"] >= config["limit"]:
        return False
    counter["count"] += 1
    return True

# أدوات إدارة الحسابات
@server.tool(name="add_twitter_account", description="إضافة حساب Twitter جديد إلى قاعدة البيانات")
async def add_twitter_account(
    username: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str,
    bearer_token: str,
    display_name: Optional[str] = None
) -> Dict:
    """إضافة حساب Twitter جديد إلى قاعدة البيانات للاستخدام المستقبلي."""
    
    try:
        success = db_manager.add_account(
            username=username,
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            bearer_token=bearer_token,
            display_name=display_name
        )
        
        if success:
            return {
                "success": True,
                "message": f"تم إضافة الحساب '{username}' بنجاح",
                "username": username
            }
        else:
            return {
                "success": False,
                "message": "فشل في إضافة الحساب",
                "username": username
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في إضافة الحساب: {str(e)}",
            "username": username
        }

@server.tool(name="list_twitter_accounts", description="عرض جميع حسابات Twitter المخزنة")
async def list_twitter_accounts() -> List[Dict]:
    """عرض جميع حسابات Twitter المخزنة في قاعدة البيانات."""
    
    try:
        accounts = db_manager.get_all_accounts()
        return [
            {
                "username": account.username,
                "display_name": account.display_name,
                "created_at": account.created_at.isoformat() if account.created_at else None,
                "last_used": account.last_used.isoformat() if account.last_used else None,
                "is_active": account.is_active
            }
            for account in accounts
        ]
    except Exception as e:
        return [{"error": f"خطأ في جلب الحسابات: {str(e)}"}]

@server.tool(name="test_twitter_account", description="اختبار صحة مفاتيح مصادقة حساب Twitter")
async def test_twitter_account(username: str) -> Dict:
    """اختبار صحة مفاتيح مصادقة حساب Twitter محدد."""
    
    try:
        is_valid = db_manager.test_credentials(username)
        return {
            "username": username,
            "is_valid": is_valid,
            "message": "الحساب يعمل بشكل صحيح" if is_valid else "الحساب لا يعمل"
        }
    except Exception as e:
        return {
            "username": username,
            "is_valid": False,
            "message": f"خطأ في اختبار الحساب: {str(e)}"
        }

@server.tool(name="remove_twitter_account", description="إزالة حساب Twitter من قاعدة البيانات")
async def remove_twitter_account(username: str) -> Dict:
    """إزالة حساب Twitter من قاعدة البيانات."""
    
    try:
        success = db_manager.delete_account(username)
        return {
            "success": success,
            "message": f"تم حذف الحساب '{username}'" if success else f"فشل في حذف الحساب '{username}'",
            "username": username
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في حذف الحساب: {str(e)}",
            "username": username
        }

# أدوات إدارة التغريدات
@server.tool(name="post_tweet", description="نشر تغريدة جديدة")
async def post_tweet(username: str, text: str, reply_to: Optional[str] = None) -> Dict:
    """نشر تغريدة جديدة باستخدام حساب Twitter محدد."""
    
    try:
        if not check_rate_limit("tweet_actions"):
            return {
                "success": False,
                "message": "تم تجاوز حد المعدل لنشر التغريدات. يرجى الانتظار قليلاً."
            }
        
        result = twitter_helper.post_tweet(username, text, reply_to)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في نشر التغريدة: {str(e)}"
        }

@server.tool(name="delete_tweet", description="حذف تغريدة")
async def delete_tweet(username: str, tweet_id: str) -> Dict:
    """حذف تغريدة محددة."""
    
    try:
        result = twitter_helper.delete_tweet(username, tweet_id)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في حذف التغريدة: {str(e)}"
        }

@server.tool(name="like_tweet", description="الإعجاب بتغريدة")
async def like_tweet(username: str, tweet_id: str) -> Dict:
    """الإعجاب بتغريدة محددة."""
    
    try:
        if not check_rate_limit("like_actions"):
            return {
                "success": False,
                "message": "تم تجاوز حد المعدل للإعجابات. يرجى الانتظار قليلاً."
            }
        
        result = twitter_helper.like_tweet(username, tweet_id)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في الإعجاب بالتغريدة: {str(e)}"
        }

@server.tool(name="unlike_tweet", description="إلغاء الإعجاب بتغريدة")
async def unlike_tweet(username: str, tweet_id: str) -> Dict:
    """إلغاء الإعجاب بتغريدة محددة."""
    
    try:
        result = twitter_helper.unlike_tweet(username, tweet_id)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في إلغاء الإعجاب بالتغريدة: {str(e)}"
        }

@server.tool(name="retweet_tweet", description="إعادة تغريد")
async def retweet_tweet(username: str, tweet_id: str) -> Dict:
    """إعادة تغريد منشور محدد."""
    
    try:
        if not check_rate_limit("tweet_actions"):
            return {
                "success": False,
                "message": "تم تجاوز حد المعدل لإعادة التغريد. يرجى الانتظار قليلاً."
            }
        
        result = twitter_helper.retweet_tweet(username, tweet_id)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في إعادة التغريد: {str(e)}"
        }

@server.tool(name="unretweet_tweet", description="إلغاء إعادة التغريد")
async def unretweet_tweet(username: str, tweet_id: str) -> Dict:
    """إلغاء إعادة تغريد منشور محدد."""
    
    try:
        result = twitter_helper.unretweet_tweet(username, tweet_id)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في إلغاء إعادة التغريد: {str(e)}"
        }

# أدوات الحصول على المعلومات
@server.tool(name="get_user_info", description="الحصول على معلومات المستخدم")
async def get_user_info(username: str) -> Dict:
    """الحصول على معلومات المستخدم الحالي."""
    
    try:
        result = twitter_helper.get_user_info(username)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في الحصول على معلومات المستخدم: {str(e)}"
        }

@server.tool(name="get_user_tweets", description="الحصول على تغريدات المستخدم")
async def get_user_tweets(username: str, max_results: int = 10) -> Dict:
    """الحصول على تغريدات المستخدم الحالي."""
    
    try:
        result = twitter_helper.get_user_tweets(username, max_results)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في الحصول على التغريدات: {str(e)}"
        }

@server.tool(name="search_tweets", description="البحث في التغريدات")
async def search_tweets(username: str, query: str, max_results: int = 10) -> Dict:
    """البحث في التغريدات باستخدام استعلام محدد."""
    
    try:
        result = twitter_helper.search_tweets(username, query, max_results)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في البحث: {str(e)}"
        }

# تشغيل الخادم الرئيسي
def run():
    """نقطة الدخول لتشغيل خادم FastMCP مباشرة."""
    logger.info(f"بدء تشغيل {server.name}...")
    logger.info("✅ خادم MCP يعمل ويمكن استخدامه مع mcp-proxy")
    # إرجاع coroutine ليتم انتظاره من قبل المتصل (مثل Claude Desktop)
    return server.run()

if __name__ == "__main__":
    run()
