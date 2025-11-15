"""
Setup Verification Script
Checks if all Day 1 prerequisites are met.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verify Python 3.11+ is installed."""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 11:
        print("✓ Python version OK")
        return True
    else:
        print("✗ Python 3.11+ required")
        return False


def check_cuda():
    """Check if CUDA is available."""
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ NVIDIA GPU detected")
            # Parse GPU info
            for line in result.stdout.split('\n'):
                if 'RTX' in line or 'GeForce' in line:
                    print(f"  {line.strip()}")
            return True
        else:
            print("✗ nvidia-smi failed")
            return False
            
    except FileNotFoundError:
        print("✗ nvidia-smi not found (CUDA not installed?)")
        return False
    except Exception as e:
        print(f"✗ Error checking CUDA: {str(e)}")
        return False


def check_dependencies():
    """Check if key Python packages are installed."""
    packages = [
        "fastapi",
        "uvicorn",
        "chromadb",
        "neo4j",
        "redis",
        "pydantic",
        "structlog"
    ]
    
    print("\nChecking Python Dependencies:")
    all_ok = True
    
    for package in packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} not installed")
            all_ok = False
    
    return all_ok


def check_llama_cpp():
    """Check if llama-cpp-python with CUDA is installed."""
    try:
        from llama_cpp import Llama
        print("✓ llama-cpp-python installed")
        
        # Try to check if CUDA is enabled (this may not work for all versions)
        print("  (Note: CUDA support will be verified when loading models)")
        return True
        
    except ImportError:
        print("✗ llama-cpp-python not installed")
        print("  Install with: pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121")
        return False


def check_models():
    """Check if models are downloaded."""
    models_dir = Path("models")
    expected_models = [
        "Phi-3.5-mini-instruct-q4.gguf",
        "mistral-7b-instruct-v0.3.Q4_K_M.gguf"
    ]
    
    print("\nChecking Models:")
    all_ok = True
    
    if not models_dir.exists():
        print("✗ models/ directory not found")
        return False
    
    for model_name in expected_models:
        model_path = models_dir / model_name
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ {model_name} ({size_mb:.1f} MB)")
        else:
            print(f"  ✗ {model_name} not found")
            all_ok = False
    
    if not all_ok:
        print("\n  Download models with: python scripts/download_models.py")
    
    return all_ok


def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✓ .env file exists")
        return True
    else:
        print("✗ .env file not found")
        print("  Copy .env.example to .env and configure it")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("NIRE Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("CUDA/GPU", check_cuda),
        ("Dependencies", check_dependencies),
        ("llama-cpp-python", check_llama_cpp),
        ("Models", check_models),
        ("Environment File", check_env_file),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✓ All checks passed! You're ready for Day 2.")
        print("=" * 60)
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
