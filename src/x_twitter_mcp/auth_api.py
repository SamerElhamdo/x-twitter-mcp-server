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
import json
import secrets
import asyncio

# إنشاء تطبيق FastAPI
auth_app = FastAPI(title="Twitter Authentication API", version="1.0.0")

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
                background: linear-gradient(45deg, #6c757d, #5a6268);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 25px;
                cursor: pointer;
                margin-top: 15px;
                font-weight: bold;
                transition: all 0.3s ease;
                box-shadow: 0 5px 15px rgba(108, 117, 125, 0.3);
            }
            .accounts-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(108, 117, 125, 0.4);
            }
            #accountsList {
                margin-top: 20px;
                text-align: right;
            }
            .account-item {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 20px;
                margin: 15px 0;
                border-radius: 15px;
                border-left: 5px solid #1da1f2;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
            }
            .account-item:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            }
            .account-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 15px;
            }
            .account-info {
                flex: 1;
            }
            .account-actions {
                display: flex;
                gap: 10px;
                flex-shrink: 0;
            }
            .action-btn {
                border: none;
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9em;
                font-weight: bold;
                transition: all 0.2s ease;
                min-width: 80px;
            }
            .test-btn {
                background: linear-gradient(45deg, #17a2b8, #138496);
                color: white;
            }
            .tweet-btn {
                background: linear-gradient(45deg, #1da1f2, #1991db);
                color: white;
            }
            .delete-btn {
                background: linear-gradient(45deg, #dc3545, #c82333);
                color: white;
            }
            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .test-result {
                margin-top: 15px;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
            }
            .loading {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .tweet-form {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border: 2px solid #1da1f2;
                border-radius: 15px;
                padding: 20px;
                margin-top: 15px;
                box-shadow: 0 5px 15px rgba(29, 161, 242, 0.2);
            }
            .tweet-input {
                width: 100%;
                min-height: 100px;
                padding: 15px;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                font-size: 1em;
                font-family: inherit;
                resize: vertical;
                margin-bottom: 15px;
                transition: border-color 0.3s ease;
            }
            .tweet-input:focus {
                outline: none;
                border-color: #1da1f2;
                box-shadow: 0 0 0 3px rgba(29, 161, 242, 0.1);
            }
            .tweet-actions {
                display: flex;
                gap: 10px;
                justify-content: space-between;
                align-items: center;
            }
            .tweet-submit {
                background: linear-gradient(45deg, #28a745, #20c997);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 25px;
                cursor: pointer;
                font-weight: bold;
                font-size: 1em;
                transition: all 0.3s ease;
            }
            .tweet-submit:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
            }
            .tweet-submit:disabled {
                background: #6c757d;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            .tweet-cancel {
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9em;
                transition: all 0.3s ease;
            }
            .tweet-cancel:hover {
                background: #5a6268;
                transform: translateY(-1px);
            }
            .char-count {
                color: #6c757d;
                font-size: 0.9em;
                font-weight: bold;
            }
            .char-count.warning {
                color: #ffc107;
            }
            .char-count.danger {
                color: #dc3545;
            }
            .empty-state {
                text-align: center;
                padding: 40px 20px;
                color: #6c757d;
                font-style: italic;
            }
            .stats {
                display: flex;
                justify-content: space-around;
                margin: 20px 0;
                padding: 20px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 15px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.05);
            }
            .stat-item {
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #1da1f2;
            }
            .stat-label {
                color: #6c757d;
                font-size: 0.9em;
                margin-top: 5px;
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
                <div style="display: flex; gap: 15px; justify-content: center; margin-bottom: 20px;">
                    <button onclick="listAccounts()" class="accounts-btn">
                        📋 عرض الحسابات المرتبطة
                    </button>
                    <button onclick="refreshAccounts()" class="accounts-btn" style="background: linear-gradient(45deg, #28a745, #20c997);">
                        🔄 تحديث القائمة
                    </button>
                </div>
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
                        accountsDiv.innerHTML = `
                            <div class="empty-state">
                                <div style="font-size: 4em; margin-bottom: 20px;">🐦</div>
                                <h3 style="color: #6c757d; margin-bottom: 10px;">لا توجد حسابات مرتبطة</h3>
                                <p style="color: #999;">اضغط على "اربط حسابك" أعلاه لإضافة أول حساب Twitter</p>
                            </div>
                        `;
                        return;
                    }
                    
                    // إضافة إحصائيات
                    const activeAccounts = accounts.filter(acc => acc.is_active).length;
                    const totalAccounts = accounts.length;
                    
                    let html = `
                        <div class="stats">
                            <div class="stat-item">
                                <div class="stat-number">${totalAccounts}</div>
                                <div class="stat-label">إجمالي الحسابات</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">${activeAccounts}</div>
                                <div class="stat-label">الحسابات النشطة</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">${totalAccounts - activeAccounts}</div>
                                <div class="stat-label">الحسابات غير النشطة</div>
                            </div>
                        </div>
                    `;
                    
                    accounts.forEach(account => {
                        const statusIcon = account.is_active ? '✅' : '❌';
                        const statusText = account.is_active ? 'نشط' : 'غير نشط';
                        const statusColor = account.is_active ? '#28a745' : '#dc3545';
                        
                        html += `
                            <div class="account-item" id="account-${account.username}">
                                <div class="account-header">
                                    <div class="account-info">
                                        <strong style="font-size: 1.2em; color: #1da1f2;">@${account.username}</strong><br>
                                        <small>الاسم: ${account.display_name || 'غير محدد'}</small><br>
                                        <small>تاريخ الربط: ${account.created_at || 'غير محدد'}</small><br>
                                        <small style="color: ${statusColor};">الحالة: ${statusIcon} ${statusText}</small>
                                    </div>
                                    <div class="account-actions">
                                        <button onclick="testAccount('${account.username}')" class="action-btn test-btn">
                                            🧪 اختبار
                                        </button>
                                        <button onclick="showTweetForm('${account.username}')" class="action-btn tweet-btn">
                                            🐦 تغريد
                                        </button>
                                        <button onclick="deleteAccount('${account.username}')" class="action-btn delete-btn">
                                            🗑️ حذف
                                        </button>
                                    </div>
                                </div>
                                <div id="test-result-${account.username}" class="test-result"></div>
                            </div>
                        `;
                    });
                    
                    accountsDiv.innerHTML = html;
                } catch (error) {
                    document.getElementById('accountsList').innerHTML = `
                        <p style="color: #dc3545; margin-top: 15px;">❌ خطأ في جلب الحسابات: ${error.message}</p>
                    `;
                }
            }
            
            async function testAccount(username) {
                const resultDiv = document.getElementById(`test-result-${username}`);
                resultDiv.innerHTML = '<div class="test-result loading">🔄 جاري الاختبار...</div>';
                
                try {
                    // استخدام الاختبار السريع أولاً
                    const response = await fetch(`/accounts/${username}/quick-test`);
                    const result = await response.json();
                    
                    if (result.success) {
                        resultDiv.innerHTML = `
                            <div class="test-result success">
                                ✅ الحساب يعمل بشكل صحيح<br>
                                <small>الاسم: ${result.name || 'غير محدد'}</small><br>
                                <small>ID: ${result.user_id || 'غير محدد'}</small>
                            </div>
                        `;
                    } else {
                        // إذا فشل الاختبار السريع، جرب الاختبار العادي
                        const testResponse = await fetch(`/accounts/${username}/test`);
                        const testResult = await testResponse.json();
                        
                        if (testResult.is_valid) {
                            resultDiv.innerHTML = '<div class="test-result success">✅ المفاتيح صحيحة - يمكن استخدام الحساب</div>';
                        } else {
                            resultDiv.innerHTML = '<div class="test-result error">❌ المفاتيح غير صحيحة - يرجى تحديثها</div>';
                        }
                    }
                } catch (error) {
                    resultDiv.innerHTML = '<div class="test-result error">❌ خطأ في الاختبار: ' + error.message + '</div>';
                }
            }
            
            async function deleteAccount(username) {
                const confirmMessage = `هل أنت متأكد من حذف الحساب @${username}؟\n\n⚠️ تحذير: هذا الإجراء لا يمكن التراجع عنه!`;
                
                if (!confirm(confirmMessage)) {
                    return;
                }
                
                try {
                    const response = await fetch(`/accounts/${username}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        // إزالة العنصر من الصفحة
                        const accountElement = document.getElementById(`account-${username}`);
                        accountElement.style.animation = 'fadeOut 0.5s ease-out';
                        
                        // عرض رسالة نجاح
                        const successMessage = document.createElement('div');
                        successMessage.innerHTML = '<div class="test-result success">✅ تم حذف الحساب @' + username + ' بنجاح</div>';
                        successMessage.style.marginTop = '10px';
                        accountElement.appendChild(successMessage);
                        
                        setTimeout(() => {
                            accountElement.remove();
                            // إعادة عرض الحسابات المتبقية
                            listAccounts();
                        }, 1500);
                    } else {
                        const errorData = await response.json();
                        alert('❌ فشل في حذف الحساب: ' + (errorData.message || 'خطأ غير معروف'));
                    }
                } catch (error) {
                    alert('❌ خطأ في حذف الحساب: ' + error.message);
                }
            }
            
            // إضافة تأثيرات بصرية
            function addVisualEffects() {
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes fadeOut {
                        from { opacity: 1; transform: translateX(0); }
                        to { opacity: 0; transform: translateX(-20px); }
                    }
                    
                    .account-item {
                        transition: all 0.3s ease;
                    }
                    
                    .account-item:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                    }
                    
                    button {
                        transition: all 0.2s ease;
                    }
                    
                    button:hover {
                        transform: translateY(-1px);
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    }
                    
                    button:active {
                        transform: translateY(0);
                    }
                `;
                document.head.appendChild(style);
            }
            
            // دالة عرض نموذج التغريد
            function showTweetForm(username) {
                // إزالة أي نماذج مفتوحة أخرى
                const existingForms = document.querySelectorAll('.tweet-form');
                existingForms.forEach(form => form.remove());
                
                const accountElement = document.getElementById(`account-${username}`);
                const tweetForm = document.createElement('div');
                tweetForm.className = 'tweet-form';
                tweetForm.innerHTML = `
                    <h4 style="margin: 0 0 15px 0; color: #1da1f2;">🐦 تغريد تجريبي من @${username}</h4>
                    <textarea 
                        class="tweet-input" 
                        placeholder="اكتب نص التغريدة هنا... (الحد الأقصى 280 حرف)"
                        maxlength="280"
                        oninput="updateCharCount(this, ${280 - this.value.length})"
                    ></textarea>
                    <div class="tweet-actions">
                        <div class="char-count" id="char-count-${username}">280 حرف متبقي</div>
                        <div>
                            <button onclick="cancelTweet('${username}')" class="tweet-cancel">❌ إلغاء</button>
                            <button onclick="submitTweet('${username}')" class="tweet-submit">🚀 نشر التغريدة</button>
                        </div>
                    </div>
                `;
                
                // إدراج النموذج بعد معلومات الحساب
                const accountInfo = accountElement.querySelector('.account-info');
                accountInfo.parentNode.insertBefore(tweetForm, accountInfo.nextSibling);
                
                // التركيز على حقل النص
                setTimeout(() => {
                    const textarea = tweetForm.querySelector('.tweet-input');
                    textarea.focus();
                }, 100);
            }
            
            // دالة تحديث عداد الأحرف
            function updateCharCount(textarea, remainingChars) {
                const username = textarea.closest('.account-item').id.replace('account-', '');
                const charCount = document.getElementById(`char-count-${username}`);
                
                charCount.textContent = `${remainingChars} حرف متبقي`;
                charCount.className = 'char-count';
                
                if (remainingChars <= 20) {
                    charCount.classList.add('warning');
                }
                if (remainingChars <= 10) {
                    charCount.classList.add('danger');
                }
            }
            
            // دالة إلغاء التغريد
            function cancelTweet(username) {
                const tweetForm = document.querySelector(`#account-${username} .tweet-form`);
                if (tweetForm) {
                    tweetForm.remove();
                }
            }
            
            // دالة إرسال التغريدة
            async function submitTweet(username) {
                const tweetForm = document.querySelector(`#account-${username} .tweet-form`);
                const textarea = tweetForm.querySelector('.tweet-input');
                const submitBtn = tweetForm.querySelector('.tweet-submit');
                const tweetText = textarea.value.trim();
                
                if (!tweetText) {
                    alert('⚠️ يرجى كتابة نص التغريدة');
                    textarea.focus();
                    return;
                }
                
                if (tweetText.length > 280) {
                    alert('⚠️ نص التغريدة طويل جداً (الحد الأقصى 280 حرف)');
                    return;
                }
                
                // تعطيل الزر وإظهار حالة التحميل
                submitBtn.disabled = true;
                submitBtn.textContent = '🔄 جاري النشر...';
                
                try {
                    // استخدام MCP tool لإنشاء التغريدة
                    const response = await fetch('/mcp/post_tweet', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            text: tweetText,
                            username: username
                        })
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        
                        // إظهار رسالة نجاح
                        const successMessage = document.createElement('div');
                        successMessage.innerHTML = `
                            <div class="test-result success">
                                ✅ تم نشر التغريدة بنجاح!<br>
                                <small>ID: ${result.id || 'غير محدد'}</small>
                            </div>
                        `;
                        successMessage.style.marginTop = '15px';
                        
                        // إزالة النموذج وإظهار رسالة النجاح
                        tweetForm.remove();
                        const accountElement = document.getElementById(`account-${username}`);
                        accountElement.appendChild(successMessage);
                        
                        // إزالة رسالة النجاح بعد 5 ثواني
                        setTimeout(() => {
                            successMessage.remove();
                        }, 5000);
                        
                    } else {
                        const errorData = await response.json();
                        throw new Error(errorData.message || 'خطأ في نشر التغريدة');
                    }
                    
                } catch (error) {
                    // إظهار رسالة خطأ
                    const errorMessage = document.createElement('div');
                    errorMessage.innerHTML = `
                        <div class="test-result error">
                            ❌ فشل في نشر التغريدة: ${error.message}
                        </div>
                    `;
                    errorMessage.style.marginTop = '15px';
                    
                    // إزالة النموذج وإظهار رسالة الخطأ
                    tweetForm.remove();
                    const accountElement = document.getElementById(`account-${username}`);
                    accountElement.appendChild(errorMessage);
                    
                    // إزالة رسالة الخطأ بعد 8 ثواني
                    setTimeout(() => {
                        errorMessage.remove();
                    }, 8000);
                    
                } finally {
                    // إعادة تفعيل الزر
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 نشر التغريدة';
                }
            }
            
            // دالة تحديث الحسابات
            async function refreshAccounts() {
                const accountsDiv = document.getElementById('accountsList');
                accountsDiv.innerHTML = '<div class="empty-state"><div style="font-size: 2em;">🔄</div><p>جاري تحديث القائمة...</p></div>';
                
                // انتظار قليل ثم إعادة عرض الحسابات
                setTimeout(() => {
                    listAccounts();
                }, 1000);
            }
            
            // تشغيل التأثيرات عند تحميل الصفحة
            window.addEventListener('load', addVisualEffects);
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
    code: str = Query(..., description="رمز التفويض من Twitter OAuth 2.0"),
    state: str = Query(None, description="حالة OAuth (اختياري)")
):
    """معالجة callback من Twitter OAuth 2.0"""
    try:
        if state:
            # استخدام username محدد
            result = oauth_manager.handle_callback(state, code)
        else:
            # استخدام الرابط العام (غير مدعوم في OAuth 2.0)
            result = {
                "success": False,
                "error": "OAuth 2.0 يتطلب state parameter. استخدم رابط المصادقة المخصص."
            }
        
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
@auth_app.get("/accounts/{username}/test", response_model=TestCredentialsResponse)
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
            "test_credentials": "GET /accounts/{username}/test",
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
                                "title": "اسم المستخدم",
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

# نقطة نهاية لاختبار الحساب (اختبار سريع)
@auth_app.get("/accounts/{username}/quick-test")
async def quick_test_account(username: str):
    """اختبار سريع للحساب"""
    try:
        # استيراد MCP server
        from .server import initialize_twitter_clients
        
        try:
            # تهيئة عملاء Twitter
            client, v1_api = initialize_twitter_clients(username)
            
            # محاولة الحصول على معلومات المستخدم
            me = client.get_me()
            
            if me.data:
                return {
                    "success": True,
                    "message": "الحساب يعمل بشكل صحيح",
                    "username": username,
                    "user_id": me.data.id,
                    "name": me.data.name,
                    "verified": getattr(me.data, 'verified', False)
                }
            else:
                return {
                    "success": False,
                    "message": "فشل في الحصول على معلومات الحساب",
                    "username": username
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"فشل في اختبار الحساب: {str(e)}",
                "error": str(e),
                "username": username
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"خطأ في معالجة الطلب: {str(e)}",
            "error": str(e)
        }

# نقطة نهاية MCP للتغريد
@auth_app.post("/mcp/post_tweet")
async def mcp_post_tweet(request: Request):
    """نقطة نهاية MCP لإنشاء تغريدة"""
    try:
        body = await request.json()
        text = body.get("text", "")
        username = body.get("username", "")
        
        if not text or not username:
            raise HTTPException(status_code=400, detail="النص واسم المستخدم مطلوبان")
        
        if len(text) > 280:
            raise HTTPException(status_code=400, detail="نص التغريدة طويل جداً (الحد الأقصى 280 حرف)")
        
        # استيراد MCP server
        from .server import initialize_twitter_clients
        
        try:
            # تهيئة عملاء Twitter
            client, v1_api = initialize_twitter_clients(username)
            
            # إنشاء التغريدة
            tweet_data = {"text": text}
            tweet = client.create_tweet(**tweet_data)
            
            # التحقق من وجود البيانات
            if hasattr(tweet, 'data') and tweet.data:
                tweet_id = tweet.data.get("id", "غير محدد")
            else:
                tweet_id = "غير محدد"
            
            return {
                "success": True,
                "message": "تم نشر التغريدة بنجاح",
                "id": tweet_id,
                "text": text,
                "username": username
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"فشل في نشر التغريدة: {str(e)}",
                "error": str(e)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في معالجة الطلب: {str(e)}")

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
