"""
Core functionality for venv-killer
"""

import os
import time
from pathlib import Path


def is_venv(folder: Path) -> bool:
    """Check if a folder is a Python virtual environment."""
    if not folder.is_dir():
        return False
    
    # Check for venv markers
    markers = [
        folder / "pyvenv.cfg",
        folder / "Scripts" / "python.exe",  # Windows
        folder / "bin" / "python",          # Unix-like
    ]
    
    # Check primary markers first
    if any(marker.exists() for marker in markers):
        return True
    
    # Check for lib/python* structure (Unix venvs)
    lib_dir = folder / "lib"
    if lib_dir.exists():
        try:
            python_dirs = [d for d in lib_dir.iterdir() if d.is_dir() and d.name.startswith('python')]
            if python_dirs:
                site_packages = any((d / "site-packages").exists() for d in python_dirs)
                if site_packages:
                    return True
        except (OSError, PermissionError):
            pass
    
    return False


def is_conda_env(folder: Path) -> bool:
    """Check if a folder is a Conda environment."""
    if not folder.is_dir():
        return False
    
    # Conda environment markers
    conda_markers = [
        folder / "conda-meta",
        folder / "Scripts" / "conda.exe",   # Windows
        folder / "bin" / "conda",           # Unix-like
    ]
    
    return any(marker.exists() for marker in conda_markers)


def get_folder_size(folder: Path) -> int:
    """Get total size of a folder in bytes."""
    total = 0
    try:
        for entry in folder.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except (OSError, PermissionError):
        pass
    return total


def format_size(bytes_size: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def parse_size(size_str: str) -> int:
    """Parse size string like '100MB' to bytes."""
    if not size_str:
        return 0
    
    size_str = size_str.upper().strip()
    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    
    for unit, multiplier in multipliers.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return int(number * multiplier)
            except ValueError:
                break
    
    # Try parsing as plain number (assume bytes)
    try:
        return int(float(size_str))
    except ValueError:
        raise ValueError(f"Invalid size format: {size_str}")


def get_folder_age(folder: Path) -> int:
    """Get folder age in days since last modification."""
    try:
        mtime = folder.stat().st_mtime
        age_seconds = time.time() - mtime
        return int(age_seconds / 86400)  # Convert to days
    except (OSError, PermissionError):
        return 0


def scan_directory_optimized(base_path: Path, max_depth: int = 10, include_conda: bool = False, progress_callback=None) -> list:
    """Optimized directory scanning with progress callback."""
    venvs = []
    scanned_count = 0
    
    def _scan_recursive(path: Path, current_depth: int = 0):
        nonlocal scanned_count
        if current_depth > max_depth:
            return
        
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    scanned_count += 1
                    if progress_callback and scanned_count % 100 == 0:
                        progress_callback(f"Scanned {scanned_count} items...")
                    
                    if entry.is_dir():
                        entry_path = Path(entry.path)
                        
                        # Check if it's a venv/conda env
                        is_env = False
                        env_type = "venv"
                        
                        if entry.name in {".venv", "venv", "env", ".env"}:
                            if is_venv(entry_path):
                                is_env = True
                        elif include_conda and is_conda_env(entry_path):
                            is_env = True
                            env_type = "conda"
                        
                        if is_env:
                            if progress_callback:
                                progress_callback(f"Found environment: {entry_path}")
                            size = get_folder_size(entry_path)
                            age = get_folder_age(entry_path)
                            venvs.append((entry_path, size, age, env_type))
                        else:
                            # Continue scanning subdirectories
                            _scan_recursive(entry_path, current_depth + 1)
        except (OSError, PermissionError):
            pass
    
    _scan_recursive(base_path)
    return venvs