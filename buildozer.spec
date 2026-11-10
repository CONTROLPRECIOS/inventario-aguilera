[app]

title = Inventario Aguilera
package.name = inventarioaguilera
package.domain = org.aguilera
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET

android.api = 31
android.minapi = 21
android.sdk = 30
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Forzar la versión de python y la rama estable para evitar conflictos de enlaces
p4a.branch = master
requirements.source.python3 = 3.10.11

[buildozer]
log_level = 2
