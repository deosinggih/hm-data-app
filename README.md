# BA HM Generator - Setup & Running Guide

Aplikasi web untuk manajemen Hour Meter (HM) dan tracking Availability Percentage (PA) untuk equipment rental.

---

## **📋 Prerequisites (Wajib Install)**

Sebelum menjalankan, pastikan sudah install:

### **1. Python 3.9+**
- **Download:** https://www.python.org/downloads/
- **Windows:** Centang "Add Python to PATH" saat install
- **Verify:** `python --version` atau `python3 --version`

### **2. Node.js & npm (LTS)**
- **Download:** https://nodejs.org/
- **Verify:** `node --version` dan `npm --version`

---

## **🚀 Quick Start (3 Steps)**

### **Step 1: Buka Terminal & Navigate ke Project**
```bash
cd /path/to/hm-data-app
```

### **Step 2: Setup Backend (First Time Only)**
```bash
cd backend

# Windows:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Mac/Linux:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Step 3: Setup Frontend (First Time Only)**
```bash
cd ../frontend
npm install
```

---

## **▶️ Running the Application**

### **Option A: Two Separate Terminals (Recommended)**

**Terminal 1 - Backend:**
```bash
cd backend

# Windows:
venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Mac/Linux:
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Then open browser:** `http://127.0.0.1:5173`

---

### **Option B: Single Script (Mac/Linux)**

Create file `start.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 Starting BA HM Generator..."

# Backend
(cd backend && source venv/bin/activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!
sleep 2

# Frontend
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "✅ Backend: http://127.0.0.1:8000/api/health"
echo "✅ Frontend: http://127.0.0.1:5173"
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
```

Then run:
```bash
chmod +x start.sh
./start.sh
```

---

### **Option C: Batch Script (Windows)**

Create file `start.bat`:
```batch
@echo off
cd /d "%~dp0"

echo Starting BA HM Generator...

start cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak
start cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://127.0.0.1:8000/api/health
echo Frontend: http://127.0.0.1:5173
```

Then double-click `start.bat`

---

## **✨ Features**

| Menu | Deskripsi |
|------|-----------|
| **Input DATA HM** | Input data hour meter dari berbagai unit (date, shift, vendor, kode unit, HM, jam kerja, dll) |
| **Tabel DATA HM** | View semua data dengan sorting DATE → CODE UNIT → SHIFT, export ke Excel |
| **Impor STATUS & PO** | Import file Excel untuk status dan PO unit |
| **Summary PA** | Hitung PA% (Availability Percentage) per unit berdasarkan working/breakdown/standby hours |
| **Berita Acara** | Generate formal report dengan signature & configuration |
| **Lampiran** | Export laporan detail dengan format tertentu |

---

## **📊 Data Format (Export Excel)**

Export menghasilkan format:

```
DATE      SHIFT   VENDOR    CODE UNIT         CN    HM START    HM STOP     AMOUNT (HM)
28-Jun    Shift 1 PT HERA   HER-DT-XC-040-001 001   8765.4      08770.9     5.5
28-Jun    Shift 1 PT HERA   HER-DT-XC-040-001 001   08770.9     8775.9      5.0
28-Jun    Shift 2 PT HERA   HER-DT-XC-040-001 001   8775.9      08786.4     10.5
```

**Sorting:** DATE → CODE UNIT → SHIFT → HM START (maintain sequential HM)

---

## **🗄️ Database**

- **Type:** SQLite
- **Location:** `backend/app.db` (auto-created)
- **Reset:** Delete `app.db` and restart app

---

## **🔧 Troubleshooting**

| Problem | Solution |
|---------|----------|
| `Address already in use :8000` | Port terpakai. Ganti: `python -m uvicorn app.main:app --port 8001` |
| `Address already in use :5173` | Port terpakai. Ganti di frontend: `npm run dev -- --port 3000` |
| `command not found: python` | Install Python dari https://www.python.org/downloads/ |
| `command not found: npm` | Install Node.js dari https://nodejs.org/ |
| `Module not found` (Backend) | Run: `pip install -r requirements.txt` |
| `Module not found` (Frontend) | Run: `npm install` |
| `venv not activated` (Mac/Linux) | Run: `source venv/bin/activate` |
| `Permission denied` (Mac/Linux) | Run: `chmod +x start.sh` |

---

## **🎁 Share dengan Teman**

### **Langkah 1: Prepare**
```bash
# Bersihkan temporary files
rm -rf backend/.venv
rm -rf frontend/node_modules
rm -rf frontend/dist
rm backend/app.db
```

### **Langkah 2: Zip Project**
Zip seluruh folder `hm-data-app/`

### **Langkah 3: Share**
Kirim zip file ke teman via email, Google Drive, atau file sharing

### **Langkah 4: Teman Setup**
Teman extract dan ikuti "Quick Start" section di atas

---

## **🛠️ Tech Stack**

- **Backend:** FastAPI + SQLAlchemy + SQLite + pandas + openpyxl
- **Frontend:** React 19 + Vite + TypeScript + React Router
- **Database:** SQLite (portable, no server needed)

---

## **✅ Checklist Sebelum Share**

- [ ] Backend berjalan tanpa error
- [ ] Frontend accessible di `http://127.0.0.1:5173`
- [ ] Bisa input data HM
- [ ] Bisa export ke Excel
- [ ] Hapus `backend/app.db` (database sample)
- [ ] Hapus `backend/.venv` dan `frontend/node_modules` (agar zip size kecil)
- [ ] Create `README.md` ini jelas dipahami

---

**Happy sharing! 🚀**