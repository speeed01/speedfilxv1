[app]
title = SpeedFlix
package.name = speedflix
package.domain = org.speedflix

source.dir = .
source.include_exts = py,png,jpg,kv,json

version = 1.3

# ❌ لا libffi
requirements = python3,kivy,requests

orientation = portrait
fullscreen = 1

icon.filename = icon.png

android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 36.0.0

# معماريّة واحدة فقط
android.archs = arm64-v8a

# تثبيت فرع مستقر
p4a.branch = master

[buildozer]
log_level = 2
