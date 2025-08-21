from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from .database import db_manager, TwitterAccount
from .oauth_manager import oauth_manager
import threading
import time
import os

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
    """الصفحة الرئيسية مع روابط المصادقة"""
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Twitter MCP Authentication</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f8fa; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #1da1f2; text-align: center; }
            .auth-section { margin: 20px 0; padding: 20px; border: 1px solid #e1e8ed; border-radius: 5px; }
            .oauth-form { display: flex; gap: 10px; margin: 15px 0; }
            input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
            button { background: #1da1f2; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
            button:hover { background: #1991db; }
            .oauth-url { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; word-break: break-all; }
            .success { color: #28a745; }
            .error { color: #dc3545; }
            .manual-section { margin-top: 30px; }
            .public-oauth { background: #e8f5e8; border-color: #28a745; }
            .public-oauth h3 { color: #28a745; }
            .public-btn { background: #28a745; }
            .public-btn:hover { background: #218838; }
            .feature-box { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .feature-box h4 { margin-top: 0; color: #495057; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐦 Twitter MCP Authentication</h1>
            
            <div class="auth-section public-oauth">
                <h2>🚀 المصادقة السريعة (مُوصى بها)</h2>
                <p><strong>أسهل طريقة لإضافة حساب Twitter:</strong></p>
                <p>اضغط على الزر أدناه وسيتم توجيهك مباشرة إلى Twitter للمصادقة. سيتم استخدام username الخاص بك تلقائياً.</p>
                <a href="/auth/redirect-to-twitter" class="public-btn" style="text-decoration: none; display: inline-block;">🔐 منح الوصول لـ Twitter</a>
                <button onclick="showPublicLink()" style="background: #6c757d; margin-left: 10px;">🔗 مشاركة الرابط</button>
                <button onclick="trySimpleOAuth()" style="background: #ffc107; margin-left: 10px;">⚡ تجربة بدون PKCE</button>
                <div id="publicOAuthResult"></div>
            </div>
            
            <div class="auth-section">
                <h2>🔐 المصادقة مع username محدد</h2>
                <p>إذا كنت تريد تحديد username معين:</p>
                <div class="oauth-form">
                    <input type="text" id="username" placeholder="أدخل اسم المستخدم المطلوب">
                    <button onclick="generateOAuthURL()">إنشاء رابط المصادقة</button>
                </div>
                <div id="oauthResult"></div>
            </div>
            
            <div class="feature-box">
                <h4>✨ المزايا الجديدة:</h4>
                <ul>
                    <li><strong>زر واحد للمصادقة:</strong> اضغط وتمتع!</li>
                    <li><strong>username تلقائي:</strong> من Twitter مباشرة</li>
                    <li><strong>لا حاجة لإدخال بيانات:</strong> كل شيء تلقائي</li>
                    <li><strong>مشاركة سهلة:</strong> يمكن مشاركة الرابط مع أي شخص</li>
                </ul>
            </div>
            
            <div class="manual-section">
                <h2>📝 المصادقة اليدوية</h2>
                <p>إذا كنت تفضل إدخال المفاتيح يدوياً:</p>
                <a href="/docs" target="_blank">
                    <button>فتح واجهة API</button>
                </a>
            </div>
            
            <div class="auth-section">
                <h2>📋 الحسابات المخزنة</h2>
                <button onclick="listAccounts()">عرض الحسابات</button>
                <div id="accountsList"></div>
            </div>
            
            <div class="feature-box">
                <h4>🔗 روابط مفيدة:</h4>
                <p><strong>الرابط العام للمصادقة:</strong> يمكن مشاركته مع أي شخص</p>
                <p><strong>الرابط المباشر:</strong> <a href="/auth/public-oauth" target="_blank">/auth/public-oauth</a></p>
            </div>
        </div>
        
        <script>
            async function trySimpleOAuth() {
                try {
                    const response = await fetch('/auth/simple-oauth');
                    const data = await response.json();
                    
                    if (data.success) {
                        const resultDiv = document.getElementById('publicOAuthResult');
                        resultDiv.innerHTML = `
                            <div class="success">
                                <p>✅ رابط المصادقة البسيط (بدون PKCE):</p>
                                <div class="oauth-url">
                                    <a href="${data.auth_url}" target="_blank">${data.auth_url}</a>
                                </div>
                                <p><strong>💡 هذا الرابط قد يحل مشكلة redirect_after_login</strong></p>
                                <button onclick="window.location.href='${data.auth_url}'" style="background: #28a745; margin-top: 10px;">
                                    🚀 تجربة الآن
                                </button>
                                <button onclick="navigator.clipboard.writeText('${data.auth_url}').then(() => alert('تم نسخ الرابط!'))" style="background: #17a2b8; margin-top: 10px; margin-left: 10px;">
                                    📋 نسخ الرابط
                                </button>
                            </div>
                        `;
                    } else {
                        document.getElementById('publicOAuthResult').innerHTML = `
                            <div class="error">❌ ${data.error}</div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('publicOAuthResult').innerHTML = `
                        <div class="error">❌ خطأ في الاتصال: ${error.message}</div>
                    `;
                }
            }
            
            async function showPublicLink() {
                try {
                    const response = await fetch('/auth/public-oauth');
                    const data = await response.json();
                    
                    if (data.success) {
                        const resultDiv = document.getElementById('publicOAuthResult');
                        resultDiv.innerHTML = `
                            <div class="success">
                                <p>✅ رابط المصادقة العام:</p>
                                <div class="oauth-url">
                                    <a href="${data.auth_url}" target="_blank">${data.auth_url}</a>
                                </div>
                                <p><strong>💡 نصيحة:</strong> يمكنك مشاركة هذا الرابط مع أي شخص!</p>
                                <button onclick="navigator.clipboard.writeText('${data.auth_url}').then(() => alert('تم نسخ الرابط!'))" style="background: #17a2b8; margin-top: 10px;">
                                    📋 نسخ الرابط
                                </button>
                            </div>
                        `;
                    } else {
                        document.getElementById('publicOAuthResult').innerHTML = `
                            <div class="error">❌ ${data.error}</div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('publicOAuthResult').innerHTML = `
                        <div class="error">❌ خطأ في الاتصال: ${error.message}</div>
                    `;
                }
            }
            
            async function redirectToTwitter() {
                try {
                    const response = await fetch('/auth/public-oauth');
                    const data = await response.json();
                    
                    if (data.success) {
                        // التوجيه المباشر إلى Twitter
                        window.location.href = data.auth_url;
                    } else {
                        document.getElementById('publicOAuthResult').innerHTML = `
                            <div class="error">❌ ${data.error}</div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('publicOAuthResult').innerHTML = `
                        <div class="error">❌ خطأ في الاتصال: ${error.message}</div>
                    `;
                }
            }
            
            async function generatePublicOAuth() {
                try {
                    const response = await fetch('/auth/public-oauth');
                    const data = await response.json();
                    
                    if (data.success) {
                        const resultDiv = document.getElementById('publicOAuthResult');
                        resultDiv.innerHTML = `
                            <div class="success">
                                <p>✅ تم إنشاء رابط المصادقة العام بنجاح!</p>
                                <p><strong>الخطوات:</strong></p>
                                <ol>
                                    <li>انقر على الزر أدناه</li>
                                    <li>سجل دخولك إلى Twitter</li>
                                    <li>أوافق على الصلاحيات</li>
                                    <li>سيتم إعادة توجيهك تلقائياً</li>
                                </ol>
                                <div class="oauth-url">
                                    <a href="${data.auth_url}" target="_blank">${data.auth_url}</a>
                                </div>
                                <p><strong>💡 نصيحة:</strong> يمكنك مشاركة هذا الرابط مع أي شخص!</p>
                                <p><small>⚠️ لا تشارك هذا الرابط مع أي شخص غير موثوق</small></p>
                            </div>
                        `;
                    } else {
                        document.getElementById('oauthResult').innerHTML = `
                            <div class="error">❌ ${data.error}</div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('oauthResult').innerHTML = `
                        <div class="error">❌ خطأ في الاتصال: ${error.message}</div>
                    `;
                }
            }
            
            async function generateOAuthURL() {
                const username = document.getElementById('username').value;
                if (!username) {
                    alert('يرجى إدخال اسم المستخدم');
                    return;
                }
                
                try {
                    const response = await fetch(`/auth/oauth-url?username=${encodeURIComponent(username)}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        const resultDiv = document.getElementById('oauthResult');
                        resultDiv.innerHTML = `
                            <div class="success">
                                <p>✅ تم إنشاء رابط المصادقة بنجاح!</p>
                                <p><strong>الخطوات:</strong></p>
                                <ol>
                                    <li>انقر على الزر أدناه</li>
                                    <li>سجل دخولك إلى Twitter</li>
                                    <li>أوافق على الصلاحيات</li>
                                    <li>سيتم إعادة توجيهك تلقائياً</li>
                                </ol>
                                <div class="oauth-url">
                                    <a href="${data.auth_url}" target="_blank">${data.auth_url}</a>
                                </div>
                                <p><small>⚠️ لا تشارك هذا الرابط مع أي شخص</small></p>
                            </div>
                        `;
                    } else {
                        document.getElementById('oauthResult').innerHTML = `
                            <div class="error">❌ ${data.error}</div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('oauthResult').innerHTML = `
                        <div class="error">❌ خطأ في الاتصال: ${error.message}</div>
                    `;
                    }
                }
                
                async function listAccounts() {
                    try {
                        const response = await fetch('/accounts/');
                        const accounts = await response.json();
                        
                        const accountsDiv = document.getElementById('accountsList');
                        if (accounts.length === 0) {
                            accountsDiv.innerHTML = '<p>لا توجد حسابات مخزنة</p>';
                            return;
                        }
                        
                        let html = '<div style="margin-top: 15px;">';
                        accounts.forEach(account => {
                            html += `
                                <div style="border: 1px solid #e1e8ed; padding: 10px; margin: 10px 0; border-radius: 5px;">
                                    <strong>@${account.username}</strong><br>
                                    <small>الاسم: ${account.display_name || 'غير محدد'}</small><br>
                                    <small>تاريخ الإنشاء: ${account.created_at || 'غير محدد'}</small><br>
                                    <small>الحالة: ${account.is_active ? '✅ نشط' : '❌ غير نشط'}</small>
                                </div>
                            `;
                        });
                        html += '</div>';
                        accountsDiv.innerHTML = html;
                    } catch (error) {
                        document.getElementById('accountsList').innerHTML = `
                            <div class="error">❌ خطأ في جلب الحسابات: ${error.message}</div>
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
    code: str = Query(..., description="رمز المصادقة من Twitter"),
    state: str = Query(None, description="حالة OAuth (اختياري)")
):
    """معالجة callback من Twitter OAuth"""
    try:
        if state:
            # استخدام username محدد
            result = oauth_manager.handle_callback(code, state)
        else:
            # استخدام الرابط العام
            result = oauth_manager.handle_public_callback(code)
        
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
