# NIRE v0.1 "The Chronicler"

**Neural Intelligence Relational Ecosystem** - A local-first, privacy-focused personal AI agent.

## 🎯 Features

- 🧠 **Persistent Memory:** Hybrid vector + graph storage for long-term context
- 🎭 **Adaptive Personality:** Learns your communication style over time
- 🔒 **100% Local:** Zero cloud dependency, complete privacy
- ⚡ **Low Latency:** Optimized for consumer GPUs (RTX 5060+)
- 🎯 **Multi-Modal UI:** Session, Command, and Ambient interaction modes

## 📋 Prerequisites

**Hardware:**
- NVIDIA GPU with 8GB+ VRAM (tested on RTX 5060)
- 16GB+ system RAM
- 100GB+ free disk space

**Software:**
- Windows 10/11
- NVIDIA Driver 525+ (for CUDA 12.1)
- CUDA Toolkit 12.1
- Python 3.11+
- Node.js 18+ LTS (for frontend, Week 4)

## 🚀 Quick Start (Day 1)

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd nire
```

### Step 2: Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies

**Option A: Install llama-cpp-python with CUDA (Recommended)**

```bash
# Install llama-cpp-python with CUDA support
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# Install other dependencies
pip install -r requirements.txt
```

**Option B: Build from source (if Option A fails)**

```bash
# Install Visual Studio Build Tools first
# Then:
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
set FORCE_CMAKE=1
pip install llama-cpp-python --no-cache-dir

# Install other dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy template
copy .env.example .env

# Edit .env with your settings (use notepad or any editor)
notepad .env
```

**Important:** Set your Neo4j password in `.env` (you'll set this up in Day 2)

### Step 5: Download Models

```bash
python scripts/download_models.py
```

This will download:
- Phi-3.5-mini (~2.5GB)
- Mistral-7B (~4.5GB)

**Total download:** ~7GB (may take 10-30 minutes depending on connection)

### Step 6: Verify Installation

```bash
# Test if llama-cpp-python has CUDA support
python -c "from llama_cpp import Llama; print('✓ llama-cpp-python installed successfully')"

# Check if models were downloaded
dir models
```

Expected output:
```
models/
  ├── Phi-3.5-mini-instruct-q4.gguf
  └── mistral-7b-instruct-v0.3.Q4_K_M.gguf
```

## 📁 Project Structure

```
nire/
├── backend/           # Python backend
│   ├── core/          # LLM engine & logic
│   ├── memory/        # Memory system (Vector + Graph)
│   ├── services/      # Business logic services
│   ├── adaptive/      # Learning algorithms
│   ├── api/           # FastAPI endpoints
│   └── utils/         # Utilities
├── frontend/          # Tauri + React UI (Week 4)
├── models/            # LLM model files (gitignored)
├── data/              # Runtime data (gitignored)
│   ├── chroma/        # Vector database
│   ├── redis/         # Cache
│   └── logs/          # Application logs
├── scripts/           # Automation scripts
├── tests/             # Test suite
└── docs/              # Documentation
```

## 🧪 Testing (End of Day 5)

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_llm_engine.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

## 📚 Development Timeline

- **Week 1 (Days 1-5):** Foundation & LLM Engine
- **Week 2 (Days 6-12):** Memory System (Vector + Graph)
- **Week 3 (Days 13-22):** Intelligence Layer (Adaptive Learning)
- **Week 4 (Days 23-30):** Frontend & Deployment

## 🐛 Troubleshooting

### CUDA not detected
```bash
# Check CUDA installation
nvcc --version

# Check if GPU is visible
nvidia-smi

# Reinstall llama-cpp-python
pip uninstall llama-cpp-python
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### Model download fails
```bash
# Set HuggingFace cache directory (if disk space issue)
set HF_HOME=D:\huggingface_cache

# Re-run download
python scripts/download_models.py
```

### Import errors
```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📖 Documentation

- [Complete Project Plan](docs/PROJECT_PLAN.md)
- [Architecture](docs/ARCHITECTURE.md) (Coming in Week 2)
- [API Reference](docs/API.md) (Coming in Week 3)
- [Memory Schema](docs/MEMORY_SCHEMA.md) (Coming in Week 2)

## 🤝 Contributing

This is currently a solo development project. Contributions will be welcome after v0.1 release.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 📊 Project Status

**Current Phase:** Week 1 - Day 1 ✅  
**Status:** Environment Setup  
**Next Milestone:** LLM Engine Implementation (Day 4-5)

---

**Last Updated:** November 13, 2024  
**Version:** 0.1.0-dev  
**Developer:** [Your Name]
