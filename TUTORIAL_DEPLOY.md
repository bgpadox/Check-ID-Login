# 🚀 Tutorial Deploy API ke hondastylo.vip

**File ini adalah SATU-SATUNYA tutorial yang perlu Anda baca!**

---

## 📋 Persiapan

- Domain: **hondastylo.vip** (sudah dibeli)
- RDP Windows dengan akses admin
- Python sudah terinstall

---

## STEP 1: Setup DNS di Hostinger (5 menit)

1. Login ke **Hostinger** → https://hpanel.hostinger.com
2. Pilih domain **hondastylo.vip**
3. Klik **DNS Zone Editor** atau **Advanced DNS**
4. Tambahkan 2 record:

   **Record 1:**
   ```
   Type: A
   Name: @
   Value: [IP RDP Anda]  ← Cek IP di: https://whatismyipaddress.com
   TTL: 3600
   ```

   **Record 2:**
   ```
   Type: A
   Name: www
   Value: [IP RDP Anda]  ← Sama dengan di atas
   TTL: 3600
   ```

5. **Save** dan tunggu 10-30 menit

**Cek DNS sudah aktif:**
```cmd
ping hondastylo.vip
```

---

## STEP 2: Install Nginx (10 menit)

### 2.1 Download & Install
1. Download: https://nginx.org/en/download.html
   - Pilih: **nginx/Windows-1.24.0** (atau versi terbaru)
2. Extract ke: `C:\nginx`
3. Test:
   ```cmd
   cd C:\nginx
   start nginx
   ```
4. Buka browser: http://localhost
   - Jika muncul "Welcome to nginx" = ✅ Berhasil!

### 2.2 Copy Config
1. Copy file `nginx.conf` (dari folder project ini)
2. Paste ke: `C:\nginx\conf\nginx.conf` (replace yang lama)
3. Buat folder SSL:
   ```cmd
   mkdir C:\nginx\conf\ssl
   ```

---

## STEP 3: Generate SSL Certificate (10 menit)

### 3.1 Download Win-ACME
1. Download: https://www.win-acme.com/
2. Extract ke: `C:\win-acme`

### 3.2 Generate Certificate
1. Buka **Command Prompt sebagai Administrator**
2. Run:
   ```cmd
   cd C:\win-acme
   wacs.exe
   ```
3. Ikuti wizard:
   - Tekan **N** (Create certificate with advanced options)
   - Tekan **2** (Manual input)
   - Masukkan: `hondastylo.vip,www.hondastylo.vip`
   - Tekan **2** (Nginx)
   - Masukkan path: `C:\nginx`
   - Tekan **1** (http validation)
   - Win-ACME akan otomatis generate dan install

4. ✅ Selesai! Certificate sudah terinstall

---

## STEP 4: Install Python Dependencies (2 menit)

```cmd
cd C:\Users\USER\Desktop\Mitmproxy\Check ID LOGIN
pip install -r requirements.txt
```

---

## STEP 5: Setup Flask sebagai Service (5 menit)

### 5.1 Download NSSM
1. Download: https://nssm.cc/download
2. Extract ke: `C:\nssm`

### 5.2 Install Service
1. Buka **Command Prompt sebagai Administrator**
2. Run:
   ```cmd
   cd C:\nssm\win64
   nssm install FlaskAPI
   ```
3. Akan muncul window, isi:
   - **Path**: `C:\Python\python.exe` (atau path Python Anda)
   - **Startup directory**: `C:\Users\USER\Desktop\Mitmproxy\Check ID LOGIN`
   - **Arguments**: `server.py`
4. Klik **Install service**
5. Start service:
   ```cmd
   nssm start FlaskAPI
   ```

---

## STEP 6: Setup Nginx sebagai Service (2 menit)

1. Buka **Command Prompt sebagai Administrator**
2. Run file `install-nginx-service.bat` (dari folder project ini)
   - Atau manual:
   ```cmd
   cd C:\nginx
   sc create nginx binPath= "C:\nginx\nginx.exe" start= auto
   sc start nginx
   ```

---

## STEP 7: Buka Firewall (3 menit)

1. Buka **Windows Defender Firewall**
2. Klik **Advanced settings**
3. **Inbound Rules** → **New Rule**

   **Rule 1 - Port 80:**
   - Type: Port
   - Protocol: TCP
   - Port: 80
   - Action: Allow
   - Name: HTTP

   **Rule 2 - Port 443:**
   - Type: Port
   - Protocol: TCP
   - Port: 443
   - Action: Allow
   - Name: HTTPS

---

## STEP 8: Test API (1 menit)

Buka browser dan akses:
```
https://hondastylo.vip/api/v1/emulators/status
```

Jika muncul JSON response = ✅ **BERHASIL!**

---

## ✅ Checklist Final

- [ ] DNS sudah pointing ke IP RDP
- [ ] Nginx sudah install dan running
- [ ] SSL Certificate sudah generate
- [ ] Flask app running sebagai service
- [ ] Nginx running sebagai service
- [ ] Firewall port 80 & 443 terbuka
- [ ] Test API berhasil

---

## 🔗 URL API Anda

Setelah semua selesai, API bisa diakses di:

- **Login**: `https://hondastylo.vip/api/v1/login?userid={userid}&password={password}`
- **Status**: `https://hondastylo.vip/api/v1/emulators/status`

---

## 🆘 Troubleshooting

### Problem: DNS tidak resolve
**Solusi:** Tunggu lebih lama (bisa sampai 24 jam), atau cek di: https://dnschecker.org

### Problem: 502 Bad Gateway
**Solusi:**
```cmd
nssm status FlaskAPI
```
Jika tidak running, start:
```cmd
nssm start FlaskAPI
```

### Problem: SSL Certificate error
**Solusi:** Pastikan port 80 terbuka saat generate certificate

### Problem: Connection refused
**Solusi:** Pastikan firewall port 80 dan 443 sudah dibuka

---

## 📝 Catatan Penting

1. **Backup**: Selalu backup sebelum edit file
2. **Port 5000**: Hanya listen di localhost (aman)
3. **Auto-start**: Service akan auto-start saat RDP restart
4. **SSL Renewal**: Win-ACME akan auto-renewal certificate

---

## 🎉 Selesai!

API Anda sekarang online di **https://hondastylo.vip**!

**Butuh bantuan?** Cek bagian Troubleshooting di atas.

