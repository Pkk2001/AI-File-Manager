import os
import sys
import json
import sqlite3
import hashlib
import shutil
import ctypes
import argparse
import re

# Ensure UTF-8 output encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def get_db_path(custom_db_path=None):
    if custom_db_path and os.path.exists(custom_db_path):
        return os.path.abspath(custom_db_path)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidate_paths = [
        os.path.join(project_root, "backend", "FileManager.Core", "files.db"),
        os.path.join(project_root, "files.db"),
        os.path.join(project_root, "backend", "FileManager.Core", "bin", "Debug", "net9.0", "files.db"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            return p
    return candidate_paths[0]

CATEGORY_MAP = {
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.pptx', '.csv', '.rtf', '.odt', '.ods', '.odp'],
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.ico', '.tiff'],
    'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso'],
    'Source Code': ['.cs', '.js', '.ts', '.py', '.html', '.css', '.json', '.cpp', '.c', '.h', '.java', '.pyw', '.sh', '.ps1'],
    'Executable/Apps': ['.exe', '.msi', '.apk', '.app', '.bat', '.cmd']
}

def get_category(ext):
    if not ext:
        return 'Other'
    e = ext.strip().lower()
    if not e.startswith('.'):
        e = '.' + e
    for cat, exts in CATEGORY_MAP.items():
        if e in exts:
            return cat
    return 'Other'

def format_size(bytes_val):
    if bytes_val is None:
        bytes_val = 0
    if bytes_val >= 1073741824:
        return f"{bytes_val / 1073741824:.2f} GB"
    elif bytes_val >= 1048576:
        return f"{bytes_val / 1048576:.2f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    return f"{bytes_val} B"

def get_drives():
    drives = []
    candidate_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    for drive_path in candidate_drives:
        try:
            total, used, free = shutil.disk_usage(drive_path)
            vol_label = "Local Disk"
            fs_type = "NTFS"
            if sys.platform == 'win32':
                vol_buf = ctypes.create_unicode_buffer(1024)
                fs_buf = ctypes.create_unicode_buffer(1024)
                try:
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        ctypes.c_wchar_p(drive_path),
                        vol_buf, 1024, None, None, None, fs_buf, 1024
                    )
                    vol_label = vol_buf.value or "Local Disk"
                    fs_type = fs_buf.value or "NTFS"
                except Exception:
                    pass
            drives.append({
                "drive": drive_path,
                "label": vol_label,
                "format": fs_type,
                "total": total,
                "used": used,
                "free": free,
                "used_pct": round((used / total * 100.0), 1) if total > 0 else 0
            })
        except Exception as e:
            pass
    return drives

def extract_drive_from_query(query):
    if not query:
        return None, query
    m = re.search(r'\b(?:in|on|from)?\s*([a-zA-Z]):?\\?\b(?:\s*drive)?', query, re.IGNORECASE)
    if m:
        drive_letter = m.group(1).upper() + ":\\"
        clean_query = re.sub(r'\b(?:in|on|from)?\s*[a-zA-Z]:?\\?\s*(?:drive)?\b', '', query, flags=re.IGNORECASE).strip()
        return drive_letter, clean_query
    return None, query

def search_files(query="", mode="text", drive=None, custom_db_path=None, limit=100):
    db_path = get_db_path(custom_db_path)
    if not os.path.exists(db_path):
        return {"error": f"Database file not found at {db_path}", "results": []}

    # Extract drive filter from query prompt if not explicitly passed
    extracted_drive, clean_query = extract_drive_from_query(query)
    effective_drive = drive or extracted_drive

    # 1. CLIP Image Search Mode
    if mode in ("clip", "image"):
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from image_search import ImageSearcher
            searcher = ImageSearcher(db_path=db_path)
            raw_results = searcher.search(query, top_k=limit)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            results = []
            for item in raw_results:
                path = item["file_path"]
                score = item["score"]
                cursor.execute("SELECT FileName, FileSizeBytes, Extension, LastModifiedTime FROM Files WHERE FullPath = ? LIMIT 1", (path,))
                row = cursor.fetchone()
                if row:
                    results.append({
                        "name": row[0],
                        "path": path,
                        "size": row[1] or 0,
                        "formatted_size": format_size(row[1]),
                        "extension": row[2] or "",
                        "category": get_category(row[2]),
                        "modified": row[3] or "",
                        "score": round(score * 100, 1)
                    })
                else:
                    filename = os.path.basename(path)
                    ext = os.path.splitext(path)[1]
                    results.append({
                        "name": filename,
                        "path": path,
                        "size": 0,
                        "formatted_size": "Unknown",
                        "extension": ext,
                        "category": "Images",
                        "modified": "",
                        "score": round(score * 100, 1)
                    })
            conn.close()
            return {"query": query, "mode": "clip", "count": len(results), "results": results}
        except Exception as e:
            sys.stderr.write(f"[WARN] CLIP Image Search Error: {e}. Falling back to SQL search.\n")

    # 2. Ollama LLM AI Agent Mode (Attempt first if mode is ollama)
    if mode in ("ollama", "ai"):
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from ai_agent import query_files_with_ai
            ai_rows = query_files_with_ai(query)
            if ai_rows:
                results = []
                for name, path, size, ext in ai_rows:
                    results.append({
                        "name": name,
                        "path": path,
                        "size": size or 0,
                        "formatted_size": format_size(size),
                        "extension": ext or "",
                        "category": get_category(ext),
                        "modified": "",
                        "score": 100.0
                    })
                return {"query": query, "mode": "ollama", "count": len(results), "results": results}
        except Exception as e:
            sys.stderr.write(f"[WARN] Ollama AI Agent failed or offline: {e}. Executing fast SQL fallback.\n")

    # 3. Direct Fast SQLite Fallback / Keyword Search
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    where_clauses = []
    params = []

    # Drive Scope Filter
    if effective_drive:
        clean_d = effective_drive.rstrip('\\/').rstrip(':').upper() + ":%"
        where_clauses.append("FullPath LIKE ?")
        params.append(clean_d)

    q_text = clean_query if clean_query else query
    if q_text and q_text.strip():
        # Check for extension search like "pdf", ".pdf", "mkv", "png"
        raw_words = [w.strip() for w in q_text.strip().split() if w.strip()]
        
        # Identify extension terms
        ext_terms = []
        keyword_terms = []
        for word in raw_words:
            w_lower = word.lower()
            if w_lower in ('find', 'files', 'file', 'in', 'c', 'd', 'e', 'f', 'drive', 'show', 'all', 'me'):
                continue
            if w_lower.startswith('.'):
                ext_terms.append(w_lower)
            elif w_lower in ('pdf', 'doc', 'docx', 'txt', 'mkv', 'mp4', 'png', 'jpg', 'zip', 'rar', 'exe', 'py', 'js', 'ts'):
                ext_terms.append('.' + w_lower)
            else:
                keyword_terms.append(word)

        sub_conditions = []
        if ext_terms:
            ext_or = " OR ".join(["Extension = ?" for _ in ext_terms])
            sub_conditions.append(f"({ext_or})")
            params.extend(ext_terms)

        if keyword_terms:
            for kw in keyword_terms:
                sub_conditions.append("(FileName LIKE ? OR FullPath LIKE ? OR Extension LIKE ?)")
                p = f"%{kw}%"
                params.extend([p, p, p])

        if sub_conditions:
            where_clauses.append(" AND ".join(sub_conditions))

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    sql = f"SELECT FullPath, FileName, FileSizeBytes, Extension, LastModifiedTime FROM Files{where_sql} LIMIT ?"
    params.append(limit)

    sys.stderr.write(f"[INFO] Executing SQLite Query: {sql} | Params: {params}\n")
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for path, name, size, ext, mod in rows:
        size = size or 0
        results.append({
            "name": name,
            "path": path,
            "size": size,
            "formatted_size": format_size(size),
            "extension": ext or "",
            "category": get_category(ext),
            "modified": mod or "",
            "score": 100.0
        })

    return {"query": query, "mode": mode, "count": len(results), "results": results}

def get_storage_analysis(target_drive=None, custom_db_path=None):
    db_path = get_db_path(custom_db_path)
    drives = get_drives()

    if not os.path.exists(db_path):
        return {"drives": drives, "categories": [], "top_extensions": [], "largest_files": []}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    params = []
    where_sql = ""
    if target_drive:
        clean_drive = target_drive.rstrip('\\/').rstrip(':').upper() + ":%"
        where_sql = "WHERE FullPath LIKE ?"
        params.append(clean_drive)

    cursor.execute(f"SELECT Extension, COUNT(*), SUM(FileSizeBytes) FROM Files {where_sql} GROUP BY Extension", params)
    ext_rows = cursor.fetchall()

    cat_map = {}
    for ext, count, size in ext_rows:
        size = size or 0
        cat = get_category(ext)
        if cat not in cat_map:
            cat_map[cat] = {"count": 0, "size": 0}
        cat_map[cat]["count"] += count
        cat_map[cat]["size"] += size

    total_size = sum(c["size"] for c in cat_map.values())
    categories = []
    for cat, d in cat_map.items():
        pct = (d["size"] / total_size * 100.0) if total_size > 0 else 0.0
        categories.append({
            "category": cat,
            "count": d["count"],
            "size": d["size"],
            "formatted_size": format_size(d["size"]),
            "percentage": round(pct, 1)
        })
    categories.sort(key=lambda x: x["size"], reverse=True)

    params_ext = list(params)
    cursor.execute(f"SELECT Extension, COUNT(*), SUM(FileSizeBytes) as TotalSize FROM Files {where_sql} GROUP BY Extension ORDER BY TotalSize DESC LIMIT 10", params_ext)
    top_extensions = []
    for ext, count, size in cursor.fetchall():
        size = size or 0
        top_extensions.append({
            "extension": ext or "[No Ext]",
            "count": count,
            "size": size,
            "formatted_size": format_size(size)
        })

    params_files = list(params)
    params_files.append(25)
    cursor.execute(f"SELECT FullPath, FileName, FileSizeBytes, Extension, LastModifiedTime FROM Files {where_sql} ORDER BY FileSizeBytes DESC LIMIT ?", params_files)
    largest_files = []
    for path, name, size, ext, mod in cursor.fetchall():
        size = size or 0
        largest_files.append({
            "name": name,
            "path": path,
            "size": size,
            "formatted_size": format_size(size),
            "category": get_category(ext),
            "modified": mod or ""
        })

    conn.close()
    return {
        "drives": drives,
        "categories": categories,
        "top_extensions": top_extensions,
        "largest_files": largest_files
    }

def get_partial_md5(file_path, bytes_to_read=8192):
    try:
        if not file_path or not os.path.exists(file_path):
            return ""
        with open(file_path, 'rb') as f:
            chunk = f.read(bytes_to_read)
            if not chunk:
                return ""
            return hashlib.md5(chunk).hexdigest()
    except Exception:
        return ""

def get_duplicates(custom_db_path=None, limit_groups=50):
    db_path = get_db_path(custom_db_path)
    if not os.path.exists(db_path):
        return {"groups": [], "total_waste_bytes": 0, "formatted_waste": "0 B"}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT FullPath, FileName, FileSizeBytes, Extension, LastModifiedTime
        FROM Files
        WHERE FileSizeBytes > 1024 AND FileSizeBytes IN (
            SELECT FileSizeBytes
            FROM Files
            WHERE FileSizeBytes > 1024
            GROUP BY FileSizeBytes
            HAVING COUNT(*) > 1
        )
        ORDER BY FileSizeBytes DESC
        LIMIT 2000;
    """)
    rows = cursor.fetchall()
    conn.close()

    size_candidates = {}
    for path, name, size, ext, mod in rows:
        if size not in size_candidates:
            size_candidates[size] = []
        size_candidates[size].append({
            "name": name,
            "path": path,
            "size": size,
            "extension": ext or "",
            "category": get_category(ext),
            "modified": mod or ""
        })

    duplicate_groups = []
    total_waste_bytes = 0

    for size, items in size_candidates.items():
        if len(duplicate_groups) >= limit_groups:
            break
        if len(items) < 2:
            continue

        hash_groups = {}
        for item in items:
            h = get_partial_md5(item["path"])
            if not h:
                h = hashlib.md5(f"{size}_{item['name']}".encode('utf-8')).hexdigest()
            if h not in hash_groups:
                hash_groups[h] = []
            hash_groups[h].append(item)

        for h, dupes in hash_groups.items():
            if len(dupes) > 1:
                group_waste = (len(dupes) - 1) * size
                total_waste_bytes += group_waste
                duplicate_groups.append({
                    "hash": h,
                    "size": size,
                    "formatted_size": format_size(size),
                    "count": len(dupes),
                    "waste_bytes": group_waste,
                    "formatted_waste": format_size(group_waste),
                    "files": dupes
                })

    return {
        "groups": duplicate_groups,
        "total_waste_bytes": total_waste_bytes,
        "formatted_waste": format_size(total_waste_bytes)
    }

def get_db_stats(custom_db_path=None):
    db_path = get_db_path(custom_db_path)
    if not os.path.exists(db_path):
        return {"total_files": 0, "db_size": 0, "formatted_db_size": "0 B", "db_path": db_path}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Files")
        total_files = cursor.fetchone()[0]
        conn.close()

        db_size = os.path.getsize(db_path)
        return {
            "total_files": total_files,
            "db_size": db_size,
            "formatted_db_size": format_size(db_size),
            "db_path": db_path
        }
    except Exception as e:
        return {"total_files": 0, "db_size": 0, "formatted_db_size": "0 B", "error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["drives", "search", "storage", "duplicates", "stats"])
    parser.add_argument("--query", default="")
    parser.add_argument("--mode", default="text")
    parser.add_argument("--drive", default="")
    parser.add_argument("--db_path", default="")
    args = parser.parse_args()

    db_p = args.db_path if args.db_path else None

    if args.action == "drives":
        out = get_drives()
    elif args.action == "search":
        out = search_files(query=args.query, mode=args.mode, drive=args.drive, custom_db_path=db_p)
    elif args.action == "storage":
        out = get_storage_analysis(target_drive=args.drive, custom_db_path=db_p)
    elif args.action == "duplicates":
        out = get_duplicates(custom_db_path=db_p)
    elif args.action == "stats":
        out = get_db_stats(custom_db_path=db_p)
    else:
        out = {}

    print(json.dumps(out, ensure_ascii=False))
