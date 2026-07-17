# Installation Guide - BA HM Generator

Panduan lengkap untuk install dan jalankan aplikasi di komputer baru.

---

## **Prerequisites Check**

Sebelum mulai, pastikan Anda punya:

### **1. Python 3.9 atau lebih baru**

**Windows:**
1. Download dari https://www.python.org/downloads/
2. Buka installer
3. ✅ **PENTING**: Centang "Add Python to PATH"
4. Click "Install Now"
5. Verify: Buka Command Prompt, ketik: `python --version`

**Mac:**
```bash
# Gunakan Homebrew (recommended)
brew install python3
python3 --version
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
python3 --version
```

### **2. Node.js & npm (LTS version)**

1. Download dari https://nodejs.org/
2. Install (next → next → finish)
3. Verify di terminal: `node --version` dan `npm --version`

---

## **Installation Steps**

### **Step 1: Extract Project**

Extract file `hm-data-app.zip` ke folder yang Anda inginkan, misal:
- **Windows:** `C:\Users\YourName\hm-data-app`
- **Mac/Linux:** `~/hm-data-app`

### **Step 2: Open Terminal/Command Prompt**

Navigate ke project folder:

**Windows (Command Prompt):**
```bash
cd C:\Users\YourName\hm-data-app
```

**Mac/Linux (Terminal):**
```bash
cd ~/hm-data-app
```

### **Step 3: Setup Backend**

```bash
# Enter backend folder
cd backend

# Create virtual environment
python -m venv venv              # Windows
python3 -m venv venv            # Mac/Linux

# Activate virtual environment
venv\Scripts\activate            # Windows
source venv/bin/activate        # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

After this, you should see `(venv)` prefix in terminal.

### **Step 4: Setup Frontend**

Open NEW terminal window, navigate to project, then:

```bash
# Enter frontend folder
cd frontend

# Install dependencies
npm install

# This will take 2-3 minutes...
```

---

## **Running the Application**

### **First Time Running**

You need **2 open terminals/windows**:

**Terminal 1 - Backend (stays open):**
```bash
cd backend

# Activate venv
venv\Scripts\activate            # Windows
source venv/bin/activate        # Mac/Linux

# Start backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 - Frontend (stays open):**
```bash
cd frontend

# Start frontend dev server
npm run dev

# You should see:
# Local:   http://127.0.0.1:5173/
```

### **Open in Browser**

Go to: **http://127.0.0.1:5173**

---

## **Automatic Start (Optional)**

### **Mac/Linux Users:**

```bash
# Make script executable (one time only)
chmod +x start.sh

# Run:
./start.sh

# Both servers start automatically!
```

### **Windows Users:**

Just double-click `start.bat` file. Both servers start automatically!

---

## **Verify It Works**

1. ✅ Frontend loads at http://127.0.0.1:5173
2. ✅ Dropdown "Vendor" shows values (PT HERA, etc)
3. ✅ Can input data and submit
4. ✅ Can navigate between menus

---

## **Common Issues & Solutions**

### **Issue: "Python not found"**
```bash
# Solution: Make sure Python is in PATH
# Reinstall Python and check "Add Python to PATH"
# Or use full path: C:\Python39\python.exe --version
```

### **Issue: "npm not found"**
```bash
# Solution: Reinstall Node.js from https://nodejs.org/
node --version  # Verify after install
```

### **Issue: "Port 8000 already in use"**
```bash
# Either:
# 1. Close other apps using port 8000
# 2. Or use different port:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### **Issue: "Port 5173 already in use"**
```bash
cd frontend
npm run dev -- --port 3000  # Use port 3000 instead
```

### **Issue: "venv not activated"** (Mac/Linux)
```bash
# You forgot to activate venv
cd backend
source venv/bin/activate    # Run this first!
```

### **Issue: Frontend shows blank page**
```bash
# Backend might not be running
# Check:
curl http://127.0.0.1:8000/api/health

# If error, start backend first
# Then refresh browser
```

### **Issue: "Module not found" error**
```bash
# Backend:
cd backend
pip install -r requirements.txt

# Frontend:
cd frontend
npm install
```

---

## **Stop the Application**

To stop servers:

1. **Terminal 1 (Backend):** Press `Ctrl + C`
2. **Terminal 2 (Frontend):** Press `Ctrl + C`

Or close the terminal windows.

---

## **Next Time (After First Install)**

You don't need to repeat steps 2-4. Just run:

**Terminal 1:**
```bash
cd backend
source venv/bin/activate        # Activate venv
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2:**
```bash
cd frontend
npm run dev
```

Or use the automatic script:
```bash
# Mac/Linux:
./start.sh

# Windows:
start.bat  # Just double-click
```

---

## **Update Dependencies (Rarely Needed)**

```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm update
```

---

## **Uninstall**

Just delete the `hm-data-app` folder. Everything is local (no system changes).

---

## **Need Help?**

Check the README.md file for troubleshooting and features.

**Happy using BA HM Generator! 🚀**
