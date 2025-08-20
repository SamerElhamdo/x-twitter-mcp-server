from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from database import db_manager, TwitterAccount
import threading
import time

# إنشاء تطبيق FastAPI
auth_app = FastAPI(
    title="Twitter MCP Authentication API",
    description="واجهة API لإدارة حسابات Twitter في MCP Server",
    version="1.0.0"
)

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

# نقطة نهاية لإنشاء حساب جديد
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
@auth_app.get("/")
async def root():
    """الصفحة الرئيسية للـ API"""
    return {
        "message": "Twitter MCP Authentication API",
        "version": "1.0.0",
        "endpoints": {
            "create_account": "POST /accounts/",
            "get_all_accounts": "GET /accounts/",
            "get_account": "GET /accounts/{username}",
            "update_account": "PUT /accounts/{username}",
            "delete_account": "DELETE /accounts/{username}",
            "deactivate_account": "PATCH /accounts/{username}/deactivate",
            "test_credentials": "POST /accounts/{username}/test"
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
    return server_thread

if __name__ == "__main__":
    start_auth_server()
