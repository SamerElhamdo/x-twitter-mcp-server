import asyncio
import logging
import warnings
from fastmcp import FastMCP
import tweepy
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .database import db_manager
from .auth_api import start_auth_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress SyntaxWarning from Tweepy docstrings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Initialize FastMCP server
server = FastMCP(name="TwitterMCPServer")

# بدء تشغيل خادم المصادقة
auth_server_thread = start_auth_server(host="127.0.0.1", port=8000)

def initialize_twitter_clients(username: str) -> tuple[tweepy.Client, Optional[tweepy.API]]:
    """Initialize Twitter API clients using OAuth 2.0."""
    
    # استخدام oauth_manager للحصول على client
    from .oauth_manager import oauth_manager
    
    # الحصول على Twitter client مع auto-refresh
    twitter_client = oauth_manager.get_client(username)
    if not twitter_client:
        raise ValueError(f"فشل في إنشاء client للحساب '{username}'. تأكد من إضافة الحساب أولاً عبر واجهة المصادقة.")
    
    # OAuth 2.0 pure - لا نحتاج v1.1 API
    # جميع العمليات تتم عبر OAuth 2.0 فقط
    twitter_v1_api = None

    return twitter_client, twitter_v1_api

# Rate limiting configuration
RATE_LIMITS = {
    "tweet_actions": {"limit": 300, "window": timedelta(minutes=15)},
    "dm_actions": {"limit": 1000, "window": timedelta(minutes=15)},
    "follow_actions": {"limit": 400, "window": timedelta(hours=24)},
    "like_actions": {"limit": 1000, "window": timedelta(hours=24)}
}

# In-memory rate limit tracking (use Redis in production)
rate_limit_counters = defaultdict(lambda: {"count": 0, "reset_time": datetime.now()})

def check_rate_limit(action_type: str) -> bool:
    """Check if the action is within rate limits."""
    config = RATE_LIMITS.get(action_type)
    if not config:
        return True  # No limit defined
    counter = rate_limit_counters[action_type]
    now = datetime.now()
    if now >= counter["reset_time"]:
        counter["count"] = 0
        counter["reset_time"] = now + config["window"]
    if counter["count"] >= config["limit"]:
        return False
    counter["count"] += 1
    return True

# Account Management Tools
@server.tool(name="add_twitter_account", description="Add a new Twitter account (OAuth 2.0)")
async def add_twitter_account(
    username: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    display_name: Optional[str] = None
) -> Dict:
    """Add a new Twitter account using OAuth 2.0 tokens.

    Args:
        username (str): Twitter username (without @)
        access_token (str): OAuth 2.0 Access Token (Bearer Token)
        refresh_token (Optional[str]): OAuth 2.0 Refresh Token
        display_name (Optional[str]): Display name for the account
    """
    try:
        success = db_manager.add_account(
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
            display_name=display_name
        )
        
        if success:
            # اختبار المفاتيح
            is_valid = db_manager.test_credentials(username)
            return {
                "success": True,
                "message": f"تم إضافة الحساب '{username}' بنجاح",
                "credentials_valid": is_valid,
                "note": "يمكنك الآن استخدام username فقط في الطلبات المستقبلية"
            }
        else:
            return {
                "success": False,
                "message": "فشل في إضافة الحساب"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ: {str(e)}"
        }

@server.tool(name="list_twitter_accounts", description="List all stored Twitter accounts")
async def list_twitter_accounts() -> List[Dict]:
    """List all Twitter accounts stored in the database."""
    try:
        accounts = db_manager.get_all_accounts()
        return [account.to_dict() for account in accounts]
    except Exception as e:
        return [{"error": f"خطأ في الحصول على الحسابات: {str(e)}"}]

@server.tool(name="test_twitter_account", description="Test if a Twitter account credentials are valid")
async def test_twitter_account(username: str) -> Dict:
    """Test if the stored credentials for a Twitter account are valid.

    Args:
        username (str): Twitter username to test
    """
    try:
        is_valid = db_manager.test_credentials(username)
        return {
            "username": username,
            "credentials_valid": is_valid,
            "message": "مفاتيح المصادقة صحيحة" if is_valid else "مفاتيح المصادقة غير صحيحة"
        }
    except Exception as e:
        return {
            "username": username,
            "credentials_valid": False,
            "message": f"خطأ في الاختبار: {str(e)}"
        }

@server.tool(name="remove_twitter_account", description="Remove a Twitter account from the database")
async def remove_twitter_account(username: str) -> Dict:
    """Remove a Twitter account from the database.

    Args:
        username (str): Twitter username to remove
    """
    try:
        success = db_manager.delete_account(username)
        if success:
            return {
                "success": True,
                "message": f"تم حذف الحساب '{username}' بنجاح"
            }
        else:
            return {
                "success": False,
                "message": f"الحساب '{username}' غير موجود"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ: {str(e)}"
        }

# User Management Tools
@server.tool(name="get_user_profile", description="Get detailed profile information for a user")
async def get_user_profile(user_id: str, username: str) -> Dict:
    """Fetches user profile by user ID.

    Args:
        user_id (str): The ID of the user to look up.
        username (str): Your Twitter username (stored in database)
    """
    client, _ = initialize_twitter_clients(username)
    user = client.get_user(id=user_id, user_fields=["id", "name", "username", "profile_image_url", "description"])
    return user.data

@server.tool(name="get_user_by_screen_name", description="Fetches a user by screen name")
async def get_user_by_screen_name(screen_name: str, username: str) -> Dict:
    """Fetches user by screen name.

    Args:
        screen_name (str): The screen name/username of the user.
        username (str): Your Twitter username (stored in database)
    """
    client, _ = initialize_twitter_clients(username)
    user = client.get_user(username=screen_name, user_fields=["id", "name", "username", "profile_image_url", "description"])
    return user.data

@server.tool(name="get_user_by_id", description="Fetches a user by ID")
async def get_user_by_id(user_id: str, username: str) -> Dict:
    """Fetches user by ID.

    Args:
        user_id (str): The ID of the user to look up.
        username (str): Your Twitter username (stored in database)
    """
    client, _ = initialize_twitter_clients(username)
    user = client.get_user(id=user_id, user_fields=["id", "name", "username", "profile_image_url", "description"])
    return user.data

@server.tool(name="get_user_followers", description="Retrieves a list of followers for a given user")
async def get_user_followers(
    user_id: str,
    username: str,
    count: Optional[int] = 100,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Retrieves a list of followers for a given user.

    Args:
        user_id (str): The user ID whose followers are to be retrieved.
        username (str): Your Twitter username (stored in database)
        count (Optional[int]): The number of followers to retrieve per page. Default is 100. Max is 100 for V2 API.
        cursor (Optional[str]): A pagination token for fetching the next set of results.
    """
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    followers = client.get_users_followers(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in followers.data]

@server.tool(name="get_user_following", description="Retrieves users the given user is following")
async def get_user_following(
    user_id: str,
    username: str,
    count: Optional[int] = 100,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Retrieves a list of users whom the given user is following.

    Args:
        user_id (str): The user ID whose following list is to be retrieved.
        username (str): Your Twitter username (stored in database)
        count (Optional[int]): The number of users to retrieve per page. Default is 100. Max is 100 for V2 API.
        cursor (Optional[str]): A pagination token for fetching the next set of results.
    """
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    following = client.get_users_following(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in following.data]

@server.tool(name="get_user_followers_you_know", description="Retrieves a list of common followers (simulated)")
async def get_user_followers_you_know(
    user_id: str,
    username: str,
    count: Optional[int] = 100,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Retrieves a list of common followers. (Simulated as Twitter API v2 doesn't directly support this).

    Args:
        user_id (str): The user ID to check for common followers.
        username (str): Your Twitter username (stored in database)
        count (Optional[int]): The number of followers to retrieve and check. Default is 100.
        cursor (Optional[str]): A pagination token for fetching the user's followers.
    """
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    # Simulate by fetching followers and filtering (v2 doesn't directly support mutual followers)
    followers = client.get_users_followers(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in followers.data][:count]

@server.tool(name="get_user_subscriptions", description="Retrieves a list of users to which the specified user is subscribed (uses following as proxy)")
async def get_user_subscriptions(
    user_id: str,
    username: str,
    count: Optional[int] = 100,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Retrieves a list of subscribed users. (Uses 'following' as a proxy as Twitter API v2 doesn't have a direct 'subscriptions' endpoint).

    Args:
        user_id (str): The user ID whose subscriptions (following list) are to be retrieved.
        username (str): Your Twitter username (stored in database)
        count (Optional[int]): The number of users to retrieve per page. Default is 100.
        cursor (Optional[str]): A pagination token for fetching the next set of results.
    """
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    # Use following as proxy for subscriptions
    subscriptions = client.get_users_following(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in subscriptions.data]

# Tweet Management Tools
@server.tool(name="post_tweet", description="Post a tweet with optional media, reply, and tags")
async def post_tweet(
    text: str,
    username: str,
    media_paths: Optional[List[str]] = None,
    reply_to: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict:
    """Posts a tweet.

    Args:
        text (str): The text content of the tweet. Max 280 characters.
        username (str): Your Twitter username (stored in database)
        media_paths (Optional[List[str]]): A list of local file paths to media (images, videos) to be uploaded and attached.
        reply_to (Optional[str]): The ID of the tweet to reply to.
        tags (Optional[List[str]]): A list of hashtags (without '#') to append to the tweet.
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    tweet_data = {"text": text}
    if reply_to:
        tweet_data["in_reply_to_tweet_id"] = reply_to
    if tags:
        tweet_data["text"] += " " + " ".join(f"#{tag}" for tag in tags)
    if media_paths:
        # OAuth 2.0 لا يدعم رفع الوسائط مباشرة عبر v2 API
        # يجب استخدام v1.1 API مع OAuth 1.0a للوسائط
        # للآن، نتجاهل الوسائط أو نعرض رسالة تحذير
        logger.warning("رفع الوسائط غير مدعوم حالياً مع OAuth 2.0. سيتم تجاهل الوسائط.")
        # يمكن إضافة دعم الوسائط لاحقاً عبر v1.1 API منفصل
    tweet = client.create_tweet(**tweet_data)
    logger.info(f"Type of response from client.create_tweet: {type(tweet)}; Content: {tweet}")
    return tweet.data

@server.tool(name="delete_tweet", description="Delete a tweet by its ID")
async def delete_tweet(tweet_id: str, username: str) -> Dict:
    """Deletes a tweet.

    Args:
        tweet_id (str): The ID of the tweet to delete.
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    result = client.delete_tweet(id=tweet_id)
    return {"id": tweet_id, "deleted": result.data["deleted"]}

@server.tool(name="get_tweet_details", description="Get detailed information about a specific tweet")
async def get_tweet_details(tweet_id: str, username: str) -> Dict:
    """Fetches tweet details.

    Args:
        tweet_id (str): The ID of the tweet to fetch.
        username (str): Your Twitter username (stored in database)
    """
    client, _ = initialize_twitter_clients(username)
    tweet = client.get_tweet(id=tweet_id, tweet_fields=["id", "text", "created_at", "author_id"])
    return tweet.data

@server.tool(name="create_poll_tweet", description="Create a tweet with a poll")
async def create_poll_tweet(
    text: str,
    choices: List[str],
    duration_minutes: int,
    username: str
) -> Dict:
    """Creates a poll tweet.

    Args:
        text (str): The question or text for the poll.
        choices (List[str]): A list of poll choices (2-4 choices, each max 25 characters).
        duration_minutes (int): Duration of the poll in minutes (min 5, max 10080 (7 days)).
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    poll_data = {
        "text": text,
        "poll_options": choices,
        "poll_duration_minutes": duration_minutes
    }
    tweet = client.create_tweet(**poll_data)
    return tweet.data

@server.tool(name="vote_on_poll", description="Vote on a poll (mocked)")
async def vote_on_poll(tweet_id: str, choice: str, username: str) -> Dict:
    """Votes on a poll. (Note: Twitter API v2 does not support programmatically voting on polls. This is a mock response.)

    Args:
        tweet_id (str): The ID of the tweet containing the poll.
        choice (str): The choice to vote for (must exactly match one of the poll options).
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    # Twitter API v2 doesn't support poll voting; return mock response
    return {"tweet_id": tweet_id, "choice": choice, "status": "voted"}

@server.tool(name="favorite_tweet", description="Favorites a tweet")
async def favorite_tweet(tweet_id: str, username: str) -> Dict:
    """Favorites a tweet.

    Args:
        tweet_id (str): The ID of the tweet to favorite (like).
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("like_actions"):
        raise Exception("Like action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    result = client.like(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "liked": result.data["liked"]}

@server.tool(name="unfavorite_tweet", description="Unfavorites a tweet")
async def unfavorite_tweet(tweet_id: str, username: str) -> Dict:
    """Unfavorites a tweet.

    Args:
        tweet_id (str): The ID of the tweet to unfavorite (unlike).
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("like_actions"):
        raise Exception("Like action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    result = client.unlike(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "liked": not result.data["liked"]}

@server.tool(name="bookmark_tweet", description="Adds the tweet to bookmarks")
async def bookmark_tweet(
    tweet_id: str,
    username: str,
    folder_id: Optional[str] = None
) -> Dict:
    """Bookmarks a tweet.

    Args:
        tweet_id (str): The ID of the tweet to bookmark.
        username (str): Your Twitter username (stored in database)
        folder_id (Optional[str]): The ID of the bookmark folder to add the tweet to. (Currently not supported by Tweepy v2 client, will be ignored).
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    result = client.bookmark(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "bookmarked": result.data["bookmarked"]}

@server.tool(name="delete_bookmark", description="Removes the tweet from bookmarks")
async def delete_bookmark(tweet_id: str, username: str) -> Dict:
    """Removes a bookmark.

    Args:
        tweet_id (str): The ID of the tweet to remove from bookmarks.
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    result = client.remove_bookmark(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "bookmarked": not result.data["bookmarked"]}

@server.tool(name="delete_all_bookmarks", description="Deletes all bookmarks (simulated)")
async def delete_all_bookmarks(username: str) -> Dict:
    """Deletes all bookmarks. (Simulated as Twitter API v2 doesn't have a direct endpoint for this. Fetches all bookmarks and deletes them one by one.)
    
    Args:
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    # Twitter API v2 doesn't have a direct endpoint; simulate by fetching and removing
    bookmarks = client.get_bookmarks()
    for bookmark in bookmarks.data:
        client.remove_bookmark(tweet_id=bookmark["id"])
    return {"status": "all bookmarks deleted"}

@server.tool(name="retweet", description="Retweet a tweet")
async def retweet(tweet_id: str, username: str) -> Dict:
    """Retweets a tweet.

    Args:
        tweet_id (str): The ID of the tweet to retweet.
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    result = client.retweet(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "retweeted": result.data["retweeted"]}

@server.tool(name="unretweet", description="Unretweet a tweet")
async def unretweet(tweet_id: str, username: str) -> Dict:
    """Unretweets a tweet.

    Args:
        tweet_id (str): The ID of the tweet to unretweet.
        username (str): Your Twitter username (stored in database)
    """
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients(username)
    result = client.unretweet(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "retweeted": not result.data["retweeted"]}

# Timeline & Search Tools
@server.tool(name="get_timeline", description="Get tweets from your home timeline (approx via v2)")
async def get_timeline(
    username: str,
    count: Optional[int] = 100,
    seen_tweet_ids: Optional[List[str]] = None,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Approximate home timeline using v2 only:
    - Get me -> following list
    - Build OR query: from:user1 OR from:user2 ...
    - search_recent_tweets(sort_order='recency')
    """
    client, _ = initialize_twitter_clients(username)
    # استخدام Bearer Token فقط (OAuth 2.0) - لا user_auth=True
    # استخدام Bearer Token authentication صراحة
    me = client.get_me().data
    # اجلب أوّل N من الذين تتابعهم (قلّل العدد لضبط طول الاستعلام)
    following = client.get_users_following(id=me.id, max_results=50, user_fields=["id"])
    if not following.data:
        return []
    # خُذ حتى 12 حساباً لبناء استعلام قصير
    author_ids = [u.id for u in following.data][:12]
    query = " OR ".join([f"from:{aid}" for aid in author_ids])
    # حدود v2: 10..100
    effective_count = 100 if (count is None or count > 100) else (10 if count < 10 else count)
    tweets = client.search_recent_tweets(
        query=query,
        max_results=effective_count,
        sort_order="recency",
        next_token=cursor,
        tweet_fields=["id", "text", "created_at","author_id"]
    )
    return [] if not tweets.data else [t.data for t in tweets.data]

@server.tool(name="get_latest_timeline", description="Get tweets from your following (approx via v2)")
async def get_latest_timeline(
    username: str,
    count: Optional[int] = 100
) -> List[Dict]:
    """Approx Following timeline using v2 only (reverse–ish via search_recent_tweets)."""
    client, _ = initialize_twitter_clients(username)
    # استخدام Bearer Token فقط (OAuth 2.0) - لا user_auth=True
    # استخدام Bearer Token authentication صراحة
    me = client.get_me().data
    following = client.get_users_following(id=me.id, max_results=50, user_fields=["id"])
    if not following.data:
        return []
    author_ids = [u.id for u in following.data][:12]
    query = " OR ".join([f"from:{aid}" for aid in author_ids])
    effective_count = 100 if (count is None or count > 100) else (10 if count < 10 else count)
    tweets = client.search_recent_tweets(
        query=query,
        max_results=effective_count,
        sort_order="recency",
        tweet_fields=["id","text","created_at","author_id"]
    )
    return [] if not tweets.data else [t.data for t in tweets.data]

@server.tool(name="search_twitter", description="Search Twitter with a query")
async def search_twitter(
    query: str,
    username: str,
    product: Optional[str] = "Top",
    count: Optional[int] = 100,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Searches Twitter for recent tweets.

    Args:
        query (str): The search query. Supports operators like #hashtag, from:user, etc.
        username (str): Your Twitter username (stored in database)
        product (Optional[str]): Sorting preference. 'Top' for relevancy (default), 'Latest' for recency.
        count (Optional[int]): Number of tweets to retrieve. Default 100. Min 10, Max 100 for search_recent_tweets.
        cursor (Optional[str]): Pagination token (next_token) for fetching the next set of results.
    """
    sort_order = "relevancy" if product == "Top" else "recency"
    
    # Ensure count is within the allowed range (10-100)
    if count is None:
        effective_count = 100 # Default to 100 if not provided
    elif count < 10:
        logger.info(f"Requested count {count} is less than minimum 10. Using 10 instead.")
        effective_count = 10
    elif count > 100:
        logger.info(f"Requested count {count} is greater than maximum 100. Using 100 instead.")
        effective_count = 100
    else:
        effective_count = count
        
    client, _ = initialize_twitter_clients(username)
    tweets = client.search_recent_tweets(query=query, max_results=effective_count, sort_order=sort_order, next_token=cursor, tweet_fields=["id", "text", "created_at"])
    return [tweet.data for tweet in tweets.data]

@server.tool(name="get_trends", description="Retrieves trending topics on Twitter")
async def get_trends(
    username: str,
    category: Optional[str] = None,
    count: Optional[int] = 50
) -> List[Dict]:
    """Fetches trending topics (uses Twitter API v1.1 as v2 trends require specific location WOEID).

    Args:
        username (str): Your Twitter username (stored in database)
        category (Optional[str]): Filter trends by category (e.g., 'Sports', 'News'). Currently not directly supported by `get_place_trends` for worldwide, will filter locally if provided.
        count (Optional[int]): Number of trending topics to retrieve. Default 50. Max 50 (as per Twitter API v1.1 default).
    """
    client, _ = initialize_twitter_clients(username)
    # Twitter API v2 لا يدعم الـ trends بدون موقع محدد
    # للآن، نعيد قائمة فارغة أو رسالة تحذير
    logger.warning("جلب الترندات غير مدعوم حالياً مع OAuth 2.0 v2 API.")
    return [{"name": "الترندات غير متاحة", "query": "OAuth 2.0 limitation", "tweet_volume": 0}]

@server.tool(name="get_highlights_tweets", description="Retrieves highlighted tweets from a user's timeline (simulated)")
async def get_highlights_tweets(
    user_id: str,
    username: str,
    count: Optional[int] = 100,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Fetches highlighted tweets from a user's timeline. (Simulated using user's timeline as Twitter API v2 doesn't have a direct 'highlights' endpoint).

    Args:
        user_id (str): The ID of the user whose highlights are to be fetched.
        username (str): Your Twitter username (stored in database)
        count (Optional[int]): Number of tweets to retrieve. Default 100. Min 5, Max 100 for get_users_tweets.
        cursor (Optional[str]): Pagination token for fetching the next set of results.
    """
    client, _ = initialize_twitter_clients(username)
    # Twitter API v2 doesn't have highlights; use user timeline
    tweets = client.get_users_tweets(id=user_id, max_results=count, pagination_token=cursor, tweet_fields=["id", "text", "created_at"])
    return [tweet.data for tweet in tweets.data]

@server.tool(name="get_user_mentions", description="Get tweets mentioning a specific user")
async def get_user_mentions(
    user_id: str,
    username: str,
    count: Optional[int] = 100,
    cursor: Optional[str] = None
) -> List[Dict]:
    """Fetches tweets mentioning a specific user.

    Args:
        user_id (str): The ID of the user whose mentions are to be retrieved.
        username (str): Your Twitter username (stored in database)
        count (Optional[int]): Number of mentions to retrieve. Default 100. Min 5, Max 100 for get_users_mentions.
        cursor (Optional[str]): Pagination token for fetching the next set of results.
    """
    client, _ = initialize_twitter_clients(username)
    mentions = client.get_users_mentions(id=user_id, max_results=count, pagination_token=cursor, tweet_fields=["id", "text", "created_at"])
    return [tweet.data for tweet in mentions.data]

# Main server execution
def run():
    """Entry point for running the FastMCP server directly."""
    logger.info(f"Starting {server.name}...")
    logger.info("✅ خادم المصادقة يعمل على http://127.0.0.1:8000")
    logger.info("📖 يمكنك إدارة الحسابات عبر: http://127.0.0.1:8000/docs")
    # Return the coroutine to be awaited by the caller (e.g., Claude Desktop)
    return server.run()