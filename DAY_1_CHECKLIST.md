# Day 1: Environment Setup - Checklist

## Overview
**Goal:** Setup complete development environment and verify all components work.
**Estimated Time:** 4-6 hours
**Status:** 🚀 Ready to Start

---

## Phase 1: Verify Prerequisites (30 minutes)

### Hardware Check
- [ ] NVIDIA GPU detected (RTX 5060 or better)
- [ ] 8GB+ VRAM available
- [ ] 16GB+ system RAM
- [ ] 100GB+ free disk space

**Command to verify:**
```cmd
nvidia-smi
wmic computersystem get totalphysicalmemory
wmic logicaldisk get size,freespace,caption
```

### Software Installation
- [ ] Windows 10/11 (21H2 or later)
- [ ] NVIDIA Driver 525+ installed
- [ ] CUDA Toolkit 12.1 installed
- [ ] Python 3.11.x installed
- [ ] Git installed

**Where to download:**
- NVIDIA Driver: https://www.nvidia.com/Download/index.aspx
- CUDA 12.1: https://developer.nvidia.com/cuda-12-1-0-download-archive
- Python 3.11: https://www.python.org/downloads/
- Git: https://git-scm.com/download/win

**Verify installations:**
```cmd
nvidia-smi
nvcc --version
python --version
git --version
```

---

## Phase 2: Setup Project (1 hour)

### 1. Create Project Directory
```cmd
cd C:\Users\<YourUsername>\Documents
mkdir nire
cd nire
```

### 2. Initialize Git Repository
```cmd
git init
git add .
git commit -m "Initial project structure"
```

**Optional:** Connect to GitHub
```cmd
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 3. Copy Files
Download and copy all these files to your project:
- [ ] .gitignore
- [ ] .env.example
- [ ] requirements.txt
- [ ] LICENSE
- [ ] README.md
- [ ] backend/config.py
- [ ] backend/utils/exceptions.py
- [ ] backend/utils/logger.py
- [ ] backend/__init__.py (and all subdirectory __init__.py files)
- [ ] scripts/download_models.py
- [ ] scripts/verify_setup.py

### 4. Create Directory Structure
```cmd
mkdir backend\core backend\memory backend\services backend\adaptive backend\api backend\utils
mkdir frontend\src frontend\src-tauri
mkdir tests docs scripts models data\chroma data\redis data\logs
mkdir installer\assets
```

---

## Phase 3: Python Environment (1.5 hours)

### 1. Create Virtual Environment
```cmd
python -m venv venv
```

### 2. Activate Virtual Environment
```cmd
venv\Scripts\activate
```

**You should see (venv) prefix in your command prompt**

### 3. Upgrade pip
```cmd
python -m pip install --upgrade pip
```

### 4. Install llama-cpp-python with CUDA
```cmd
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

**This may take 5-10 minutes. Watch for any errors.**

**Common Issues:**
- If it fails with "Microsoft Visual C++ 14.0 is required":
  - Download Visual Studio Build Tools
  - Install "Desktop development with C++"
  - Retry installation

### 5. Install Other Dependencies
```cmd
pip install -r requirements.txt
```

**This may take 10-15 minutes.**

### 6. Verify Installation
```cmd
python -c "from llama_cpp import Llama; print('Success!')"
python -c "import fastapi; import chromadb; print('Dependencies OK')"
```

---

## Phase 4: Download Models (1-2 hours)

### 1. Setup HuggingFace (Optional but Recommended)
```cmd
pip install huggingface-hub
```

### 2. Run Download Script
```cmd
python scripts\download_models.py
```

**Expected downloads:**
- Phi-3.5-mini-instruct-q4.gguf (~2.5 GB)
- mistral-7b-instruct-v0.3.Q4_K_M.gguf (~4.5 GB)

**Total time:** 10-30 minutes depending on internet speed

**Alternative: Manual Download**
If script fails, download manually from:
- https://huggingface.co/microsoft/Phi-3.5-mini-instruct-gguf
- https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF

Place files in `models/` directory.

### 3. Verify Models
```cmd
dir models
```

You should see both .gguf files.

---

## Phase 5: Configuration (30 minutes)

### 1. Create .env File
```cmd
copy .env.example .env
```

### 2. Edit .env
Open `.env` in notepad or VS Code:
```cmd
notepad .env
```

**Update these values:**
```env
# Models (should work as-is if downloaded to models/)
LLM_MODEL_PRIMARY=models/Phi-3.5-mini-instruct-q4.gguf
LLM_MODEL_SECONDARY=models/mistral-7b-instruct-v0.3.Q4_K_M.gguf

# Neo4j (you'll set password in Day 2)
NEO4J_PASSWORD=your_secure_password_here

# Everything else can stay as default for now
```

Save and close.

---

## Phase 6: Verification (30 minutes)

### Run Setup Verification Script
```cmd
python scripts\verify_setup.py
```

**Expected output:**
```
============================================================
NIRE Setup Verification
============================================================

--- Python Version ---
Python Version: 3.11.x
✓ Python version OK

--- CUDA/GPU ---
✓ NVIDIA GPU detected
  RTX 5060...

--- Dependencies ---
Checking Python Dependencies:
  ✓ fastapi
  ✓ uvicorn
  ✓ chromadb
  ...

--- llama-cpp-python ---
✓ llama-cpp-python installed

--- Models ---
Checking Models:
  ✓ Phi-3.5-mini-instruct-q4.gguf (2500.5 MB)
  ✓ mistral-7b-instruct-v0.3.Q4_K_M.gguf (4500.2 MB)

--- Environment File ---
✓ .env file exists

============================================================
Summary:
============================================================
✓ PASS: Python Version
✓ PASS: CUDA/GPU
✓ PASS: Dependencies
✓ PASS: llama-cpp-python
✓ PASS: Models
✓ PASS: Environment File

============================================================
✓ All checks passed! You're ready for Day 2.
============================================================
```

---

## Troubleshooting

### Issue: CUDA not found
**Solution:**
1. Verify CUDA installation: `nvcc --version`
2. Check PATH includes: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin`
3. Restart command prompt after PATH changes

### Issue: llama-cpp-python install fails
**Solution 1 - Use prebuilt wheels:**
```cmd
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

**Solution 2 - Build from source:**
```cmd
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
set FORCE_CMAKE=1
pip install llama-cpp-python --no-cache-dir
```

### Issue: Model download timeout
**Solution:**
```cmd
# Set longer timeout
set HF_HUB_DOWNLOAD_TIMEOUT=600

# Retry
python scripts\download_models.py
```

### Issue: Insufficient disk space
**Solution:**
- Free up at least 100GB
- Or install models to different drive:
```cmd
mkdir D:\nire-models
# Update .env to point to D:\nire-models\
```

---

## Success Criteria

You're ready for Day 2 if:
- [ ] All verification checks pass
- [ ] Virtual environment activates successfully
- [ ] Both models downloaded and verified
- [ ] No import errors when running Python scripts
- [ ] GPU visible in nvidia-smi

---

## Next Steps

**Day 2 Preview:**
- Install Neo4j Desktop
- Setup Redis for Windows
- Initialize ChromaDB
- Test database connections

**Estimated time for Day 2:** 3-4 hours

---

## Notes & Tips

### Save Your Work
```cmd
git add .
git commit -m "Day 1 complete - Environment setup"
```

### IDE Setup (Optional)
If using VS Code, install these extensions:
- Python (Microsoft)
- Pylance
- Error Lens
- GitLens

### Performance Tip
Close unnecessary applications before testing:
- Discord, Chrome with many tabs, etc.
- This ensures maximum VRAM available for models

### Backup
Consider backing up:
- `models/` directory (7GB) - in case you need to reinstall
- `.env` file - contains your configuration

---

**Completion Time:** _________  
**Issues Encountered:** _________  
**Notes:** _________

---

✅ **Day 1 Complete!** Take a break, you've earned it! 🎉
