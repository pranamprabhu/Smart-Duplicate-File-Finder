import os, hashlib
from collections import defaultdict

def find_duplicates(folder_path):
    sizes, total = defaultdict(list), 0
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d.lower() not in {'$recycle.bin', 'appdata', '__pycache__', 'node_modules', '.git', '.venv'}]
        for file in files:
            path = os.path.join(root, file)
            total += 1
            try:
                s = os.path.getsize(path)
                if s > 0: sizes[s].append(path)
            except Exception: pass

    # Fast 8KB partial hash filter
    partials = defaultdict(list)
    for size, paths in sizes.items():
        if len(paths) > 1:
            for p in paths:
                try:
                    with open(p, 'rb') as f:
                        partials[(size, hashlib.md5(f.read(8192)).hexdigest())].append(p)
                except Exception: pass

    # Full MD5 hash on candidate matches only
    full_hashes = defaultdict(list)
    for paths in partials.values():
        if len(paths) > 1:
            for p in paths:
                try:
                    with open(p, 'rb') as f:
                        full_hashes[hashlib.md5(f.read()).hexdigest()].append(p)
                except Exception: pass

    return total, {h: p for h, p in full_hashes.items() if len(p) > 1}

if __name__ == '__main__':
    target = input("Enter folder path: ").strip().strip('"').strip("'")
    total, duplicates = find_duplicates(target)
    print(f"\nScanned {total} files. Found {len(duplicates)} duplicate group(s).")
    for file_hash, paths in duplicates.items():
        print(f"\nHash: {file_hash}")
        for p in paths:
            print(f"  -> {p}")
