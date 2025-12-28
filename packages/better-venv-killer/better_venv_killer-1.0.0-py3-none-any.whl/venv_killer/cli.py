#!/usr/bin/env python3
"""
CLI interface for venv-killer
"""

import sys
import shutil
import argparse
from pathlib import Path

from .core import (
    scan_directory_optimized,
    format_size,
    parse_size,
)


def main():
    parser = argparse.ArgumentParser(description="Find and delete Python virtual environments.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=[Path.home()],
        help="Paths to scan (default: your home directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--min-size",
        type=str,
        help="Minimum size to consider (e.g., '100MB', '1GB')"
    )
    parser.add_argument(
        "--older-than",
        type=int,
        help="Only consider environments older than N days"
    )
    parser.add_argument(
        "--include-conda",
        action="store_true",
        help="Include Conda environments in search"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum directory depth to scan (default: 10)"
    )
    args = parser.parse_args()

    # Parse min_size if provided
    min_size_bytes = 0
    if args.min_size:
        try:
            min_size_bytes = parse_size(args.min_size)
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)

    search_paths = [Path(p).resolve() for p in args.paths if Path(p).exists()]
    if not search_paths:
        print("❌ No valid paths provided.")
        sys.exit(1)

    env_type_str = "Python virtual environments"
    if args.include_conda:
        env_type_str += " and Conda environments"
    
    print(f"🔍 Scanning for {env_type_str}...")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be deleted")
    
    venvs = []

    for base_path in search_paths:
        print(f"  Scanning {base_path}...")
        try:
            found_venvs = scan_directory_optimized(base_path, args.max_depth, args.include_conda)
            venvs.extend(found_venvs)
        except (OSError, PermissionError) as e:
            print(f"  ⚠️ Skipping {base_path}: {e}")

    # Apply filters
    if min_size_bytes > 0:
        venvs = [(path, size, age, env_type) for path, size, age, env_type in venvs if size >= min_size_bytes]
    
    if args.older_than:
        venvs = [(path, size, age, env_type) for path, size, age, env_type in venvs if age >= args.older_than]

    if not venvs:
        print(f"\n✅ No {env_type_str.lower()} found matching criteria.")
        return

    # Sort by size (largest first)
    venvs.sort(key=lambda x: x[1], reverse=True)

    print(f"\nFound {len(venvs)} environment(s):\n")
    total_size = 0
    for i, (path, size, age, env_type) in enumerate(venvs, 1):
        age_str = f"({age}d old)" if age > 0 else ""
        type_str = f"[{env_type}]" if args.include_conda else ""
        print(f"[{i}] {format_size(size):>8} {type_str:>7} {age_str:>8}  {path}")
        total_size += size

    print(f"\nTotal size: {format_size(total_size)}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - These environments would be deleted.")
        return

    print("\nSelect numbers to delete (e.g., '1 3 5'), or 'all', or press Enter to skip.")
    choice = input(">>> ").strip()

    if not choice:
        print("ℹ️  No changes made.")
        return

    if choice.lower() == "all":
        indices = list(range(len(venvs)))
    else:
        try:
            indices = [int(x) - 1 for x in choice.split() if x.isdigit()]
            indices = [i for i in indices if 0 <= i < len(venvs)]
        except ValueError:
            print("❌ Invalid input.")
            return

    if not indices:
        print("ℹ️  No valid selections.")
        return

    # Show confirmation with total size
    selected_size = sum(venvs[i][1] for i in indices)
    print(f"\n⚠️  About to delete {len(indices)} environment(s) totaling {format_size(selected_size)}")
    confirm = input("Are you sure? (y/N): ").strip().lower()
    
    if confirm not in ['y', 'yes']:
        print("ℹ️  Operation cancelled.")
        return

    total_freed = 0
    for i in sorted(indices, reverse=True):  # Delete from last to avoid index shift
        path, size, age, env_type = venvs[i]
        print(f"🗑️  Deleting {path} ({format_size(size)})")
        try:
            shutil.rmtree(path, ignore_errors=False)
            total_freed += size
        except (OSError, PermissionError) as e:
            print(f"  ❌ Failed: {e}")

    print(f"\n✅ Done! Estimated space freed: {format_size(total_freed)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user.")
        sys.exit(1)