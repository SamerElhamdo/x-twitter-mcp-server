# Twitter MCP Server - OAuth 2.0

خادم MCP (Model Context Protocol) لـ Twitter يستخدم OAuth 2.0 مع PKCE للوصول الآمن إلى Twitter API v2.

## ✨ المميزات

- **OAuth 2.0 مع PKCE**: مصادقة آمنة وحديثة
- **Twitter API v2**: استخدام أحدث إصدار من Twitter API
- **إدارة تلقائية للتوكنات**: تجديد access tokens تلقائياً
- **دعم متعدد المستخدمين**: كل مستخدم له سياق منفصل
- **واجهة MCP موحدة**: تكامل سلس مع أدوات AI

## 🚀 التثبيت

### المتطلبات

- Python 3.8+
- حساب Twitter Developer
- تطبيق Twitter مع OAuth 2.0 مفعل

### 1. استنساخ المشروع

```bash
git clone <repository-url>
cd x-twitter-mcp-server
```

### 2. تثبيت التبعيات

```bash
pip install -r requirements.txt
```

### 3. إعداد Twitter Developer App

1. اذهب إلى [Twitter Developer Portal](https://developer.twitter.com/)
2. أنشئ تطبيق جديد أو استخدم موجود
3. فعّل **OAuth 2.0** في إعدادات التطبيق
4. أضف **Callback URL**: `http://localhost:8000/auth/callback`
5. فعّل السكوبات التالية:
   - `tweet.read` - قراءة التغريدات
   - `tweet.write` - كتابة التغريدات
   - `users.read` - قراءة معلومات المستخدمين
   - `like.read` - قراءة الإعجابات
   - `like.write` - كتابة الإعجابات
   - `offline.access` - الوصول بدون اتصال

### 4. إعداد متغيرات البيئة

انسخ `config.env.example` إلى `.env` وقم بتعديل القيم:

```bash
cp config.env.example .env
```

أضف قيم Twitter الخاصة بك:

```env
TWITTER_CLIENT_ID=your_twitter_client_id_here
TWITTER_CLIENT_SECRET=your_twitter_client_secret_here
TWITTER_REDIRECT_URI=http://localhost:8000/auth/callback
```

## 🏃‍♂️ التشغيل

### تشغيل الخادم

#### الطريقة الأولى: استخدام السكريبت المدمج
```bash
python run_server.py
```

#### الطريقة الثانية: استخدام uvicorn مباشرة
```bash
uvicorn src.x_twitter_mcp.server:app --host 0.0.0.0 --port 8000 --reload
```

#### الطريقة الثالثة: استخدام Python module
```bash
python -m src.x_twitter_mcp
```

### الوصول إلى الخادم

- **الخادم**: http://localhost:8000
- **التوثيق**: http://localhost:8000/docs
- **المصادقة**: http://localhost:8000/auth

## 🔐 عملية المصادقة

### 1. بدء المصادقة

```
GET /auth?username=your_username
```

### 2. إعادة التوجيه إلى Twitter

سيتم توجيه المستخدم إلى Twitter للمصادقة

### 3. Callback

بعد المصادقة، سيعود المستخدم إلى:
```
GET /auth/callback?code=authorization_code&state=oauth_state
```

### 4. الحصول على التوكنات

سيتم تبادل authorization code مع access token و refresh token

## 📚 استخدام API

### مثال: الإعجاب بتغريدة

```python
from src.x_twitter_mcp.twitter_client import twitter_helper

# الإعجاب بتغريدة
result = twitter_helper.like_tweet("username", "tweet_id")
if result["success"]:
    print("تم الإعجاب بنجاح!")
else:
    print(f"خطأ: {result['error']}")
```

### مثال: نشر تغريدة

```python
# نشر تغريدة جديدة
result = twitter_helper.post_tweet("username", "مرحباً بالعالم! 🌍")
if result["success"]:
    print(f"تم النشر! Tweet ID: {result['tweet_id']}")
else:
    print(f"خطأ: {result['error']}")
```

### مثال: الحصول على معلومات المستخدم

```python
# معلومات المستخدم
user_info = twitter_helper.get_user_info("username")
if user_info["success"]:
    data = user_info["data"]
    print(f"@{data['username']} - {data['name']}")
    print(f"المتابعون: {data['followers_count']}")
else:
    print(f"خطأ: {user_info['error']}")
```

## 🗄️ قاعدة البيانات

النظام يستخدم SQLite افتراضياً مع دعم PostgreSQL للإنتاج.

### الجداول

- **twitter_accounts**: حسابات Twitter مع OAuth 2.0 tokens
- **user_id**: Twitter User ID الفريد
- **access_token**: توكن الوصول
- **refresh_token**: توكن التجديد
- **expires_at**: تاريخ انتهاء الصلاحية
- **scopes**: الصلاحيات الممنوحة

## 🔄 تجديد التوكنات

النظام يتعامل مع تجديد access tokens تلقائياً:

```python
# تجديد التوكن يدوياً
new_token = oauth_manager.refresh_access_token("username")

# أو الحصول على توكن صالح (مع التجديد التلقائي)
valid_token = oauth_manager.get_valid_access_token("username")
```

## 🛠️ التطوير

### هيكل المشروع

```
src/x_twitter_mcp/
├── __init__.py
├── __main__.py
├── auth_api.py          # واجهات API للمصادقة
├── config.py            # إعدادات التطبيق
├── database.py          # إدارة قاعدة البيانات
├── oauth_manager.py     # مدير OAuth 2.0
├── server.py            # خادم FastAPI الرئيسي
└── twitter_client.py    # دوال مساعدة لـ Twitter API
```

### تشغيل في وضع التطوير

```bash
# تشغيل مع إعادة التحميل التلقائي
python run_server.py --debug --reload

# تشغيل على منفذ مختلف
python run_server.py --port 8080

# تشغيل على عنوان مختلف
python run_server.py --host 0.0.0.0 --port 8000
```

### إضافة ميزات جديدة

1. أضف الدالة في `TwitterClientHelper`
2. استخدم `user_auth=True` للعمليات التي تتطلب سياق المستخدم
3. تأكد من معالجة الأخطاء بشكل صحيح

## 🚨 استكشاف الأخطاء

### مشاكل شائعة

1. **TWITTER_CLIENT_ID غير محدد**
   - تأكد من إعداد `.env` بشكل صحيح

2. **خطأ في Callback URL**
   - تأكد من تطابق URL في Twitter Developer Portal

3. **خطأ في السكوبات**
   - تأكد من تفعيل السكوبات المطلوبة

4. **انتهاء صلاحية التوكن**
   - النظام يجدد التوكنات تلقائياً

### سجلات الأخطاء

راجع console output للتفاصيل:

```bash
python run_server.py --debug
```

## 🐳 Docker (اختياري)

إذا كنت تريد تشغيل الخادم في حاوية Docker:

```bash
# بناء الصورة
docker build -t twitter-mcp-server .

# تشغيل الحاوية
docker run -p 8000:8000 --env-file .env twitter-mcp-server
```

## 📝 الترخيص

هذا المشروع مرخص تحت [MIT License](LICENSE).

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:

1. Fork المشروع
2. إنشاء branch للميزة الجديدة
3. Commit التغييرات
4. Push إلى Branch
5. إنشاء Pull Request

## 📞 الدعم

للدعم أو الأسئلة:

- افتح Issue في GitHub
- راجع التوثيق في `/docs`
- تحقق من Twitter Developer Documentation

---

**ملاحظة**: تأكد من اتباع [Twitter Developer Agreement](https://developer.twitter.com/en/developer-terms/agreement-and-policy) و [Developer Policy](https://developer.twitter.com/en/developer-terms/policy).