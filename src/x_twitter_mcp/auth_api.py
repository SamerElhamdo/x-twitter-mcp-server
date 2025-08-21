from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from .database import db_manager, TwitterAccount
from .oauth_manager import oauth_manager
from .sse_manager import sse_manager
from .ai_processor import ai_processor
import threading
import time
import os
import json
import secrets

# إنشاء تطبيق FastAPI
auth_app = FastAPI(
    title="Twitter MCP Authentication API",
    description="واجهة API لإدارة حسابات Twitter في MCP Server مع OAuth",
    version="2.0.0"
)

# إعداد القوالب (اختياري)
templates = Jinja2Templates(directory="templates") if os.path.exists("templates") else None

# نماذج البيانات
class AccountCreate(BaseModel):
    username: str
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: str
    display_name: Optional[str] = None

class AccountResponse(BaseModel):
    username: str
    display_name: Optional[str]
    created_at: Optional[str]
    last_used: Optional[str]
    is_active: bool

class AccountUpdate(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    access_token_secret: Optional[str] = None
    bearer_token: Optional[str] = None
    display_name: Optional[str] = None

class TestCredentialsResponse(BaseModel):
    username: str
    is_valid: bool
    message: str

class OAuthRequest(BaseModel):
    username: str

# الصفحة الرئيسية
@auth_app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """الصفحة الرئيسية مع زر واحد للمصادقة"""
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ربط حساب Twitter</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container { 
                background: white; 
                padding: 50px; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
                text-align: center;
                max-width: 500px;
                width: 90%;
            }
            h1 { 
                color: #1da1f2; 
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .description {
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1em;
                line-height: 1.6;
            }
            .connect-btn { 
                background: linear-gradient(45deg, #1da1f2, #1991db);
                color: white; 
                border: none; 
                padding: 20px 40px; 
                border-radius: 50px; 
                font-size: 1.3em;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 10px 20px rgba(29, 161, 242, 0.3);
                text-decoration: none;
                display: inline-block;
            }
            .connect-btn:hover { 
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(29, 161, 242, 0.4);
            }
            .connect-btn:active {
                transform: translateY(-1px);
            }
            .icon {
                font-size: 1.5em;
                margin-right: 10px;
            }
            .footer {
                margin-top: 40px;
                color: #999;
                font-size: 0.9em;
            }
            .accounts-section {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }
            .accounts-btn {
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                margin-top: 15px;
            }
            .accounts-btn:hover {
                background: #5a6268;
            }
            #accountsList {
                margin-top: 15px;
                text-align: right;
            }
            .account-item {
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 10px;
                border-left: 4px solid #1da1f2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐦 ربط حساب Twitter</h1>
            
            <div class="description">
                اضغط على الزر أدناه لربط حسابك على Twitter مع النظام
                <br><br>
                <strong>سيتم توجيهك مباشرة إلى Twitter للموافقة</strong>
            </div>
            
            <a href="/auth/redirect-to-twitter" class="connect-btn">
                <span class="icon">🔗</span>
                اربط حسابك
            </a>
            
            <div class="accounts-section">
                <button onclick="listAccounts()" class="accounts-btn">
                    📋 عرض الحسابات المرتبطة
                </button>
                <div id="accountsList"></div>
            </div>
            
            <div class="footer">
                نظام ربط حسابات Twitter مع MCP Server
            </div>
        </div>
        
        <script>
            async function listAccounts() {
                try {
                    const response = await fetch('/accounts/');
                    const accounts = await response.json();
                    
                    const accountsDiv = document.getElementById('accountsList');
                    if (accounts.length === 0) {
                        accountsDiv.innerHTML = '<p style="color: #666; margin-top: 15px;">لا توجد حسابات مرتبطة</p>';
                        return;
                    }
                    
                    let html = '<div style="margin-top: 15px;">';
                    accounts.forEach(account => {
                        html += `
                            <div class="account-item">
                                <strong>@${account.username}</strong><br>
                                <small>الاسم: ${account.display_name || 'غير محدد'}</small><br>
                                <small>تاريخ الربط: ${account.created_at || 'غير محدد'}</small><br>
                                <small>الحالة: ${account.is_active ? '✅ نشط' : '❌ غير نشط'}</small>
                            </div>
                        `;
                    });
                    html += '</div>';
                    accountsDiv.innerHTML = html;
                } catch (error) {
                    document.getElementById('accountsList').innerHTML = `
                        <p style="color: #dc3545; margin-top: 15px;">❌ خطأ في جلب الحسابات: ${error.message}</p>
                    `;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# نقطة نهاية OAuth
@auth_app.get("/auth/oauth-url")
async def get_oauth_url(username: str = Query(..., description="اسم المستخدم المطلوب")):
    """إنشاء رابط مصادقة OAuth لـ Twitter مع username محدد"""
    try:
        auth_url, state = oauth_manager.get_authorization_url(username)
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "message": f"تم إنشاء رابط المصادقة لـ @{username}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# نقطة نهاية OAuth العام
@auth_app.get("/auth/public-oauth")
async def get_public_oauth():
    """إنشاء رابط مصادقة OAuth عام للجميع"""
    try:
        auth_url = oauth_manager.get_public_oauth_url()
        return {
            "success": True,
            "auth_url": auth_url,
            "message": "رابط المصادقة العام جاهز"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# نقطة نهاية OAuth البسيط (بدون PKCE)
@auth_app.get("/auth/simple-oauth")
async def get_simple_oauth():
    """إنشاء رابط مصادقة OAuth بسيط بدون PKCE"""
    try:
        auth_url = oauth_manager.get_simple_oauth_url()
        return {
            "success": True,
            "auth_url": auth_url,
            "message": "رابط المصادقة البسيط جاهز"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# نقطة نهاية التوجيه المباشر
@auth_app.get("/auth/redirect-to-twitter")
async def redirect_to_twitter():
    """التوجيه المباشر إلى Twitter للمصادقة"""
    try:
        auth_url = oauth_manager.get_public_oauth_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <title>خطأ</title>
        </head>
        <body>
            <h1>خطأ في إنشاء رابط المصادقة</h1>
            <p>{str(e)}</p>
            <a href="/">العودة للصفحة الرئيسية</a>
        </body>
        </html>
        """)

# نقطة نهاية Callback
@auth_app.get("/auth/callback")
async def oauth_callback(
    oauth_token: str = Query(..., description="رمز OAuth من Twitter"),
    oauth_verifier: str = Query(..., description="رمز التحقق من Twitter"),
    state: str = Query(None, description="حالة OAuth (اختياري)")
):
    """معالجة callback من Twitter OAuth 1.0a"""
    try:
        if state:
            # استخدام username محدد
            result = oauth_manager.handle_callback(oauth_token, oauth_verifier, state)
        else:
            # استخدام الرابط العام
            result = oauth_manager.handle_public_callback(oauth_token, oauth_verifier)
        
        if result["success"]:
            # صفحة نجاح
            username = result.get("username", "المستخدم")
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <title>تمت المصادقة بنجاح</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; margin: 50px; background: #f5f8fa; }}
                    .success {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .success-icon {{ font-size: 60px; color: #28a745; }}
                    .back-btn {{ background: #1da1f2; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin-top: 20px; }}
                    .username {{ background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 15px 0; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="success">
                    <div class="success-icon">✅</div>
                    <h1>تمت المصادقة بنجاح!</h1>
                    <p>{result['message']}</p>
                    <div class="username">
                        اسم المستخدم: @{username}
                    </div>
                    <p>يمكنك الآن إغلاق هذه الصفحة والعودة إلى Claude Desktop</p>
                    <p><strong>لاستخدام الحساب:</strong></p>
                    <p><code>Post a tweet saying "Hello!" using username "{username}"</code></p>
                    <a href="/" class="back-btn">العودة للصفحة الرئيسية</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        else:
            # صفحة خطأ
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <title>خطأ في المصادقة</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; margin: 50px; background: #f5f8fa; }}
                    .error {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error-icon {{ font-size: 60px; color: #dc3545; }}
                    .back-btn {{ background: #1da1f2; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <div class="error-icon">❌</div>
                    <h1>خطأ في المصادقة</h1>
                    <p>{result['error']}</p>
                    <a href="/" class="back-btn">العودة للصفحة الرئيسية</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
            
    except Exception as e:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <title>خطأ</title>
        </head>
        <body>
            <h1>خطأ</h1>
            <p>{str(e)}</p>
        </body>
        </html>
        """)

# نقطة نهاية لإنشاء حساب جديد (يدوي)
@auth_app.post("/accounts/", response_model=AccountResponse)
async def create_account(account: AccountCreate):
    """إنشاء حساب Twitter جديد أو تحديثه إذا كان موجوداً"""
    try:
        success = db_manager.add_account(
            username=account.username,
            api_key=account.api_key,
            api_secret=account.api_secret,
            access_token=account.access_token,
            access_token_secret=account.access_token_secret,
            bearer_token=account.bearer_token,
            display_name=account.display_name
        )
        
        if success:
            # الحصول على الحساب المُحدث
            saved_account = db_manager.get_account(account.username)
            if saved_account:
                return AccountResponse(**saved_account.to_dict())
            else:
                raise HTTPException(status_code=500, detail="فشل في حفظ الحساب")
        else:
            raise HTTPException(status_code=500, detail="فشل في إنشاء الحساب")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الخادم: {str(e)}")

# نقطة نهاية للحصول على جميع الحسابات
@auth_app.get("/accounts/", response_model=List[AccountResponse])
async def get_all_accounts():
    """الحصول على جميع الحسابات النشطة"""
    try:
        accounts = db_manager.get_all_accounts()
        return [AccountResponse(**account.to_dict()) for account in accounts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الخادم: {str(e)}")

# نقطة نهاية للحصول على حساب محدد
@auth_app.get("/accounts/{username}", response_model=AccountResponse)
async def get_account(username: str):
    """الحصول على حساب Twitter محدد"""
    try:
        account = db_manager.get_account(username)
        if account:
            return AccountResponse(**account.to_dict())
        else:
            raise HTTPException(status_code=404, detail="الحساب غير موجود")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الخادم: {str(e)}")

# نقطة نهاية لتحديث حساب
@auth_app.put("/accounts/{username}", response_model=AccountResponse)
async def update_account(username: str, update_data: AccountUpdate):
    """تحديث حساب Twitter موجود"""
    try:
        # الحصول على الحساب الحالي
        current_account = db_manager.get_account(username)
        if not current_account:
            raise HTTPException(status_code=404, detail="الحساب غير موجود")
        
        # تحديث الحقول المطلوبة
        if update_data.api_key is not None:
            current_account.api_key = update_data.api_key
        if update_data.api_secret is not None:
            current_account.api_secret = update_data.api_secret
        if update_data.access_token is not None:
            current_account.access_token = update_data.access_token
        if update_data.access_token_secret is not None:
            current_account.access_token_secret = update_data.access_token_secret
        if update_data.bearer_token is not None:
            current_account.bearer_token = update_data.bearer_token
        if update_data.display_name is not None:
            current_account.display_name = update_data.display_name
        
        # حفظ التغييرات
        with db_manager.get_session() as session:
            session.merge(current_account)
            session.commit()
        
        # إعادة الحصول على الحساب المُحدث
        updated_account = db_manager.get_account(username)
        return AccountResponse(**updated_account.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الخادم: {str(e)}")

# نقطة نهاية لحذف حساب
@auth_app.delete("/accounts/{username}")
async def delete_account(username: str):
    """حذف حساب Twitter"""
    try:
        success = db_manager.delete_account(username)
        if success:
            return {"message": f"تم حذف الحساب {username} بنجاح"}
        else:
            raise HTTPException(status_code=404, detail="الحساب غير موجود")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الخادم: {str(e)}")

# نقطة نهاية لإلغاء تفعيل حساب
@auth_app.patch("/accounts/{username}/deactivate")
async def deactivate_account(username: str):
    """إلغاء تفعيل حساب Twitter"""
    try:
        success = db_manager.deactivate_account(username)
        if success:
            return {"message": f"تم إلغاء تفعيل الحساب {username} بنجاح"}
        else:
            raise HTTPException(status_code=404, detail="الحساب غير موجود")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الخادم: {str(e)}")

# نقطة نهاية لاختبار مفاتيح المصادقة
@auth_app.post("/accounts/{username}/test", response_model=TestCredentialsResponse)
async def test_account_credentials(username: str):
    """اختبار صحة مفاتيح المصادقة لحساب Twitter"""
    try:
        is_valid = db_manager.test_credentials(username)
        if is_valid:
            return TestCredentialsResponse(
                username=username,
                is_valid=True,
                message="مفاتيح المصادقة صحيحة"
            )
        else:
            return TestCredentialsResponse(
                username=username,
                is_valid=False,
                message="مفاتيح المصادقة غير صحيحة أو الحساب غير موجود"
            )
    except Exception as e:
        return TestCredentialsResponse(
            username=username,
            is_valid=False,
            message=f"خطأ في اختبار المفاتيح: {str(e)}"
        )

# نقطة نهاية للحصول على معلومات الخادم
@auth_app.get("/info")
async def get_server_info():
    """الحصول على معلومات الخادم"""
    return {
        "message": "Twitter MCP Authentication API",
        "version": "2.0.0",
        "features": [
            "OAuth 2.0 Authentication",
            "Local Database Storage",
            "Web Interface",
            "API Documentation"
        ],
        "endpoints": {
            "home": "GET /",
            "oauth_url": "GET /auth/oauth-url?username={username}",
            "oauth_callback": "GET /auth/callback?code={code}&state={state}",
            "create_account": "POST /accounts/",
            "get_all_accounts": "GET /accounts/",
            "get_account": "GET /accounts/{username}",
            "update_account": "PUT /accounts/{username}",
            "delete_account": "DELETE /accounts/{username}",
            "deactivate_account": "PATCH /accounts/{username}/deactivate",
            "test_credentials": "POST /accounts/{username}/test",
            "api_docs": "GET /docs"
        }
    }

# نقطة نهاية خاصة بـ n8n
@auth_app.get("/n8n/tools")
async def get_n8n_tools():
    """نقطة نهاية خاصة بـ n8n لجلب الأدوات"""
    
    # تنسيق متوافق مع n8n
    return [
        {
            "name": "add_twitter_account",
            "displayName": "إضافة حساب Twitter",
            "description": "إضافة حساب Twitter جديد",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            }
        },
        {
            "name": "list_twitter_accounts", 
            "displayName": "عرض الحسابات",
            "description": "عرض جميع الحسابات المرتبطة",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "test_twitter_account",
            "displayName": "اختبار الحساب",
            "description": "اختبار صحة حساب Twitter",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            }
        },
        {
            "name": "delete_twitter_account",
            "displayName": "حذف الحساب",
            "description": "حذف حساب Twitter",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            }
        },
        {
            "name": "get_help",
            "displayName": "المساعدة",
            "description": "عرض قائمة الأوامر المتاحة",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]

# نقطة نهاية بسيطة جداً لـ n8n
@auth_app.get("/n8n/simple")
async def get_n8n_simple():
    """نقطة نهاية بسيطة جداً لـ n8n"""
    
    return [
        {
            "name": "add_account",
            "description": "إضافة حساب Twitter"
        },
        {
            "name": "list_accounts",
            "description": "عرض الحسابات"
        },
        {
            "name": "test_account",
            "description": "اختبار الحساب"
        },
        {
            "name": "delete_account",
            "description": "حذف الحساب"
        },
        {
            "name": "help",
            "description": "المساعدة"
        }
    ]

# نقطة نهاية متوافقة تماماً مع n8n
@auth_app.get("/n8n/tools-compatible")
async def get_n8n_tools_compatible():
    """نقطة نهاية متوافقة تماماً مع n8n"""
    
    return [
        {
            "name": "add_twitter_account",
            "displayName": "إضافة حساب Twitter",
            "description": "إضافة حساب Twitter جديد",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "execute": {
                "type": "function",
                "function": {
                    "name": "add_twitter_account",
                    "description": "إضافة حساب Twitter جديد",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "اسم المستخدم بدون @"
                            }
                        },
                        "required": ["username"]
                    }
                }
            }
        },
        {
            "name": "list_twitter_accounts", 
            "displayName": "عرض الحسابات",
            "description": "عرض جميع الحسابات المرتبطة",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "execute": {
                "type": "function",
                "function": {
                    "name": "list_twitter_accounts",
                    "description": "عرض جميع الحسابات المرتبطة",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        },
        {
            "name": "test_twitter_account",
            "displayName": "اختبار الحساب",
            "description": "اختبار صحة حساب Twitter",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "execute": {
                "type": "function",
                "function": {
                    "name": "test_twitter_account",
                    "description": "اختبار صحة حساب Twitter",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "اسم المستخدم بدون @"
                            }
                        },
                        "required": ["username"]
                    }
                }
            }
        },
        {
            "name": "delete_twitter_account",
            "displayName": "حذف الحساب",
            "description": "حذف حساب Twitter",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "execute": {
                "type": "function",
                "function": {
                    "name": "delete_twitter_account",
                    "description": "حذف حساب Twitter",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "اسم المستخدم بدون @"
                            }
                        },
                        "required": ["username"]
                    }
                }
            }
        },
        {
            "name": "get_help",
            "displayName": "المساعدة",
            "description": "عرض قائمة الأوامر المتاحة",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "execute": {
                "type": "function",
                "function": {
                    "name": "get_help",
                    "description": "عرض قائمة الأوامر المتاحة",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        }
    ]

# نقطة نهاية بديلة لـ n8n
@auth_app.get("/n8n/tools-alt")
async def get_n8n_tools_alt():
    """نقطة نهاية بديلة لـ n8n"""
    
    return {
        "status": "success",
        "data": [
            {
                "name": "add_twitter_account",
                "displayName": "إضافة حساب Twitter",
                "description": "إضافة حساب Twitter جديد",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "title": "اسم المستخدم",
                            "description": "اسم المستخدم بدون @"
                        }
                    },
                    "required": ["username"]
                }
            },
            {
                "name": "list_twitter_accounts", 
                "displayName": "عرض الحسابات",
                "description": "عرض جميع الحسابات المرتبطة",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "test_twitter_account",
                "displayName": "اختبار الحساب",
                "description": "اختبار صحة حساب Twitter",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "title": "اسم المستخدم",
                            "description": "اسم المستخدم بدون @"
                        }
                    },
                    "required": ["username"]
                }
            },
            {
                "name": "delete_twitter_account",
                "displayName": "حذف الحساب",
                "description": "حذف حساب Twitter",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "title": "اسم المستخدم",
                            "description": "اسم المستخدم بدون @"
                        }
                    },
                    "required": ["username"]
                }
            },
            {
                "name": "get_help",
                "displayName": "المساعدة",
                "description": "عرض قائمة الأوامر المتاحة",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    }

# نقطة نهاية سريعة للأدوات (بدون تحقق)
@auth_app.get("/tools")
async def get_tools_fast():
    """نقطة نهاية سريعة لجلب الأدوات بدون تحقق"""
    
    tools = [
        {
            "name": "add_twitter_account",
            "description": "إضافة حساب Twitter جديد",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "example": "أضف حساب @username"
        },
        {
            "name": "list_twitter_accounts", 
            "description": "عرض جميع الحسابات المرتبطة",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "example": "عرض الحسابات"
        },
        {
            "name": "test_twitter_account",
            "description": "اختبار صحة حساب Twitter",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "example": "اختبر @username"
        },
        {
            "name": "delete_twitter_account",
            "description": "حذف حساب Twitter",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "اسم المستخدم",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "example": "احذف @username"
        },
        {
            "name": "get_help",
            "description": "عرض قائمة الأوامر المتاحة",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "example": "مساعدة"
        }
    ]
    
    return {
        "success": True,
        "tools": tools,
        "count": len(tools),
        "timestamp": time.time(),
        "version": "1.0.0",
        "description": "Twitter MCP Server Tools for AI Agent"
    }

# نقطة نهاية SSE لجلب قائمة الأدوات
@auth_app.get("/ai/tools")
async def get_ai_tools(
    api_key: str = Query(..., description="API Key للتحقق")
):
    """جلب قائمة الأدوات المتاحة للـ AI Agent"""
    
    # التحقق من API Key
    if api_key != os.getenv("API_SECRET_KEY", "default-key"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    tools = [
        {
            "name": "add_twitter_account",
            "description": "إضافة حساب Twitter جديد",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "example": "أضف حساب @username"
        },
        {
            "name": "list_twitter_accounts", 
            "description": "عرض جميع الحسابات المرتبطة",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "example": "عرض الحسابات"
        },
        {
            "name": "test_twitter_account",
            "description": "اختبار صحة حساب Twitter",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "example": "اختبر @username"
        },
        {
            "name": "delete_twitter_account",
            "description": "حذف حساب Twitter",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string", 
                        "description": "اسم المستخدم بدون @"
                    }
                },
                "required": ["username"]
            },
            "example": "احذف @username"
        },
        {
            "name": "get_help",
            "description": "عرض قائمة الأوامر المتاحة",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "example": "مساعدة"
        }
    ]
    
    return {
        "success": True,
        "tools": tools,
        "count": len(tools),
        "timestamp": time.time(),
        "version": "1.0.0",
        "description": "Twitter MCP Server Tools for AI Agent"
    }

# نقطة نهاية SSE للتواصل مع AI Agent
@auth_app.get("/ai/stream")
async def ai_stream(
    request: Request,
    api_key: str = Query(..., description="API Key للتحقق")
):
    """نقطة نهاية SSE للتواصل مع AI Agent في n8n"""
    
    # التحقق من API Key
    if api_key != os.getenv("API_SECRET_KEY", "default-key"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # إنشاء معرف فريد للاتصال
    connection_id = secrets.token_urlsafe(16)
    
    return StreamingResponse(
        sse_manager.event_stream(connection_id, api_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Connection-ID": connection_id
        }
    )

# نقطة نهاية لمعالجة طلبات AI
@auth_app.post("/ai/process")
async def process_ai_request(
    request: Request,
    api_key: str = Query(..., description="API Key للتحقق")
):
    """معالجة طلبات AI من n8n"""
    
    # التحقق من API Key
    if api_key != os.getenv("API_SECRET_KEY", "default-key"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        body = await request.json()
        ai_message = body.get("message", "")
        user_id = body.get("user_id", "unknown")
        
        # معالجة الرسالة
        response = await ai_processor.process_message(ai_message, user_id)
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }

# نقطة نهاية لعرض معلومات الاتصالات النشطة
@auth_app.get("/ai/connections")
async def get_connections(
    api_key: str = Query(..., description="API Key للتحقق")
):
    """عرض معلومات الاتصالات النشطة"""
    
    # التحقق من API Key
    if api_key != os.getenv("API_SECRET_KEY", "default-key"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return sse_manager.get_connection_info()

# نقطة نهاية لإرسال رسالة لجميع الاتصالات
@auth_app.post("/ai/broadcast")
async def broadcast_message(
    request: Request,
    api_key: str = Query(..., description="API Key للتحقق")
):
    """إرسال رسالة لجميع الاتصالات النشطة"""
    
    # التحقق من API Key
    if api_key != os.getenv("API_SECRET_KEY", "default-key"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        body = await request.json()
        message = body.get("message", "")
        message_type = body.get("type", "info")
        
        if not message:
            return {
                "success": False,
                "error": "الرسالة مطلوبة"
            }
        
        # إرسال الرسالة
        sse_manager.broadcast_message({
            "type": message_type,
            "message": message,
            "timestamp": time.time()
        })
        
        return {
            "success": True,
            "message": "تم إرسال الرسالة لجميع الاتصالات النشطة",
            "connections_count": len(sse_manager.active_connections)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def start_auth_server(host: str = "127.0.0.1", port: int = 8000):
    """بدء تشغيل خادم المصادقة"""
    def run_server():
        uvicorn.run(auth_app, host=host, port=port, log_level="info")
    
    # تشغيل الخادم في خيط منفصل
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # انتظار قليل للتأكد من بدء الخادم
    time.sleep(2)
    
    print(f"✅ خادم المصادقة يعمل على http://{host}:{port}")
    print(f"🌐 الصفحة الرئيسية: http://{host}:{port}/")
    print(f"📖 واجهة API: http://{host}:{port}/docs")
    return server_thread

if __name__ == "__main__":
    start_auth_server()
