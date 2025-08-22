"""
Twitter Client Helper - دوال مساعدة لاستخدام Twitter API v2 مع OAuth 2.0
"""
import os
from typing import Optional, Dict, List, Any
import tweepy
from .oauth_manager import oauth_manager
from .database import db_manager

class TwitterClientHelper:
    """مساعد عميل Twitter مع OAuth 2.0"""
    
    @staticmethod
    def get_client_for_user(username: str) -> Optional[tweepy.Client]:
        """الحصول على عميل Twitter لمستخدم محدد مع تجديد التوكن تلقائياً"""
        return oauth_manager.create_client_for_user(username)
    
    @staticmethod
    def like_tweet(username: str, tweet_id: str) -> Dict[str, Any]:
        """إعجاب بتغريدة
        
        Args:
            username (str): اسم المستخدم
            tweet_id (str): معرف التغريدة
            
        Returns:
            Dict: نتيجة العملية
        """
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            # إعجاب بالتغريدة (v2): POST /2/users/:id/likes
            response = client.like(tweet_id=tweet_id, user_auth=True)
            
            if response.data:
                return {
                    "success": True,
                    "message": f"تم الإعجاب بالتغريدة {tweet_id} بنجاح",
                    "data": response.data
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في الإعجاب بالتغريدة"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في الإعجاب بالتغريدة: {str(e)}"
            }
    
    @staticmethod
    def unlike_tweet(username: str, tweet_id: str) -> Dict[str, Any]:
        """إلغاء الإعجاب بتغريدة"""
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            response = client.unlike(tweet_id=tweet_id, user_auth=True)
            
            if response.data:
                return {
                    "success": True,
                    "message": f"تم إلغاء الإعجاب بالتغريدة {tweet_id} بنجاح",
                    "data": response.data
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في إلغاء الإعجاب بالتغريدة"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في إلغاء الإعجاب بالتغريدة: {str(e)}"
            }
    
    @staticmethod
    def retweet_tweet(username: str, tweet_id: str) -> Dict[str, Any]:
        """إعادة تغريد
        
        Args:
            username (str): اسم المستخدم
            tweet_id (str): معرف التغريدة
            
        Returns:
            Dict: نتيجة العملية
        """
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            # إعادة تغريد (v2): POST /2/users/:id/retweets
            response = client.retweet(tweet_id=tweet_id, user_auth=True)
            
            if response.data:
                return {
                    "success": True,
                    "message": f"تم إعادة تغريد {tweet_id} بنجاح",
                    "data": response.data
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في إعادة التغريد"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في إعادة التغريد: {str(e)}"
            }
    
    @staticmethod
    def unretweet_tweet(username: str, tweet_id: str) -> Dict[str, Any]:
        """إلغاء إعادة التغريد"""
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            response = client.unretweet(tweet_id=tweet_id, user_auth=True)
            
            if response.data:
                return {
                    "success": True,
                    "message": f"تم إلغاء إعادة تغريد {tweet_id} بنجاح",
                    "data": response.data
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في إلغاء إعادة التغريد"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في إلغاء إعادة التغريد: {str(e)}"
            }
    
    @staticmethod
    def post_tweet(username: str, text: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """نشر تغريدة جديدة
        
        Args:
            username (str): اسم المستخدم
            text (str): نص التغريدة
            reply_to (str, optional): معرف التغريدة المراد الرد عليها
            
        Returns:
            Dict: نتيجة العملية
        """
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            # نشر التغريدة
            response = client.create_tweet(
                text=text,
                in_reply_to_tweet_id=reply_to if reply_to else None,
                user_auth=True
            )
            
            if response.data:
                return {
                    "success": True,
                    "message": "تم نشر التغريدة بنجاح",
                    "data": response.data,
                    "tweet_id": response.data["id"]
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في نشر التغريدة"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في نشر التغريدة: {str(e)}"
            }
    
    @staticmethod
    def delete_tweet(username: str, tweet_id: str) -> Dict[str, Any]:
        """حذف تغريدة"""
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            response = client.delete_tweet(id=tweet_id, user_auth=True)
            
            if response.data:
                return {
                    "success": True,
                    "message": f"تم حذف التغريدة {tweet_id} بنجاح",
                    "data": response.data
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في حذف التغريدة"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في حذف التغريدة: {str(e)}"
            }
    
    @staticmethod
    def get_user_info(username: str) -> Dict[str, Any]:
        """الحصول على معلومات المستخدم"""
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            # الحصول على معلومات المستخدم الحالي
            me = client.get_me(user_auth=True)
            
            if me.data:
                user = me.data
                return {
                    "success": True,
                    "data": {
                        "id": user.id,
                        "username": user.username,
                        "name": user.name,
                        "description": user.description,
                        "location": user.location,
                        "followers_count": user.public_metrics.followers_count if user.public_metrics else None,
                        "following_count": user.public_metrics.following_count if user.public_metrics else None,
                        "tweet_count": user.public_metrics.tweet_count if user.public_metrics else None,
                        "verified": user.verified,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "فشل في الحصول على معلومات المستخدم"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في الحصول على معلومات المستخدم: {str(e)}"
            }
    
    @staticmethod
    def get_user_tweets(username: str, max_results: int = 10) -> Dict[str, Any]:
        """الحصول على تغريدات المستخدم"""
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            # الحصول على تغريدات المستخدم
            tweets = client.get_users_tweets(
                id=username,
                max_results=max_results,
                user_auth=True
            )
            
            if tweets.data:
                return {
                    "success": True,
                    "data": [
                        {
                            "id": tweet.id,
                            "text": tweet.text,
                            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                            "public_metrics": {
                                "retweet_count": tweet.public_metrics.retweet_count if tweet.public_metrics else 0,
                                "like_count": tweet.public_metrics.like_count if tweet.public_metrics else 0,
                                "reply_count": tweet.public_metrics.reply_count if tweet.public_metrics else 0
                            } if tweet.public_metrics else {}
                        }
                        for tweet in tweets.data
                    ]
                }
            else:
                return {
                    "success": True,
                    "data": [],
                    "message": "لا توجد تغريدات"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في الحصول على التغريدات: {str(e)}"
            }
    
    @staticmethod
    def search_tweets(username: str, query: str, max_results: int = 10) -> Dict[str, Any]:
        """البحث في التغريدات"""
        try:
            client = TwitterClientHelper.get_client_for_user(username)
            if not client:
                return {
                    "success": False,
                    "error": "فشل في إنشاء عميل Twitter"
                }
            
            # البحث في التغريدات
            tweets = client.search_recent_tweets(
                query=query,
                max_results=max_results,
                user_auth=True
            )
            
            if tweets.data:
                return {
                    "success": True,
                    "data": [
                        {
                            "id": tweet.id,
                            "text": tweet.text,
                            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                            "author_id": tweet.author_id
                        }
                        for tweet in tweets.data
                    ]
                }
            else:
                return {
                    "success": True,
                    "data": [],
                    "message": "لا توجد نتائج للبحث"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في البحث: {str(e)}"
            }

# إنشاء مثيل عام من المساعد
twitter_helper = TwitterClientHelper()
