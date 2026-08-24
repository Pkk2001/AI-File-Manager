import os
import sys
import sqlite3
import shutil
import ctypes
import argparse
from datetime import datetime

# Set console encoding to UTF-8 if possible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def format_size(bytes_val):
    if bytes_val is None:
        bytes_val = 0
    if bytes_val >= 1073741824:  # 1 GB
        return f"{bytes_val / 1073741824:.2f} GB"
    elif bytes_val >= 1048576:  # 1 MB
        return f"{bytes_val / 1048576:.2f} MB"
    elif bytes_val >= 1024:  # 1 KB
        return f"{bytes_val / 1024:.2f} KB"
    return f"{bytes_val} Bytes"

def create_bar(percentage, length=18):
    percentage = max(0.0, min(100.0, percentage))
    filled = int(round(length * percentage / 100.0))
    # Use ASCII characters to guarantee compatibility on Windows CP1252 / standard cmd
    bar = '=' * filled + ' ' * (length - filled)
    return f"[{bar}] {percentage:5.1f}%"

def get_db_path():
    base_core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "FileManager.Core"))
    candidate_paths = [
        os.path.join(base_core_dir, "files.db"),
        os.path.join(base_core_dir, "files_index.db"),
        os.path.join(base_core_dir, "bin", "Debug", "net9.0", "files.db"),
        os.path.join(base_core_dir, "bin", "Debug", "net9.0", "files_index.db"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return candidate_paths[0]

def get_drive_overviews(target_drive=None):
    drives = []
    if target_drive:
        clean = target_drive.rstrip('\\/').rstrip(':').upper() + ":\\"
        candidate_drives = [clean]
    else:
        candidate_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]

    for drive_path in candidate_drives:
        if not os.path.exists(drive_path):
            continue
        try:
            total, used, free = shutil.disk_usage(drive_path)
            vol_label = ""
            fs_type = "Fixed"
            if sys.platform == 'win32':
                vol_buf = ctypes.create_unicode_buffer(1024)
                fs_buf = ctypes.create_unicode_buffer(1024)
                try:
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        ctypes.c_wchar_p(drive_path),
                        vol_buf, 1024, None, None, None, fs_buf, 1024
                    )
                    vol_label = vol_buf.value
                    fs_type = fs_buf.value
                except Exception:
                    pass
            used_pct = (used / total * 100.0) if total > 0 else 0.0
            drives.append({
                "drive": drive_path,
                "label": vol_label or "Local Disk",
                "format": fs_type,
                "total": total,
                "used": used,
                "free": free,
                "used_pct": used_pct
            })
        except Exception:
            pass
    return drives

CATEGORY_MAP = {
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.pptx', '.csv', '.rtf', '.odt', '.ods', '.odp'],
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.ico', '.tiff'],
    'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso'],
    'Source Code': ['.cs', '.js', '.ts', '.py', '.html', '.css', '.json', '.cpp', '.c', '.h', '.java', '.pyw', '.sh', '.ps1'],
    'Executable/Apps': ['.exe', '.msi', '.apk', '.app', '.bat', '.cmd']
}

def get_category_from_extension(ext):
    if not ext:
        return 'Other'
    e = ext.strip().lower()
    if not e.startswith('.'):
        e = '.' + e
    for cat, exts in CATEGORY_MAP.items():
        if e in exts:
            return cat
    return 'Other'

def format_drive_pattern(target_drive):
    clean = target_drive.rstrip('\\/').rstrip(':').upper()
    return f"{clean}:%"

def get_category_breakdown(conn, target_drive=None):
    cursor = conn.cursor()
    params = []
    where_clause = ""
    if target_drive:
        where_clause = "WHERE FullPath LIKE ?"
        params.append(format_drive_pattern(target_drive))

    query = f"""
        SELECT Extension, COUNT(*), SUM(FileSizeBytes)
        FROM Files
        {where_clause}
        GROUP BY Extension;
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()

    cat_totals = {}
    for ext, count, size in rows:
        size = size or 0
        cat = get_category_from_extension(ext)
        if cat not in cat_totals:
            cat_totals[cat] = {"count": 0, "size": 0}
        cat_totals[cat]["count"] += count
        cat_totals[cat]["size"] += size

    overall_size = sum(item["size"] for item in cat_totals.values())
    result = []
    for cat, data in cat_totals.items():
        pct = (data["size"] / overall_size * 100.0) if overall_size > 0 else 0.0
        result.append({
            "category": cat,
            "count": data["count"],
            "size": data["size"],
            "formatted_size": format_size(data["size"]),
            "percentage": pct
        })

    result.sort(key=lambda x: x["size"], reverse=True)
    return result

def get_extension_breakdown(conn, target_drive=None, top=10):
    cursor = conn.cursor()
    params = []
    where_clause = ""
    if target_drive:
        where_clause = "WHERE FullPath LIKE ?"
        params.append(format_drive_pattern(target_drive))

    query = f"""
        SELECT Extension, COUNT(*), SUM(FileSizeBytes) as TotalSize
        FROM Files
        {where_clause}
        GROUP BY Extension
        ORDER BY TotalSize DESC
        LIMIT ?;
    """
    params.append(top)
    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for ext, count, size in rows:
        ext_str = ext if ext else "[No Ext]"
        size = size or 0
        result.append({
            "extension": ext_str,
            "count": count,
            "size": size,
            "formatted_size": format_size(size)
        })
    return result

def get_largest_files(conn, target_drive=None, limit=20):
    cursor = conn.cursor()
    params = []
    where_clause = ""
    if target_drive:
        where_clause = "WHERE FullPath LIKE ?"
        params.append(format_drive_pattern(target_drive))

    query = f"""
        SELECT FullPath, FileName, FileSizeBytes, Extension, LastModifiedTime
        FROM Files
        {where_clause}
        ORDER BY FileSizeBytes DESC
        LIMIT ?;
    """
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for path, name, size, ext, last_mod in rows:
        size = size or 0
        cat = get_category_from_extension(ext)
        result.append({
            "path": path,
            "name": name,
            "size": size,
            "formatted_size": format_size(size),
            "category": cat,
            "last_modified": last_mod or ""
        })
    return result

def print_storage_analysis(target_drive=None):
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found at: {os.path.abspath(db_path)}")
        return

    drive_filter_title = f"Filter: Drive {target_drive.upper()}" if target_drive else "Scope: All System Drives"

    print("\n" + "=" * 90)
    print(f"                   SYSTEM STORAGE ANALYZER REPORT ({drive_filter_title})")
    print("=" * 90 + "\n")

    # 1. Drive Summaries
    drives = get_drive_overviews(target_drive)
    print("+" + "-" * 88 + "+")
    print("| SYSTEM DRIVES OVERVIEW" + " " * 67 + "|")
    print("+" + "-" * 88 + "+")
    print(f"| {'Drive':<6} | {'Volume Label':<16} | {'Format':<6} | {'Used / Total Space':<24} | {'Usage Visual':<24} |")
    print("+" + "-" * 88 + "+")
    for d in drives:
        used_total_str = f"{format_size(d['used'])} / {format_size(d['total'])}"
        bar_str = create_bar(d['used_pct'], length=15)
        print(f"| {d['drive']:<6} | {d['label']:<16.16} | {d['format']:<6} | {used_total_str:<24} | {bar_str:<24} |")
    print("+" + "-" * 88 + "+\n")

    # Connect to SQLite
    conn = sqlite3.connect(db_path)

    # 2. Category Storage Breakdown
    cat_breakdown = get_category_breakdown(conn, target_drive)
    print("+" + "-" * 88 + "+")
    print("| CATEGORY STORAGE DISTRIBUTION" + " " * 59 + "|")
    print("+" + "-" * 88 + "+")
    print(f"| {'Category':<18} | {'Indexed Files':<13} | {'Total Size':<14} | {'Storage Share Visual':<34} |")
    print("+" + "-" * 88 + "+")
    for c in cat_breakdown:
        bar_str = create_bar(c['percentage'], length=22)
        print(f"| {c['category']:<18} | {c['count']:<13,d} | {c['formatted_size']:<14} | {bar_str:<34} |")
    print("+" + "-" * 88 + "+\n")

    # 3. Top Extension Breakdown
    ext_breakdown = get_extension_breakdown(conn, target_drive, top=10)
    print("+" + "-" * 88 + "+")
    print("| TOP 10 FILE EXTENSIONS BY STORAGE" + " " * 55 + "|")
    print("+" + "-" * 88 + "+")
    print(f"| {'Rank':<6} | {'Extension':<15} | {'Indexed Files':<18} | {'Total Size':<39} |")
    print("+" + "-" * 88 + "+")
    for idx, e in enumerate(ext_breakdown, 1):
        print(f"| {idx:<6} | {e['extension']:<15} | {e['count']:<18,d} | {e['formatted_size']:<39} |")
    print("+" + "-" * 88 + "+\n")

    # 4. Top Largest Space-Hogging Files
    largest_files = get_largest_files(conn, target_drive, limit=15)
    print("+" + "-" * 88 + "+")
    print("| TOP SPACE-HOGGING LARGEST FILES" + " " * 57 + "|")
    print("+" + "-" * 88 + "+")
    print(f"| {'Rank':<4} | {'Size':<10} | {'Category':<15} | {'File Name / Full Path':<51} |")
    print("+" + "-" * 88 + "+")
    for idx, f in enumerate(largest_files, 1):
        print(f"| {idx:<4} | {f['formatted_size']:<10} | {f['category']:<15.15} | {f['name']:<51.51} |")
        print(f"| {'':<4} | {'':<10} | {'':<15} | -> {f['path']:<48.48} |")
    print("+" + "-" * 88 + "+\n")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI File Manager - System Storage Analyzer")
    parser.add_argument("--drive", type=str, default=None, help="Target drive letter to filter analysis (e.g. C: or D:)")
    args = parser.parse_args()

    print_storage_analysis(target_drive=args.drive)
