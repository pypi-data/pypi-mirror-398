"""
Model download utilities
Handles automatic model weight downloading from GitHub Releases
"""

import os
import urllib.request
import urllib.error
from pathlib import Path
from tqdm import tqdm


def get_cache_dir():
    """Get cache directory for model weights"""
    if os.name == 'nt':  # Windows
        cache_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'neuro_deblur' / 'weights'
    else:  # Linux/Mac
        cache_dir = Path.home() / '.cache' / 'neuro_deblur' / 'weights'
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_with_progress(url, output_path):
    """Download file with progress bar"""
    try:
        print(f"Downloading model weights from GitHub...")
        print(f"Source: {url}")
        
        # Get file size
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get('content-length', 0))
        
        # Download with progress bar
        with tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading') as pbar:
            def reporthook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                pbar.update(downloaded - pbar.n)
            
            urllib.request.urlretrieve(url, output_path, reporthook=reporthook)
        
        print(f"✓ Model downloaded successfully!")
        print(f"✓ Saved to: {output_path}")
        return True
        
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"\n❌ Error: Model file not found on GitHub Releases.")
            print(f"Please make sure you've created a release with the model file.")
            print(f"Expected URL: {url}")
        else:
            print(f"\n❌ HTTP Error {e.code}: {e.reason}")
        return False
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False


def get_model_path(model_name='best_model.pth'):
    """
    Get model path, downloading if necessary
    
    Args:
        model_name: Name of the model file
        
    Returns:
        Path to model file
    """
    # GitHub Release URL
    GITHUB_USER = "Parshva2605"
    GITHUB_REPO = "neuro-deblur"
    VERSION = "v0.1.1"
    MODEL_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/download/{VERSION}/{model_name}"
    
    # Check cache first
    cache_dir = get_cache_dir()
    model_path = cache_dir / model_name
    
    if model_path.exists():
        print(f"✓ Using cached model: {model_path}")
        return model_path
    
    # Download model
    print(f"\nModel not found in cache. Downloading from GitHub Releases...")
    print(f"This is a one-time download (~334 MB)")
    print("-" * 60)
    
    success = download_with_progress(MODEL_URL, model_path)
    
    if not success:
        raise RuntimeError(
            f"Failed to download model weights.\n"
            f"Please download manually from:\n"
            f"{MODEL_URL}\n"
            f"And place it at: {model_path}"
        )
    
    return model_path
