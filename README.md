# Twitter MCP Server

خادم MCP (Model Context Protocol) لـ Twitter مع دعم OAuth وإدارة حسابات محلية.

## 🚀 التشغيل السريع

### الطريقة 1: تشغيل مباشر (مُوصى به)

```bash
# Terminal 1: تشغيل الخادم الأساسي
python run_server.py

# Terminal 2: تشغيل mcp-proxy
mcp-proxy --host=0.0.0.0 --port=9000 --allow-origin='*' -- python run_server.py
```

### الطريقة 2: تشغيل بسيط

```bash
# تشغيل الخادم الأساسي
python start_server.py
```

## 🌐 نقاط النهاية

### الخادم الأساسي
- **الواجهة الرئيسية**: http://127.0.0.1:8000
- **واجهة API**: http://127.0.0.1:8000/docs
- **إدارة الحسابات**: http://127.0.0.1:8000

### mcp-proxy (لـ n8n)
- **SSE Endpoint**: http://0.0.0.0:9000/sse
- **في n8n**: http://YOUR_IP:9000/sse

## 📋 المميزات

- ✅ **OAuth 1.0a** مع Twitter
- ✅ **قاعدة بيانات محلية** SQLite
- ✅ **واجهة ويب** لإدارة الحسابات
- ✅ **دعم mcp-proxy** للاتصال بـ n8n
- ✅ **أدوات Twitter كاملة** (تغريد، بحث، إدارة المستخدمين)
- ✅ **إدارة متقدمة للحسابات** (إضافة، حذف، اختبار)

## 🛠️ التثبيت

### المتطلبات
```bash
pip install -r requirements.txt
```

### المتطلبات الأساسية
- Python 3.8+
- FastAPI
- SQLAlchemy
- Tweepy
- FastMCP

## 🔧 الإعداد

### 1. إنشاء ملف .env
```bash
cp config.env.example .env
# ثم تعديل المتغيرات
```

### 2. إعداد Twitter API
- احصل على مفاتيح API من [Twitter Developer Portal](https://developer.twitter.com/)
- أضف المفاتيح في ملف `.env`

### 3. تشغيل الخادم
```bash
python run_server.py
```

## 📱 الاستخدام

### إضافة حساب Twitter
1. افتح http://127.0.0.1:8000
2. اضغط "اربط حسابك"
3. اتبع خطوات OAuth

### في n8n
1. أضف MCP Client Tool
2. Endpoint: `http://YOUR_IP:9000/sse`
3. Transport: `SSE`

## 🎯 الأدوات المتاحة

### إدارة الحسابات
- `add_twitter_account` - إضافة حساب جديد
- `list_twitter_accounts` - عرض الحسابات
- `test_twitter_account` - اختبار الحساب
- `remove_twitter_account` - حذف الحساب

### التغريد
- `post_tweet` - نشر تغريدة
- `delete_tweet` - حذف تغريدة
- `create_poll_tweet` - إنشاء استطلاع

### إدارة المستخدمين
- `get_user_profile` - معلومات المستخدم
- `get_user_followers` - المتابعون
- `get_user_following` - المتابَعون

### البحث والجدول الزمني
- `search_twitter` - البحث في Twitter
- `get_timeline` - الجدول الزمني
- `get_trends` - المواضيع الرائجة

## 🔍 استكشاف الأخطاء

### مشاكل شائعة
1. **مفاتيح API غير صحيحة** - تأكد من صحة المفاتيح
2. **مشاكل OAuth** - تأكد من إعدادات Callback URL
3. **مشاكل الاتصال** - تأكد من تشغيل الخادم

### السجلات
- الخادم الأساسي: `mcp_server.log`
- mcp-proxy: في Terminal

## 📄 الترخيص

MIT License - راجع ملف LICENSE للتفاصيل.

## 🤝 المساهمة

نرحب بالمساهمات! يرجى إنشاء Issue أو Pull Request.

## 📞 الدعم

للمساعدة أو الأسئلة، يرجى إنشاء Issue في المستودع.

to run mcp as sse use this command
mcp-proxy --host=0.0.0.0 --port=9000 --allow-origin='*' -- python run_server.
py

can accses it http://ip:port/sse