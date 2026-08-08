"""
Duplicate File Finder - Flask Web Dashboard
A stunning light-themed web interface for scanning and managing duplicate files.
"""
import os
import json
import time
import threading
from collections import defaultdict
from flask import Flask, render_template, request, jsonify
from scanner import scan_directory
from utils import format_size, calculate_wasted_space

app = Flask(__name__)

# Global scan state for progress tracking
scan_state = {
    "is_scanning": False,
    "progress_messages": [],
    "results": None,
    "error": None,
    "start_time": None,
    "elapsed": None,
}


def reset_scan_state():
    scan_state["is_scanning"] = False
    scan_state["progress_messages"] = []
    scan_state["results"] = None
    scan_state["error"] = None
    scan_state["start_time"] = None
    scan_state["elapsed"] = None


def progress_callback(message):
    scan_state["progress_messages"].append(message)


def create_sample_demo_folder():
    """Creates a sample demo directory with duplicate files for live web testing."""
    sample_dir = os.path.abspath("sample_demo")
    os.makedirs(os.path.join(sample_dir, "documents"), exist_ok=True)
    os.makedirs(os.path.join(sample_dir, "backup"), exist_ok=True)
    os.makedirs(os.path.join(sample_dir, "images"), exist_ok=True)

    # Sample duplicate 1 (Text document copies)
    content1 = b"Smart Duplicate File Finder Demo File Content - 2026\n" * 100
    with open(os.path.join(sample_dir, "documents", "project_report.txt"), "wb") as f:
        f.write(content1)
    with open(os.path.join(sample_dir, "backup", "project_report_copy.txt"), "wb") as f:
        f.write(content1)

    # Sample duplicate 2 (Media file copies)
    content2 = b"Binary sample data for image hash test\x00\xFF\xAA\xBB" * 600
    with open(os.path.join(sample_dir, "images", "wallpaper.jpg"), "wb") as f:
        f.write(content2)
    with open(os.path.join(sample_dir, "backup", "wallpaper_backup.jpg"), "wb") as f:
        f.write(content2)

    # Unique file
    with open(os.path.join(sample_dir, "documents", "readme_unique.txt"), "wb") as f:
        f.write(b"Unique content that has no duplicate.")

    return sample_dir


def run_scan(folder_path, display_name=None):
    """Background thread function to run the scan."""
    try:
        scan_state["start_time"] = time.time()
        
        # Check if directory exists
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            total_files = 0
            duplicates = {}
            if progress_callback:
                progress_callback(
                    f"Notice: Path '{folder_path}' does not exist on this server. "
                    "Use the 'Select Folder from PC' button to pick any folder directly from your computer!"
                )
        else:
            total_files, duplicates = scan_directory(folder_path, progress_callback)

        elapsed = time.time() - scan_state["start_time"]
        scan_state["elapsed"] = round(elapsed, 2)

        wasted = calculate_wasted_space(duplicates)

        groups = []
        for idx, (file_hash, paths) in enumerate(duplicates.items(), 1):
            file_size = 0
            try:
                file_size = os.path.getsize(paths[0])
            except OSError:
                pass

            file_details = []
            for p in paths:
                fname = os.path.basename(p)
                ext = os.path.splitext(fname)[1].lower()
                file_details.append({
                    "path": p,
                    "name": fname,
                    "extension": ext if ext else "(none)",
                    "directory": os.path.dirname(p),
                })

            groups.append({
                "group_id": idx,
                "hash": file_hash,
                "count": len(paths),
                "file_size": file_size,
                "file_size_formatted": format_size(file_size),
                "wasted": file_size * (len(paths) - 1),
                "wasted_formatted": format_size(file_size * (len(paths) - 1)),
                "files": file_details,
            })

        groups.sort(key=lambda g: g["wasted"], reverse=True)

        ext_counts = {}
        ext_sizes = {}
        for g in groups:
            for f in g["files"][1:]:
                ext = f["extension"]
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
                ext_sizes[ext] = ext_sizes.get(ext, 0) + g["file_size"]

        type_distribution = [
            {"type": ext, "count": ext_counts[ext], "size": format_size(ext_sizes[ext])}
            for ext in sorted(ext_counts, key=lambda e: ext_counts[e], reverse=True)
        ]

        scan_state["results"] = {
            "total_files": total_files,
            "duplicate_groups": len(duplicates),
            "total_duplicates": sum(len(p) - 1 for p in duplicates.values()),
            "wasted_bytes": wasted,
            "wasted_formatted": format_size(wasted),
            "elapsed": scan_state["elapsed"],
            "folder_path": display_name or folder_path,
            "groups": groups,
            "type_distribution": type_distribution,
        }
    except Exception as e:
        scan_state["error"] = str(e)
    finally:
        scan_state["is_scanning"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def start_scan():
    data = request.get_json() or {}
    user_input = data.get("folder_path", "").strip().strip('"').strip("'")

    if scan_state["is_scanning"]:
        return jsonify({"error": "A scan is already in progress."}), 409

    reset_scan_state()
    scan_state["is_scanning"] = True

    if not user_input or user_input.lower() in ["sample", "demo"]:
        target_path = create_sample_demo_folder()
        display_name = "sample_demo (Server Demo Files)"
    else:
        target_path = user_input
        display_name = user_input

    thread = threading.Thread(target=run_scan, args=(target_path, display_name), daemon=True)
    thread.start()

    return jsonify({"status": "started", "folder_path": display_name})


@app.route("/api/scan_client_files", methods=["POST"])
def scan_client_files():
    """Processes browser folder picker files hashed client-side."""
    data = request.get_json() or {}
    files_list = data.get("files", [])
    folder_name = data.get("folder_name", "Selected PC Folder")

    if not files_list:
        return jsonify({"error": "No files selected."}), 400

    start_time = time.time()
    reset_scan_state()

    # Group files by MD5 hash
    hash_map = defaultdict(list)
    total_files = len(files_list)

    for item in files_list:
        f_hash = item.get("hash")
        f_path = item.get("path") or item.get("name")
        f_size = item.get("size", 0)
        if f_hash:
            hash_map[f_hash].append({"path": f_path, "name": item.get("name"), "size": f_size})

    duplicates = {h: items for h, items in hash_map.items() if len(items) > 1}
    wasted = sum(items[0]["size"] * (len(items) - 1) for items in duplicates.values())

    groups = []
    for idx, (f_hash, items) in enumerate(duplicates.items(), 1):
        f_size = items[0]["size"]
        file_details = []
        for it in items:
            fname = it["name"]
            ext = os.path.splitext(fname)[1].lower() or "(none)"
            file_details.append({
                "path": it["path"],
                "name": fname,
                "extension": ext,
                "directory": os.path.dirname(it["path"]),
            })

        groups.append({
            "group_id": idx,
            "hash": f_hash,
            "count": len(items),
            "file_size": f_size,
            "file_size_formatted": format_size(f_size),
            "wasted": f_size * (len(items) - 1),
            "wasted_formatted": format_size(f_size * (len(items) - 1)),
            "files": file_details,
        })

    groups.sort(key=lambda g: g["wasted"], reverse=True)

    ext_counts = {}
    ext_sizes = {}
    for g in groups:
        for f in g["files"][1:]:
            ext = f["extension"]
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            ext_sizes[ext] = ext_sizes.get(ext, 0) + g["file_size"]

    type_distribution = [
        {"type": ext, "count": ext_counts[ext], "size": format_size(ext_sizes[ext])}
        for ext in sorted(ext_counts, key=lambda e: ext_counts[e], reverse=True)
    ]

    elapsed = round(time.time() - start_time, 2)
    scan_state["results"] = {
        "total_files": total_files,
        "duplicate_groups": len(duplicates),
        "total_duplicates": sum(len(items) - 1 for items in duplicates.values()),
        "wasted_bytes": wasted,
        "wasted_formatted": format_size(wasted),
        "elapsed": elapsed,
        "folder_path": folder_name,
        "groups": groups,
        "type_distribution": type_distribution,
    }

    return jsonify({"status": "done", "results": scan_state["results"]})


@app.route("/api/sample", methods=["POST"])
def scan_sample():
    sample_dir = create_sample_demo_folder()
    if scan_state["is_scanning"]:
        return jsonify({"error": "A scan is already in progress."}), 409

    reset_scan_state()
    scan_state["is_scanning"] = True

    thread = threading.Thread(target=run_scan, args=(sample_dir, "sample_demo (Server Demo Files)"), daemon=True)
    thread.start()

    return jsonify({"status": "started", "folder_path": "sample_demo (Server Demo Files)"})


@app.route("/api/progress")
def get_progress():
    return jsonify({
        "is_scanning": scan_state["is_scanning"],
        "messages": scan_state["progress_messages"],
        "has_results": scan_state["results"] is not None,
        "error": scan_state["error"],
    })


@app.route("/api/results")
def get_results():
    if scan_state["results"] is None:
        return jsonify({"error": "No scan results available."}), 404
    return jsonify(scan_state["results"])


@app.route("/api/delete", methods=["POST"])
def delete_files():
    data = request.get_json() or {}
    paths = data.get("paths", [])

    deleted = []
    failed = []
    freed = 0

    for path in paths:
        try:
            size = os.path.getsize(path)
            os.remove(path)
            deleted.append(path)
            freed += size
        except (OSError, PermissionError) as e:
            failed.append({"path": path, "error": str(e)})

    return jsonify({
        "deleted_count": len(deleted),
        "failed_count": len(failed),
        "freed_bytes": freed,
        "freed_formatted": format_size(freed),
        "deleted": deleted,
        "failed": failed,
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  DUPLICATE FILE FINDER - WEB DASHBOARD")
    print("=" * 50)
    print("\n  Open your browser to: http://127.0.0.1:5000\n")
    app.run(debug=False, host="127.0.0.1", port=5000)
