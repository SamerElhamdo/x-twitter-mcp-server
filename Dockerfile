# Twitter MCP Server - OAuth 2.0
# Docker image for running the Twitter MCP server

FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# تحديث النظام وتثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المتطلبات
COPY requirements.txt .

# تثبيت Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود التطبيق
COPY . .

# فتح المنفذ
EXPOSE 8000

# تشغيل التطبيق
CMD ["python", "run_server.py", "--host", "0.0.0.0", "--port", "8000"]
