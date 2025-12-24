import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path

def get_cache_dir():
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        cache_dir = Path(base) / "tunnelify" / "bin"
    elif platform.system() == "Darwin":
        cache_dir = Path.home() / "Library" / "Caches" / "tunnelify" / "bin"
    else:
        base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        cache_dir = Path(base) / "tunnelify" / "bin"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_cloudflared_path():
    is_windows = platform.system() == "Windows"
    filename = "cloudflared.exe" if is_windows else "cloudflared"
    
    system_binary = shutil.which("cloudflared")
    if system_binary:
        return system_binary
    
    cache_dir = get_cache_dir()
    cached_binary = cache_dir / filename
    
    if cached_binary.exists():
        return str(cached_binary)
    
    return None

def download_cloudflared():
    system = platform.system()
    
    if system == "Linux":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        filename = "cloudflared"
    elif system == "Darwin":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
        filename = "cloudflared"
    elif system == "Windows":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        filename = "cloudflared.exe"
    else:
        raise Exception(f"Unsupported platform: {system}")
    
    cache_dir = get_cache_dir()
    dest_path = cache_dir / filename
    
    print(f"Downloading cloudflared for {system}...")
    print(f"This only happens once. Binary will be cached at: {dest_path}")
    
    try:
        import requests
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end="", flush=True)
        
        print("\nDownload complete!")
        
        if system != "Windows":
            os.chmod(dest_path, 0o755)
        
        return str(dest_path)
    
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        raise Exception(f"Failed to download cloudflared: {e}")

def ensure_cloudflared():
    path = get_cloudflared_path()
    if path:
        return path
    
    return download_cloudflared()