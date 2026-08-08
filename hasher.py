import hashlib


def calculate_partial_hash(file_path, sample_size=8192):
    """
    Computes MD5 hash of only the first `sample_size` bytes (default 8 KB).
    Ultra-fast for quickly filtering out non-duplicate files of identical size.
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read(sample_size)
        return hashlib.md5(data).hexdigest()
    except (OSError, PermissionError):
        return None


def calculate_file_hash(file_path, chunk_size=65536):
    """
    Generates full MD5 hash for a file by reading in 64 KB chunks.
    Ensures 100% data integrity confirmation without high RAM usage.
    """
    hasher = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


# Aliases for compatibility
calculate_md5 = calculate_file_hash
