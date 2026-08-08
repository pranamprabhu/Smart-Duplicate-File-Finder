import os
import sys
import time
import re
from scanner import scan_directory
from utils import format_size, calculate_wasted_space
from report import generate_report


def clean_path_input(user_input):
    """Cleans user input if they paste terminal commands or quotes."""
    user_input = user_input.strip()
    quoted = re.findall(r'["\']([^"\']+)["\']', user_input)
    if quoted:
        return quoted[0]
    user_input = re.sub(r'^(python\s+[\w\.]+\s+)', '', user_input, flags=re.IGNORECASE)
    return user_input.strip('"').strip("'").strip()


def delete_duplicates(duplicates):
    """Safely deletes duplicate copies while retaining 1 original file per group."""
    deleted_count = 0
    freed_bytes = 0

    print("\n" + "=" * 50)
    print("CLEANUP DUPLICATES")
    print("=" * 50)

    confirm = input("Are you sure you want to delete duplicate files? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("Cleanup cancelled.")
        return

    for group_num, (file_hash, file_paths) in enumerate(duplicates.items(), 1):
        original = file_paths[0]
        copies = file_paths[1:]
        print(f"\nGroup {group_num}: Keeping original -> {original}")

        for copy_path in copies:
            try:
                size = os.path.getsize(copy_path)
                os.remove(copy_path)
                deleted_count += 1
                freed_bytes += size
                print(f"  [DELETED] {copy_path}")
            except (OSError, PermissionError) as e:
                print(f"  [FAILED] Could not delete {copy_path}: {e}")

    print("\n" + "=" * 50)
    print(f"CLEANUP COMPLETE: Removed {deleted_count} duplicate file(s), freed {format_size(freed_bytes)}.")
    print("=" * 50)


def main():
    print("=" * 50)
    print("        DUPLICATE FILE FINDER & CLEANER")
    print("=" * 50)

    if len(sys.argv) > 1:
        folder_path = " ".join(sys.argv[1:])
    else:
        folder_path = input("Enter target folder path: ")

    folder_path = clean_path_input(folder_path)

    if not folder_path or not os.path.isdir(folder_path):
        print(f"\n[Error] Directory '{folder_path}' does not exist.")
        return

    print(f"\n[+] Scanning directory: {folder_path}\n")

    start_time = time.time()
    try:
        total_files, duplicates = scan_directory(
            folder_path, progress_callback=lambda msg: print(f"  {msg}")
        )
    except KeyboardInterrupt:
        print("\n\n[!] Scan cancelled by user.")
        return

    elapsed = time.time() - start_time

    print("\n" + "=" * 50)
    print("SCAN SUMMARY")
    print("=" * 50)
    print(f"Total files scanned : {total_files:,}")
    print(f"Duplicate groups    : {len(duplicates):,}")
    print(f"Scan duration       : {elapsed:.2f} seconds")
    wasted = calculate_wasted_space(duplicates)
    print(f"Wasted storage space: {format_size(wasted)}")

    if not duplicates:
        print("\n[+] No duplicate files found!")
        return

    print("\nDuplicate Groups:")
    print("-" * 50)
    for group_num, (file_hash, paths) in enumerate(duplicates.items(), 1):
        print(f"\n[Group {group_num}] Hash: {file_hash}")
        for p in paths:
            print(f"  -> {p}")

    txt_path, json_path = generate_report(duplicates, total_files)
    print(f"\n[+] Reports generated:\n    - {txt_path}\n    - {json_path}")

    print("\nActions:")
    print("1. Keep files (Exit)")
    print("2. Delete duplicate files (Keep 1 original per group)")
    choice = input("Select an option (1/2): ").strip()

    if choice == "2":
        delete_duplicates(duplicates)
    else:
        print("Exiting without deleting any files.")


if __name__ == "__main__":
    main()