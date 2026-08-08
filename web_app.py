"""
Duplicate File Finder - Flask Web Dashboard
A stunning dark-themed web interface for scanning and managing duplicate files.
"""
import os
import json
import time
import threading
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


def run_scan(folder_path):
    """Background thread function to run the scan."""
    try:
        scan_state["start_time"] = time.time()
        total_files, duplicates = scan_directory(folder_path, progress_callback)
        elapsed = time.time() - scan_state["start_time"]
        scan_state["elapsed"] = round(elapsed, 2)

        wasted = calculate_wasted_space(duplicates)

        # Build structured results
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

        # Sort by wasted space descending (biggest offenders first)
        groups.sort(key=lambda g: g["wasted"], reverse=True)

        # Build file type distribution
        ext_counts = {}
        ext_sizes = {}
        for g in groups:
            for f in g["files"][1:]:  # skip original, count duplicates only
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
            "folder_path": folder_path,
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
    data = request.get_json()
    folder_path = data.get("folder_path", "").strip().strip('"').strip("'")

    if not folder_path or not os.path.isdir(folder_path):
        return jsonify({"error": f"Invalid directory: '{folder_path}'"}), 400

    if scan_state["is_scanning"]:
        return jsonify({"error": "A scan is already in progress."}), 409

    reset_scan_state()
    scan_state["is_scanning"] = True

    thread = threading.Thread(target=run_scan, args=(folder_path,), daemon=True)
    thread.start()

    return jsonify({"status": "started", "folder_path": folder_path})


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
    data = request.get_json()
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
