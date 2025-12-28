"""
venv-killer: Find and delete Python virtual environments to free disk space
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core import (
    is_venv,
    is_conda_env,
    get_folder_size,
    format_size,
    parse_size,
    get_folder_age,
    scan_directory_optimized,
)

__all__ = [
    "is_venv",
    "is_conda_env", 
    "get_folder_size",
    "format_size",
    "parse_size",
    "get_folder_age",
    "scan_directory_optimized",
]