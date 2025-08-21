#!/usr/bin/env python3
"""
Simple MCP Server for Twitter - Compatible with mcp-proxy
"""

import asyncio
import json
import sys
from pathlib import Path

# إضافة المسار للوحدات
sys.path.insert(0, str(Path(__file__).parent / "src"))

def send_response(response_id, result=None, error=None):
    """إرسال استجابة إلى mcp-proxy"""
    if error:
        response = {
            "jsonrpc": "2.0",
            "id": response_id,
            "error": {
                "code": -1,
                "message": str(error)
            }
        }
    else:
        response = {
            "jsonrpc": "2.0",
            "id": response_id,
            "result": result
        }
    
    print(json.dumps(response), flush=True)

async def handle_request(request):
    """معالجة طلب MCP"""
    try:
        method = request.get("method")
        request_id = request.get("id")
        
        if method == "initialize":
            # استجابة التهيئة
            send_response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "Twitter MCP Server",
                    "version": "1.0.0"
                }
            })
            
        elif method == "tools/list":
            # قائمة الأدوات
            tools = [
                {
                    "name": "post_tweet",
                    "description": "Post a tweet",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "username": {"type": "string"}
                        },
                        "required": ["text", "username"]
                    }
                },
                {
                    "name": "list_accounts",
                    "description": "List Twitter accounts",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ]
            send_response(request_id, {"tools": tools})
            
        elif method == "tools/call":
            # استدعاء أداة
            params = request.get("params", {})
            tool_name = params.get("name")
            
            if tool_name == "post_tweet":
                text = params.get("arguments", {}).get("text", "")
                username = params.get("arguments", {}).get("username", "")
                
                # استيراد وتشغيل التغريد
                try:
                    from x_twitter_mcp.server import initialize_twitter_clients
                    client, _ = initialize_twitter_clients(username)
                    tweet = client.create_tweet(text=text)
                    
                    send_response(request_id, {
                        "content": [
                            {
                                "type": "text",
                                "text": f"✅ تم نشر التغريدة بنجاح! ID: {tweet.data['id']}"
                            }
                        ]
                    })
                except Exception as e:
                    send_response(request_id, error=f"فشل في نشر التغريدة: {str(e)}")
                    
            elif tool_name == "list_accounts":
                try:
                    from x_twitter_mcp.database import db_manager
                    accounts = db_manager.get_all_accounts()
                    account_list = [acc.username for acc in accounts]
                    
                    send_response(request_id, {
                        "content": [
                            {
                                "type": "text",
                                "text": f"الحسابات المتاحة: {', '.join(account_list) if account_list else 'لا توجد حسابات'}"
                            }
                        ]
                    })
                except Exception as e:
                    send_response(request_id, error=f"فشل في جلب الحسابات: {str(e)}")
                    
            else:
                send_response(request_id, error=f"أداة غير معروفة: {tool_name}")
                
        else:
            # تجاهل الطلبات الأخرى
            pass
            
    except Exception as e:
        send_response(request.get("id", 0), error=str(e))

async def main():
    """الدالة الرئيسية"""
    print("🚀 Simple Twitter MCP Server Started", flush=True)
    
    try:
        while True:
            # قراءة طلب من stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                await handle_request(request)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr, flush=True)
                
    except KeyboardInterrupt:
        print("🛑 Server stopped by user", flush=True)
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
