[app]

# عنوان التطبيق
title = SpeedFlix

# اسم الحزمة (يجب أن يكون فريداً)
package.name = speedflix.movies

# اسم المجلد
package.domain = org.speedflix

# رقم إصدار التطبيق
version = 1.0

# رقم الإصدار المطلوب
requirements = python3,kivy==2.2.1,requests,urllib3,ssl,certifi,android

# إصدار Android الأدنى
android.minapi = 21

# إصدار Android المستهدف
android.api = 33

# إصدار Android للبناء
android.ndk = 25b

# الأذونات
android.permissions = INTERNET,WAKE_LOCK,ACCESS_NETWORK_STATE

# السماح بالوصول للإنترنت
android.allow_backup = True

# التوجه
orientation = portrait

# النافذة كاملة
fullscreen = 0

# نقطة الدخول
source.dir = .

# الملف الرئيسي
source.main = main.py

# استبعاد الملفات غير الضرورية
source.exclude_exts = spec,pyc,pyo,git,md,yml,yaml

# رمز التطبيق
app.orientation = portrait

# استخدام AndroidX
android.enable_androidx = True

# بناء لـ arm64 فقط
android.arch = arm64-v8a

# حجم الذاكرة
android.minsdk = 21
android.maxsdk = 33

# خيارات Gradle
android.gradle_dependencies = 'com.android.support:support-v4:28.0.0'

# إخفاء شريط الحالة
android.hide_status_bar = True

# شاشة البداية
presplash.filename = %(source.dir)s/icon.png

# أيقونة التطبيق (تأكد من وجودها)
icon.filename = %(source.dir)s/icon.png

# نوع APK
build_type = debug

# إعدادات الذاكرة
android.accept_sdk_license = true
