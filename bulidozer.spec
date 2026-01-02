
[app]
title = SpeedFlix
package.name = speedflix
package.domain = org.speedflix

source.dir = .
source.include_exts = py,png,jpg,kv

version = 1.0

requirements = python3,kivy,requests

orientation = portrait

fullscreen = 1

icon.filename = icon.png

android.permissions = INTERNET

android.api = 33
android.minapi = 21

android.ndk = 25b

android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
