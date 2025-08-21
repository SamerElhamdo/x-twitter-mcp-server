#!/usr/bin/env python3
"""
Twitter MCP Server - Async Version for mcp-proxy
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# استيراد الكود المطلوب
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from x_twitter_mcp.database import db_manager
from x_twitter_mcp.server import initialize_twitter_clients

# إنشاء قاعدة البيانات
db_manager.create_tables()

# تعريف الأدوات
TOOLS = [
    Tool(
        name="post_tweet",
        description="نشر تغريدة جديدة على Twitter",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "نص التغريدة"
                },
                "username": {
                    "type": "string",
                    "description": "اسم المستخدم للحساب المراد التغريد منه"
                }
            },
            "required": ["text", "username"]
        }
    ),
    Tool(
        name="list_twitter_accounts",
        description="عرض جميع حسابات Twitter المحفوظة",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="test_twitter_account",
        description="اختبار صحة مفاتيح مصادقة حساب Twitter",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "اسم المستخدم للحساب المراد اختباره"
                }
            },
            "required": ["username"]
        }
    )
]

class TwitterMCPServer:
    """خادم MCP لـ Twitter"""
    
    def __init__(self):
        self.server = Server("twitter-mcp-server")
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات الطلبات"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """عرض الأدوات المتاحة"""
            return ListToolsResult(tools=TOOLS)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """تنفيذ أداة"""
            try:
                if name == "post_tweet":
                    return await self.post_tweet(arguments)
                elif name == "list_twitter_accounts":
                    return await self.list_accounts()
                elif name == "test_twitter_account":
                    return await self.test_account(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"أداة غير معروفة: {name}")]
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"خطأ: {str(e)}")]
                )
    
    async def post_tweet(self, args: Dict[str, Any]) -> CallToolResult:
        """نشر تغريدة"""
        text = args.get("text", "")
        username = args.get("username", "")
        
        if not text or not username:
            return CallToolResult(
                content=[TextContent(type="text", text="النص واسم المستخدم مطلوبان")]
            )
        
        try:
            client, v1_api = initialize_twitter_clients(username)
            tweet_data = {"text": text}
            tweet = client.create_tweet(**tweet_data)
            
            if hasattr(tweet, 'data') and tweet.data:
                tweet_id = tweet.data.get("id", "غير محدد")
            else:
                tweet_id = "غير محدد"
            
            result = f"تم نشر التغريدة بنجاح! معرف التغريدة: {tweet_id}"
            return CallToolResult(content=[TextContent(type="text", text=result)])
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"فشل في نشر التغريدة: {str(e)}")]
            )
    
    async def list_accounts(self) -> CallToolResult:
        """عرض الحسابات"""
        try:
            accounts = db_manager.get_all_accounts()
            if not accounts:
                return CallToolResult(
                    content=[TextContent(type="text", text="لا توجد حسابات محفوظة")]
                )
            
            account_list = []
            for account in accounts:
                account_list.append(f"• {account.username} ({account.display_name or 'بدون اسم'})")
            
            result = "الحسابات المحفوظة:\n" + "\n".join(account_list)
            return CallToolResult(content=[TextContent(type="text", text=result)])
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"خطأ في جلب الحسابات: {str(e)}")]
            )
    
    async def test_account(self, args: Dict[str, Any]) -> CallToolResult:
        """اختبار الحساب"""
        username = args.get("username", "")
        
        if not username:
            return CallToolResult(
                content=[TextContent(type="text", text="اسم المستخدم مطلوب")]
            )
        
        try:
            client, v1_api = initialize_twitter_clients(username)
            # محاولة جلب معلومات المستخدم
            me = client.get_me()
            result = f"✅ الحساب '{username}' يعمل بشكل صحيح"
            return CallToolResult(content=[TextContent(type="text", text=result)])
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ فشل في اختبار الحساب '{username}': {str(e)}")]
            )

async def main():
    """الدالة الرئيسية"""
    server = TwitterMCPServer()
    
    # تشغيل الخادم
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="twitter-mcp-server",
                server_version="1.0.0",
                capabilities=server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
