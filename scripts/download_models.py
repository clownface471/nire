"""
Model Download Script
Downloads quantized LLM models from HuggingFace Hub.
"""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download

# Model configurations
MODELS = {
    "phi3": {
        "repo_id": "microsoft/Phi-3.5-mini-instruct-gguf",
        "filename": "Phi-3.5-mini-instruct-q4.gguf",
        "description": "Phi-3.5-mini (3.8B, Q4 quantized) - Primary model"
    },
    "mistral": {
        "repo_id": "TheBloke/Mistral-7B-Instruct-v0.3-GGUF",
        "filename": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
        "description": "Mistral-7B (Q4 quantized) - Secondary model"
    }
}

def download_models():
    """Download both models to models/ directory."""
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("NIRE Model Download Script")
    print("=" * 60)
    print()
    
    for key, config in MODELS.items():
        target_path = models_dir / config["filename"]
        
        if target_path.exists():
            print(f"✓ {config['description']}")
            print(f"  Already downloaded: {target_path}")
            print()
            continue
        
        print(f"Downloading {config['description']}...")
        print(f"  Repo: {config['repo_id']}")
        print(f"  File: {config['filename']}")
        print(f"  Size: ~{get_estimated_size(key)}")
        print()
        
        try:
            downloaded_path = hf_hub_download(
                repo_id=config["repo_id"],
                filename=config["filename"],
                local_dir=str(models_dir),
                local_dir_use_symlinks=False
            )
            
            print(f"✓ Successfully downloaded to {downloaded_path}")
            print()
            
        except Exception as e:
            print(f"✗ Error downloading {key}: {str(e)}")
            print()
    
    print("=" * 60)
    print("Download Complete!")
    print("=" * 60)


def get_estimated_size(model_key: str) -> str:
    """Return estimated download size."""
    sizes = {
        "phi3": "~2.5 GB",
        "mistral": "~4.5 GB"
    }
    return sizes.get(model_key, "Unknown")


if __name__ == "__main__":
    download_models()
