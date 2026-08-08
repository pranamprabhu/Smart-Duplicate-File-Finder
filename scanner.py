import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from hasher import calculate_partial_hash, calculate_file_hash

# Folders to skip for speed and system safety
IGNORED_FOLDERS = {
    "$recycle.bin",
    "system volume information",
    "appdata",
    "__pycache__",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "temp",
    "tmp",
}


def scan_directory(folder_path, progress_callback=None):
    """
    High-speed 3-stage duplicate file scanner:
      Stage 1: Directory walk & size pre-filtering (skips 0-byte & unique size files).
      Stage 2: 8 KB partial hash filter (eliminates 95%+ non-duplicates instantly).
      Stage 3: Parallel full MD5 hashing for candidate matches.

    Returns:
        total_files (int): Total files scanned.
        duplicates (dict): Mapping of MD5 hash -> list of duplicate file paths.
    """
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return 0, {}

    files_by_size = defaultdict(list)
    total_files = 0

    if progress_callback:
        progress_callback("Stage 1/3: Traversing folders & grouping files by size...")

    # Stage 1: Fast directory walk & size grouping
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d.lower() not in IGNORED_FOLDERS]

        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                size = os.path.getsize(file_path)
                if size > 0:
                    files_by_size[size].append(file_path)
                total_files += 1

                # Frequent progress feedback every 200 files
                if progress_callback and total_files % 200 == 0:
                    progress_callback(f"Stage 1: Discovered {total_files:,} files...")
            except (OSError, PermissionError):
                continue

    # Discard size groups with only 1 file
    size_candidates = {
        size: paths for size, paths in files_by_size.items() if len(paths) > 1
    }

    if progress_callback:
        progress_callback(
            f"Stage 1 Complete: {total_files:,} files scanned. "
            f"Found {len(size_candidates):,} potential duplicate size group(s)."
        )

    if not size_candidates:
        return total_files, {}

    # Stage 2: Quick 8 KB partial hashing
    total_size_candidates = sum(len(paths) for paths in size_candidates.values())
    if progress_callback:
        progress_callback(
            f"Stage 2/3: Fast-checking headers for {total_size_candidates:,} files..."
        )

    partial_groups = defaultdict(list)
    checked_count = 0

    for size, paths in size_candidates.items():
        for path in paths:
            p_hash = calculate_partial_hash(path)
            if p_hash:
                partial_groups[(size, p_hash)].append(path)
            checked_count += 1

            if progress_callback and checked_count % 100 == 0:
                progress_callback(
                    f"Stage 2: Header-checked {checked_count:,}/{total_size_candidates:,} files..."
                )

    # Keep candidate lists with > 1 file after partial hash
    candidate_paths_lists = [
        paths for paths in partial_groups.values() if len(paths) > 1
    ]

    candidate_files = [path for paths in candidate_paths_lists for path in paths]

    if progress_callback:
        progress_callback(
            f"Stage 2 Complete: Filtered down to {len(candidate_files):,} candidate files."
        )

    if not candidate_files:
        return total_files, {}

    # Stage 3: Multithreaded full MD5 hashing
    if progress_callback:
        progress_callback(
            f"Stage 3/3: Verifying full MD5 signatures for {len(candidate_files):,} candidate files..."
        )

    full_hash_map = defaultdict(list)

    def hash_worker(path):
        return path, calculate_file_hash(path)

    workers = min(32, (os.cpu_count() or 4) * 4)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(hash_worker, candidate_files)
        for path, f_hash in results:
            if f_hash:
                full_hash_map[f_hash].append(path)

    duplicates = {
        h: paths for h, paths in full_hash_map.items() if len(paths) > 1
    }

    if progress_callback:
        progress_callback(
            f"Stage 3 Complete: Scan finished! Found {len(duplicates):,} duplicate group(s)."
        )

    return total_files, duplicates