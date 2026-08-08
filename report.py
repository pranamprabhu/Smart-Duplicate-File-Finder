import os
import json
from datetime import datetime
from utils import format_size, calculate_wasted_space


def generate_report(duplicates, total_files, output_dir="reports"):
    """
    Generates and saves scan reports in both TXT and JSON formats.
    Returns:
        txt_path (str): Path to generated text report.
        json_path (str): Path to generated JSON report.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    txt_path = os.path.join(output_dir, f"duplicate_report_{timestamp}.txt")
    json_path = os.path.join(output_dir, f"duplicate_report_{timestamp}.json")

    wasted_bytes = calculate_wasted_space(duplicates)

    # Write human-readable text report
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("          DUPLICATE FILE FINDER - SCAN REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated On : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Files Scanned: {total_files}\n")
        f.write(f"Duplicate Groups   : {len(duplicates)}\n")
        f.write(f"Wasted Storage     : {format_size(wasted_bytes)}\n")
        f.write("-" * 60 + "\n\n")

        for idx, (file_hash, file_paths) in enumerate(duplicates.items(), 1):
            f.write(f"Group {idx} [Hash: {file_hash}]\n")
            for p in file_paths:
                f.write(f"  -> {p}\n")
            f.write("\n")

    # Write structured JSON report
    report_data = {
        "timestamp": timestamp,
        "total_files_scanned": total_files,
        "duplicate_groups_count": len(duplicates),
        "wasted_bytes": wasted_bytes,
        "wasted_formatted": format_size(wasted_bytes),
        "duplicates": duplicates,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4)

    return txt_path, json_path
