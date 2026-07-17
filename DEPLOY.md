# 🚀 Deployment Guide - Vercel + PythonAnywhere (Free)

Aplikasi akan di-host di:
- **Frontend:** https://your-app.vercel.app (Vercel)
- **Backend:** https://your-username.pythonanywhere.com/api (PythonAnywhere)

---

## **BAGIAN 1: Deploy Backend ke PythonAnywhere (5 menit)**

### **Step 1: Buat Account PythonAnywhere**
1. Buka https://www.pythonanywhere.com/
2. Klik "Sign up for free account"
3. Pilih username Anda (ini akan jadi domain backend)
4. Verifikasi email

### **Step 2: Setup Backend di PythonAnywhere**

1. **Login ke PythonAnywhere dashboard**
   - Klik "Consoles" di top menu
   - Klik "Open bash console"

2. **Clone repository:**
   ```bash
   git clone https://github.com/deosinggih/hm-data-app.git
   cd hm-data-app
   ```

3. **Setup Python virtual environment:**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 hmapp
   cd backend
   pip install -r requirements.txt
   ```

4. **Setup Web App**
   - Di PythonAnywhere, klik "Web" di top menu
   - Klik "+ Add a new web app"
   - Pilih "Manual configuration"
   - Pilih "Python 3.10"
   - Klik "Next"

5. **Configure WSGI File**
   - PythonAnywhere akan buat file di `/home/USERNAME/mysite/wsgi.py`
   - Ganti isinya dengan:
   ```python
   import sys
   path = '/home/USERNAME/hm-data-app/backend'
   if path not in sys.path:
       sys.path.append(path)
   
   from app.main import app as application
   ```
   (Ganti `USERNAME` dengan username PythonAnywhere Anda)

6. **Configure Virtual Environment**
   - Di Web tab, cari "Virtualenv"
   - Enter path: `/home/USERNAME/.virtualenvs/hmapp`

7. **Enable CORS di Backend**
   - Edit `/home/USERNAME/hm-data-app/backend/app/main.py`
   - Tambahkan di bawah import:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app = FastAPI()
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Allow all origins for free tier
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

8. **Reload Web App**
   - Klik tombol "Reload" di Web tab
   - Wait a few seconds
   - Test: buka `https://USERNAME.pythonanywhere.com/api/health`
   - Harus return JSON, jika sukses ✅

---

## **BAGIAN 2: Deploy Frontend ke Vercel (3 menit)**

### **Step 1: Buat Account Vercel**
1. Buka https://vercel.com/signup
2. Klik "Continue with GitHub"
3. Authorize Vercel dengan GitHub Anda

### **Step 2: Deploy di Vercel**
1. Di Vercel dashboard, klik "Add New..." → "Project"
2. Pilih repository `hm-data-app`
3. Pada "Configure project":
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend` (penting!)
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

4. **Set Environment Variable:**
   - Di "Environment Variables", tambahkan:
     - **Name:** `VITE_API_PROXY_TARGET`
     - **Value:** `https://USERNAME.pythonanywhere.com` (ganti USERNAME)
   - Klik "Add"

5. Klik "Deploy"
6. Wait ~3 menit
7. Jika sukses, Anda dapat URL: `https://your-project.vercel.app`

---

## **BAGIAN 3: Testing**

1. Buka frontend: `https://your-project.vercel.app`
2. Test input data HM
3. Test export Excel
4. Jika ada error, check browser console (F12)

---

## **Troubleshooting**

| Problem | Solution |
|---------|----------|
| Backend 404 error | Pastikan PythonAnywhere status "running" (Web tab) |
| CORS error | Pastikan CORS middleware sudah ditambah di `app/main.py` |
| Database not found | PythonAnywhere akan auto-create `app.db` saat pertama kali |
| Frontend not connecting | Check `VITE_API_PROXY_TARGET` env var di Vercel |
| PythonAnywhere module not found | Run `pip install -r requirements.txt` di venv |

---

## **Update Code di Masa Depan**

1. **Local:**
   ```bash
   git add .
   git commit -m "Update: fix something"
   git push origin main
   ```

2. **Vercel:** Auto-deploy when you push to main ✅
3. **PythonAnywhere:** 
   ```bash
   cd ~/hm-data-app
   git pull
   workon hmapp  # activate venv
   pip install -r backend/requirements.txt  # if new dependencies
   ```
   Then reload web app di PythonAnywhere dashboard

---

## **Share Link**

Kirim link ini ke teman: `https://your-project.vercel.app`

Teman bisa langsung pakai tanpa install apa-apa! 🎉
