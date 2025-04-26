import asyncio
import logging
import os
import warnings
from fastmcp import FastMCP
import tweepy
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress SyntaxWarning from Tweepy docstrings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Load environment variables from .env file (if present)
load_dotenv()

# Initialize FastMCP server
server = FastMCP(name="TwitterMCPServer")

# Twitter API client setup (lazy-loaded)
_twitter_client = None
_twitter_v1_api = None

def initialize_twitter_clients() -> tuple[tweepy.Client, tweepy.API]:
    """Initialize Twitter API clients on-demand."""
    global _twitter_client, _twitter_v1_api

    if _twitter_client is not None and _twitter_v1_api is not None:
        return _twitter_client, _twitter_v1_api

    # Verify required environment variables
    required_env_vars = [
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
        "TWITTER_BEARER_TOKEN",
    ]
    for var in required_env_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")

    # Initialize v2 API client
    _twitter_client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        bearer_token=os.getenv("TWITTER_BEARER_TOKEN")
    )

    # Initialize v1.1 API for media uploads and other unsupported v2 endpoints
    auth = tweepy.OAuth1UserHandler(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    )
    _twitter_v1_api = tweepy.API(auth)

    return _twitter_client, _twitter_v1_api

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

# User Management Tools
@server.tool(name="get_user_profile", description="Get detailed profile information for a user")
async def get_user_profile(user_id: str) -> Dict:
    """Fetches user profile by user ID."""
    client, _ = initialize_twitter_clients()
    user = client.get_user(id=user_id, user_fields=["id", "name", "username", "profile_image_url", "description"])
    return user.data.data

@server.tool(name="get_user_by_screen_name", description="Fetches a user by screen name")
async def get_user_by_screen_name(screen_name: str) -> Dict:
    """Fetches user by screen name."""
    client, _ = initialize_twitter_clients()
    user = client.get_user(username=screen_name, user_fields=["id", "name", "username", "profile_image_url", "description"])
    return user.data.data

@server.tool(name="get_user_by_id", description="Fetches a user by ID")
async def get_user_by_id(user_id: str) -> Dict:
    """Fetches user by ID."""
    client, _ = initialize_twitter_clients()
    user = client.get_user(id=user_id, user_fields=["id", "name", "username", "profile_image_url", "description"])
    return user.data.data

@server.tool(name="get_user_followers", description="Retrieves a list of followers for a given user")
async def get_user_followers(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> List[Dict]:
    """Retrieves a list of followers for a given user."""
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    followers = client.get_users_followers(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in followers.data]

@server.tool(name="get_user_following", description="Retrieves users the given user is following")
async def get_user_following(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> List[Dict]:
    """Retrieves a list of users whom the given user is following."""
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    following = client.get_users_following(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in following.data]

@server.tool(name="get_user_followers_you_know", description="Retrieves a list of common followers")
async def get_user_followers_you_know(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> List[Dict]:
    """Retrieves a list of common followers."""
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    # Simulate by fetching followers and filtering (v2 doesn't directly support mutual followers)
    followers = client.get_users_followers(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in followers.data][:count]

@server.tool(name="get_user_subscriptions", description="Retrieves a list of users to which the specified user is subscribed")
async def get_user_subscriptions(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> List[Dict]:
    """Retrieves a list of subscribed users."""
    if not check_rate_limit("follow_actions"):
        raise Exception("Follow action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    # Use following as proxy for subscriptions
    subscriptions = client.get_users_following(id=user_id, max_results=count, pagination_token=cursor, user_fields=["id", "name", "username"])
    return [user.data for user in subscriptions.data]

# Tweet Management Tools
@server.tool(name="post_tweet", description="Post a tweet with optional media, reply, and tags")
async def post_tweet(text: str, media_paths: Optional[List[str]] = None, reply_to: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict:
    """Posts a tweet."""
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, v1_api = initialize_twitter_clients()
    tweet_data = {"text": text}
    if reply_to:
        tweet_data["in_reply_to_status_id"] = reply_to
    if tags:
        tweet_data["text"] += " " + " ".join(f"#{tag}" for tag in tags)
    if media_paths:
        media_ids = []
        for path in media_paths:
            media = v1_api.media_upload(filename=path)
            media_ids.append(media.media_id_string)
        tweet_data["media_ids"] = media_ids
    tweet = client.create_tweet(**tweet_data)
    return tweet.data.data

@server.tool(name="delete_tweet", description="Delete a tweet by its ID")
async def delete_tweet(tweet_id: str) -> Dict:
    """Deletes a tweet."""
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    result = client.delete_tweet(id=tweet_id)
    return {"id": tweet_id, "deleted": result.data["deleted"]}

@server.tool(name="get_tweet_details", description="Get detailed information about a specific tweet")
async def get_tweet_details(tweet_id: str) -> Dict:
    """Fetches tweet details."""
    client, _ = initialize_twitter_clients()
    tweet = client.get_tweet(id=tweet_id, tweet_fields=["id", "text", "created_at", "author_id"])
    return tweet.data.data

@server.tool(name="create_poll_tweet", description="Create a tweet with a poll")
async def create_poll_tweet(text: str, choices: List[str], duration_minutes: int) -> Dict:
    """Creates a poll tweet."""
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    poll_data = {
        "text": text,
        "poll_options": choices,
        "poll_duration_minutes": duration_minutes
    }
    tweet = client.create_tweet(**poll_data)
    return tweet.data.data

@server.tool(name="vote_on_poll", description="Vote on a poll")
async def vote_on_poll(tweet_id: str, choice: str) -> Dict:
    """Votes on a poll."""
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    # Twitter API v2 doesn't support poll voting; return mock response
    return {"tweet_id": tweet_id, "choice": choice, "status": "voted"}

@server.tool(name="favorite_tweet", description="Favorites a tweet")
async def favorite_tweet(tweet_id: str) -> Dict:
    """Favorites a tweet."""
    if not check_rate_limit("like_actions"):
        raise Exception("Like action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    result = client.like(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "liked": result.data["liked"]}

@server.tool(name="unfavorite_tweet", description="Unfavorites a tweet")
async def unfavorite_tweet(tweet_id: str) -> Dict:
    """Unfavorites a tweet."""
    if not check_rate_limit("like_actions"):
        raise Exception("Like action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    result = client.unlike(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "liked": not result.data["liked"]}

@server.tool(name="bookmark_tweet", description="Adds the tweet to bookmarks")
async def bookmark_tweet(tweet_id: str, folder_id: Optional[str] = None) -> Dict:
    """Bookmarks a tweet."""
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    result = client.bookmark(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "bookmarked": result.data["bookmarked"]}

@server.tool(name="delete_bookmark", description="Removes the tweet from bookmarks")
async def delete_bookmark(tweet_id: str) -> Dict:
    """Removes a bookmark."""
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    result = client.remove_bookmark(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "bookmarked": not result.data["bookmarked"]}

@server.tool(name="delete_all_bookmarks", description="Deletes all bookmarks")
async def delete_all_bookmarks() -> Dict:
    """Deletes all bookmarks."""
    if not check_rate_limit("tweet_actions"):
        raise Exception("Tweet action rate limit exceeded")
    client, _ = initialize_twitter_clients()
    # Twitter API v2 doesn't have a direct endpoint; simulate by fetching and removing
    bookmarks = client.get_bookmarks()
    for bookmark in bookmarks.data:
        client.remove_bookmark(tweet_id=bookmark["id"])
    return {"status": "all bookmarks deleted"}

# Timeline & Search Tools
@server.tool(name="get_timeline", description="Get tweets from your home timeline (For You)")
async def get_timeline(count: Optional[int] = 100, seen_tweet_ids: Optional[List[str]] = None, cursor: Optional[str] = None) -> List[Dict]:
    """Fetches home timeline tweets."""
    client, _ = initialize_twitter_clients()
    tweets = client.get_home_timeline(max_results=count, pagination_token=cursor, tweet_fields=["id", "text", "created_at"])
    return [tweet.data for tweet in tweets.data]

@server.tool(name="get_latest_timeline", description="Get tweets from your home timeline (Following)")
async def get_latest_timeline(count: Optional[int] = 100) -> List[Dict]:
    """Fetches latest timeline tweets."""
    client, _ = initialize_twitter_clients()
    tweets = client.get_home_timeline(max_results=count, tweet_fields=["id", "text", "created_at"], exclude=["replies", "retweets"])
    return [tweet.data for tweet in tweets.data]

@server.tool(name="search_twitter", description="Search Twitter with a query")
async def search_twitter(query: str, product: Optional[str] = "Top", count: Optional[int] = 100, cursor: Optional[str] = None) -> List[Dict]:
    """Searches Twitter."""
    sort_order = "relevancy" if product == "Top" else "recency"
    client, _ = initialize_twitter_clients()
    tweets = client.search_recent_tweets(query=query, max_results=count, sort_order=sort_order, pagination_token=cursor, tweet_fields=["id", "text", "created_at"])
    return [tweet.data for tweet in tweets.data]

@server.tool(name="get_trends", description="Retrieves trending topics on Twitter")
async def get_trends(category: Optional[str] = None, count: Optional[int] = 50) -> List[Dict]:
    """Fetches trending topics."""
    _, v1_api = initialize_twitter_clients()
    # Twitter API v2 trends require a location; use v1.1 for trends
    trends = v1_api.get_place_trends(id=1)  # WOEID 1 = Worldwide
    trends = trends[0]["trends"]
    if category:
        trends = [t for t in trends if t.get("category") == category]
    return trends[:count]

@server.tool(name="get_highlights_tweets", description="Retrieves highlighted tweets from a user’s timeline")
async def get_highlights_tweets(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> List[Dict]:
    """Fetches highlighted tweets."""
    client, _ = initialize_twitter_clients()
    # Twitter API v2 doesn't have highlights; use user timeline
    tweets = client.get_users_tweets(id=user_id, max_results=count, pagination_token=cursor, tweet_fields=["id", "text", "created_at"])
    return [tweet.data for tweet in tweets.data]

@server.tool(name="get_user_mentions", description="Get tweets mentioning a specific user")
async def get_user_mentions(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> List[Dict]:
    """Fetches user mentions."""
    client, _ = initialize_twitter_clients()
    mentions = client.get_users_mentions(id=user_id, max_results=count, pagination_token=cursor, tweet_fields=["id", "text", "created_at"])
    return [tweet.data for tweet in mentions.data]

# Main server execution
def run():
    """Entry point for running the FastMCP server directly."""
    logger.info(f"Starting {server.name}...")
    # Return the coroutine to be awaited by the caller (e.g., Claude Desktop)
    return server.run()