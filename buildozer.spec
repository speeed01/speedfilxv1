[app]
title = SpeedFlix
package.name = speedflix
package.domain = org.speedflix

source.dir = .
source.include_exts = py,png,jpg,kv,json

version = 1.5

requirements = python3,kivy,requests

orientation = portrait
fullscreen = 1

icon.filename = icon.png

android.permissions = INTERNET

android.api = 33
android.minapi = 21

# 🔥 لا 36.x نهائيًا
android.build_tools_version = 33.0.2

android.ndk = 25b
android.archs = arm64-v8a

p4a.branch = master

[buildozer]
log_level = 2
