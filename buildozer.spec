[app]
title = SpeedFlix
package.name = speedflix
package.domain = org.speedflix

source.dir = .
source.include_exts = py,png,jpg,kv,json

version = 1.1

requirements = python3,kivy,requests,libffi

orientation = portrait
fullscreen = 1

icon.filename = icon.png

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 36.0.0

android.archs = arm64-v8a,armeabi-v7a

# 🔑 إجبار python-for-android الحديث
p4a.branch = master

[buildozer]
log_level = 2
