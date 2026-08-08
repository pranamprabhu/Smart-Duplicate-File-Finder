import os
import sys
import time
import re
from scanner import scan_directory
from utils import format_size, calculate_wasted_space
from report import generate_report
from web_app import app  # Expose Flask WSGI application for deployment (gunicorn app:app)



def clean_path_input(user_input):
    """Cleans user input if they paste terminal commands or quotes."""
    user_input = user_input.strip()
    quoted = re.findall(r'["\']([^"\']+)["\']', user_input)
    if quoted:
        return quoted[0]
    user_input = re.sub(r'^(python\s+[\w\.]+\s+)', '', user_input, flags=re.IGNORECASE)
    return user_input.strip('"').strip("'").strip()


def main():
    print("=" * 50)
    print("        DUPLICATE FILE FINDER (FAST)")
    print("=" * 50)

    if len(sys.argv) > 1:
        folder_path = " ".join(sys.argv[1:])
    else:
        folder_path = input("Enter folder path to scan: ")

    folder_path = clean_path_input(folder_path)

    if not folder_path or not os.path.isdir(folder_path):
        print(f"\n[Error] Invalid directory path: '{folder_path}'")
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
    print("SCAN RESULTS")
    print("=" * 50)
    print(f"Total files scanned: {total_files:,}")
    print(f"Duplicate groups   : {len(duplicates):,}")
    print(f"Scan duration      : {elapsed:.2f} seconds")

    wasted_space = calculate_wasted_space(duplicates)
    print(f"Wasted storage     : {format_size(wasted_space)}")

    if not duplicates:
        print("\n[+] No duplicate files found!")
        return

    print("\nDuplicate Files:")
    print("-" * 50)

    for group_number, (file_hash, file_paths) in enumerate(duplicates.items(), 1):
        print(f"\nGroup {group_number} (MD5: {file_hash})")
        for file_path in file_paths:
            print(f"  -> {file_path}")

    txt_path, json_path = generate_report(duplicates, total_files)
    print("\n" + "=" * 50)
    print("REPORTS GENERATED")
    print("=" * 50)
    print(f"Text Report : {txt_path}")
    print(f"JSON Report : {json_path}")


if __name__ == "__main__":
    main()