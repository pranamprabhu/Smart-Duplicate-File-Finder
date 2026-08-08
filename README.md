# 📁 Smart Duplicate File Finder

> An automated, high-performance storage management utility that scans directories, detects identical files via MD5 digital hashing, and reclaims wasted disk space.

[![Live Web Dashboard](https://img.shields.io/badge/Live_Demo-smart--duplicate--file--finder.onrender.com-10b981?style=for-the-badge&logo=render)](https://smart-duplicate-file-finder.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

🌐 **Live Web Application:** [https://smart-duplicate-file-finder.onrender.com](https://smart-duplicate-file-finder.onrender.com)

---

## 📖 About The Project

**Smart Duplicate File Finder** is an automated utility designed to identify and manage duplicate files within your storage. It scans folders, compares file sizes, and uses digital hashing to accurately detect identical files. By identifying redundant files, it helps reduce unnecessary storage usage and keeps your files organized. Simple, fast, and efficient file management at your fingertips.

---

## ⚡ Key Features

- **🌐 Web Dashboard:** Fresh, modern light-theme dashboard with floating ambient animations, live scan logs, and interactive file type breakdown donut chart.
- **🚀 3-Stage Ultra-Fast Scanning:**
  - **Stage 1 (Walk & Size Pre-Filter):** Traverses folder trees recursively and groups files by byte size. Discards unique size files immediately.
  - **Stage 2 (8 KB Fast Partial Hash):** Reads only the first 8 KB of size-matched files to eliminate 95%+ of false matches instantly.
  - **Stage 3 (Multithreaded Full MD5 Hash):** Computes full MD5 signatures in parallel across CPU cores only for confirmed candidate matches.
- **📊 Storage Space Analytics:** Calculates wasted bytes and converts values into human-readable units (KB, MB, GB, TB).
- **🗑 One-Click Duplicate Cleanup:** Safely deletes duplicate copies while preserving 1 original file per group.
- **📜 Auto-Generated Audit Reports:** Saves structured JSON and formatted TXT scan logs into the `reports/` folder.
- **💻 Multiple Run Modes:** Use the Web Dashboard, Interactive Terminal CLI, or a compact 25-line standalone script.

---

## 📁 Project Structure

```text
Dublicate_File_Finder/
│
├── web_app.py              # Flask web server & REST API endpoints
├── templates/
│   └── index.html          # Dashboard UI (HTML5, CSS3, Vanilla JS)
│
├── scanner.py              # 3-stage multithreaded directory scanner
├── hasher.py               # 8 KB partial + chunked full MD5 hasher
├── utils.py                # Byte size formatter & space calculator
├── report.py               # JSON & TXT report exporter
│
├── main.py                 # Interactive CLI menu with cleanup & reports
├── app.py                  # Command-line scanner script
├── standalone_finder.py    # Compact ~25 line single-file script version
│
├── reports/                # Output folder for generated scan reports
├── LICENSE                 # MIT License file
├── requirements.txt        # Project dependencies (Flask)
└── README.md               # Project documentation
```

---

## 🛠 Tech Stack

- **Core Logic:** Python 3 (built-in `os`, `hashlib`, `concurrent.futures`, `json`, `collections`)
- **Backend Web Server:** Flask (Python)
- **Frontend UI:** HTML5, CSS3 (Mint Green Light Theme, CSS Grid/Flexbox, Animations), Vanilla JavaScript (Fetch API)

---

## 🚀 Installation & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

---

### Option 1: Web Dashboard (Recommended)

- **🌐 Live Hosted App (No Installation Needed):**
  👉 **[https://smart-duplicate-file-finder.onrender.com](https://smart-duplicate-file-finder.onrender.com)**

- **💻 Run Locally:**
  ```bash
  python web_app.py
  ```
  Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

### Option 2: Interactive Terminal CLI
Run the interactive terminal tool with duplicate file cleanup:
```bash
python main.py
```

---

### Option 3: Command-Line Scanner
Run a quick scan from the terminal:
```bash
python app.py "C:\path\to\your\folder"
```

---

### Option 4: Compact Standalone Script (~25 lines)
Run the lightweight single-file script:
```bash
python standalone_finder.py
```

---

## ⚙️ How The Hashing Pipeline Works

```text
[ Target Directory ]
         │
         ▼
[ Stage 1: Folder Walk & Size Grouping ] ──► (Skips 0-byte & unique size files)
         │
         ▼
[ Stage 2: 8 KB Fast Partial Hashing ]   ──► (Eliminates 95% false matches)
         │
         ▼
[ Stage 3: Multithreaded Full MD5 Hash ] ──► (Verifies exact duplicate signatures)
         │
         ▼
[ Results & Wasted Storage Cleanup ]
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for full details.