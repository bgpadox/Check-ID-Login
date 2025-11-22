# Check ID LOGIN - API Server

## 📁 File Penting

### 🎯 WAJIB DIBACA:
- **`TUTORIAL_DEPLOY.md`** ← Baca ini untuk deploy ke hondastylo.vip
- **`GIT_TUTORIAL.md`** ← Baca ini untuk push ke GitHub

### 📄 File Lainnya:
- **`server.py`** - Flask API server (program utama)
- **`mitm.py`** - Mitmproxy addon (untuk intercept traffic)
- **`requirements.txt`** - Dependencies Python
- **`nginx.conf`** - Konfigurasi Nginx (untuk HTTPS)
- **`install-nginx-service.bat`** - Script install Nginx service
- **`setup-flask-service.bat`** - Script setup Flask service

---

## 🚀 Quick Start

1. **Baca `TUTORIAL_DEPLOY.md`** - Ikuti step-by-step
2. Selesai! API akan online di https://hondastylo.vip

---

## 📦 Push ke Git

**Baca `GIT_TUTORIAL.md`** untuk tutorial lengkap push ke GitHub.

Quick command:
```cmd
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/repo.git
git push -u origin main
```

---

## 📞 API Endpoints

Setelah deploy:
- Login: `https://hondastylo.vip/api/v1/login?userid={userid}&password={password}`
- Status: `https://hondastylo.vip/api/v1/emulators/status`

---

**Punya pertanyaan? Baca `TUTORIAL_DEPLOY.md` bagian Troubleshooting**

