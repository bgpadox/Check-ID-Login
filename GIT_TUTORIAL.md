# 📦 Tutorial Push ke Git

## STEP 1: Install Git (jika belum ada)

1. Download: https://git-scm.com/download/win
2. Install dengan default settings
3. Buka **Command Prompt** atau **Git Bash**

---

## STEP 2: Setup Git (pertama kali)

```cmd
git config --global user.name "Nama Anda"
git config --global user.email "email@anda.com"
```

---

## STEP 3: Inisialisasi Git di Project

1. Buka **Command Prompt** atau **Git Bash**
2. Masuk ke folder project:
```cmd
cd C:\Users\USER\Desktop\Mitmproxy\Check ID LOGIN
```

3. Inisialisasi Git:
```cmd
git init
```

---

## STEP 4: Add Files ke Git

```cmd
git add .
```

Ini akan menambahkan semua file (kecuali yang ada di `.gitignore`)

---

## STEP 5: Commit

```cmd
git commit -m "Initial commit - API server dengan load balancing"
```

---

## STEP 6: Buat Repository di GitHub

### 6.1 Buat Akun GitHub (jika belum)
- Daftar di: https://github.com

### 6.2 Buat Repository Baru
1. Login ke GitHub
2. Klik **+** (tanda plus) di pojok kanan atas
3. Pilih **New repository**
4. Isi:
   - **Repository name**: `check-id-login` (atau nama lain)
   - **Description**: `API Server untuk Check ID Login`
   - **Visibility**: Pilih **Private** (lebih aman) atau **Public**
5. **JANGAN** centang "Initialize with README"
6. Klik **Create repository**

### 6.3 Copy URL Repository
Setelah repository dibuat, copy URL-nya:
- Contoh: `https://github.com/username/check-id-login.git`

---

## STEP 7: Push ke GitHub

1. Di Command Prompt, tambahkan remote:
```cmd
git remote add origin https://github.com/username/check-id-login.git
```
*(Ganti `username` dan `check-id-login` dengan yang sesuai)*

2. Push ke GitHub:
```cmd
git branch -M main
git push -u origin main
```

3. Akan diminta login GitHub:
   - Username: username GitHub Anda
   - Password: **Personal Access Token** (bukan password biasa)

---

## STEP 8: Buat Personal Access Token (untuk password)

Jika diminta password saat push:

1. Login ke GitHub
2. Klik profil → **Settings**
3. Scroll ke bawah → **Developer settings**
4. **Personal access tokens** → **Tokens (classic)**
5. **Generate new token (classic)**
6. Isi:
   - **Note**: `Git Push Token`
   - **Expiration**: Pilih durasi (misal: 90 days)
   - **Scopes**: Centang **repo** (semua checkbox di bawah repo)
7. Klik **Generate token**
8. **COPY TOKEN** (hanya muncul sekali!)
9. Gunakan token ini sebagai password saat push

---

## ✅ Selesai!

Repository Anda sudah di GitHub!

**URL Repository**: `https://github.com/username/check-id-login`

---

## 🔄 Update Repository (jika ada perubahan)

Setelah edit file, push lagi:

```cmd
git add .
git commit -m "Update: deskripsi perubahan"
git push
```

---

## 📋 Command Git yang Sering Dipakai

```cmd
# Cek status
git status

# Lihat perubahan
git diff

# Lihat history
git log

# Pull update dari GitHub
git pull

# Clone repository (di komputer lain)
git clone https://github.com/username/check-id-login.git
```

---

## 🆘 Troubleshooting

### Problem: "fatal: not a git repository"
**Solusi:** Pastikan sudah run `git init` di folder project

### Problem: "fatal: could not read Username"
**Solusi:** Gunakan Personal Access Token sebagai password

### Problem: "error: failed to push"
**Solusi:** 
- Pastikan sudah login GitHub
- Cek koneksi internet
- Coba: `git push -u origin main --force` (hati-hati, ini overwrite)

---

**Selamat! Code Anda sudah di GitHub! 🎉**

