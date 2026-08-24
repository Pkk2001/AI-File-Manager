import os
import sqlite3
import time
import numpy as np
from PIL import Image, ImageFile
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer

# Allow PIL to load truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Allowed image extensions for semantic search
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

# Optimization Constants
BATCH_SIZE = 64
MIN_FILE_SIZE_BYTES = 25 * 1024  # 25 KB
MIN_DIMENSION = 128
RESIZE_TARGET = (224, 224)
MAX_WORKERS = 8

# Directories/Keywords to skip (case-insensitive)
EXCLUDED_DIR_KEYWORDS = {
    'appdata',
    'windows',
    'program files',
    'program files (x86)',
    '$recycle.bin',
    'node_modules',
    '.git',
    '.cache',
    'steam',
    'onlinefix',
    'goldberg',
    'thumbnails',
    'temp',
    'tmp',
}

# User data keywords for priority sorting
USER_PRIORITY_KEYWORDS = [
    'desktop',
    'downloads',
    'pictures',
    'documents',
    'photos',
    'media',
    'dcim',
]


def is_ignored_path(path: str) -> bool:
    path_lower = path.lower().replace('/', '\\')
    return any(kw in path_lower for kw in EXCLUDED_DIR_KEYWORDS)


def priority_score(item: tuple) -> int:
    path_lower = item[0].lower()
    for idx, kw in enumerate(USER_PRIORITY_KEYWORDS):
        if kw in path_lower:
            return idx
    return 999


def get_db_path():
    base_core_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "backend", "FileManager.Core"
        )
    )
    candidate_paths = [
        os.path.join(base_core_dir, "files.db"),
        os.path.join(base_core_dir, "files_index.db"),
        os.path.join(base_core_dir, "bin", "Debug", "net9.0", "files.db"),
        os.path.join(base_core_dir, "bin", "Debug", "net9.0", "files_index.db"),
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "files.db")
        ),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return candidate_paths[0]


def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            last_modified INTEGER NOT NULL,
            embedding BLOB NOT NULL
        );
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_image_path ON image_embeddings(file_path);
    """)
    conn.commit()


def get_table_name(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    if "Files" in tables:
        return "Files"
    elif "IndexedFiles" in tables:
        return "IndexedFiles"
    elif tables:
        return tables[0]
    return "Files"


def fetch_existing_embeddings(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, last_modified FROM image_embeddings")
    return {row[0]: row[1] for row in cursor.fetchall()}


def fetch_image_records(conn):
    cursor = conn.cursor()
    table_name = get_table_name(cursor)

    placeholders = ",".join(["?"] * len(IMAGE_EXTENSIONS))
    query = f"""
        SELECT FullPath, LastModifiedTime FROM {table_name} 
        WHERE lower(Extension) IN ({placeholders})
    """
    cursor.execute(query, IMAGE_EXTENSIONS)
    return cursor.fetchall()


def load_and_preprocess_image(item):
    full_path, mtime = item
    try:
        if os.path.getsize(full_path) < MIN_FILE_SIZE_BYTES:
            return None

        with Image.open(full_path) as img:
            if img.width < MIN_DIMENSION or img.height < MIN_DIMENSION:
                return None
            img_rgb = img.convert("RGB")
            resized = img_rgb.resize(RESIZE_TARGET, Image.Resampling.BICUBIC)
            return (resized, full_path, mtime)
    except Exception:
        return None


def index_images(db_path=None, model_name="clip-ViT-B-32", batch_size=BATCH_SIZE):
    if db_path is None:
        db_path = get_db_path()

    print(f"Connecting to database at: {db_path}", flush=True)
    conn = sqlite3.connect(db_path)

    # Initialize schema
    init_db(conn)

    # Fetch existing embeddings for change detection
    existing_embeddings = fetch_existing_embeddings(conn)
    image_records = fetch_image_records(conn)

    print(f"Found {len(image_records)} image records in database.", flush=True)

    # Filter out system/cache directories, non-existent files, and already indexed files
    pending_items = []
    skipped_system_count = 0

    for full_path, _ in image_records:
        if not full_path or not os.path.isfile(full_path):
            continue

        if is_ignored_path(full_path):
            skipped_system_count += 1
            continue

        try:
            mtime = int(os.path.getmtime(full_path))
        except OSError:
            continue

        # Skip if already indexed and mtime hasn't changed
        if full_path in existing_embeddings and existing_embeddings[full_path] == mtime:
            continue

        pending_items.append((full_path, mtime))

    print(f"Skipped {skipped_system_count} system/cache/game directory images.", flush=True)

    # Prioritize user data paths (e.g. Desktop, Downloads, Pictures, etc.)
    pending_items.sort(key=priority_score)

    total_pending = len(pending_items)
    if total_pending == 0:
        print("All candidate image files are already indexed and up-to-date!", flush=True)
        conn.close()
        return 0

    print(f"Found {total_pending} candidate user images pending indexing/update.", flush=True)
    print(f"Loading '{model_name}' vision model...", flush=True)
    model = SentenceTransformer(model_name)

    start_time = time.time()
    indexed_count = 0
    processed_candidates = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i in range(0, total_pending, batch_size):
            batch = pending_items[i : i + batch_size]
            processed_candidates += len(batch)

            # Preprocess images concurrently across threads
            results = list(executor.map(load_and_preprocess_image, batch))
            valid_items = [r for r in results if r is not None]

            if valid_items:
                valid_images = [r[0] for r in valid_items]
                valid_metadata = [(r[1], r[2]) for r in valid_items]

                try:
                    embeddings = model.encode(
                        valid_images,
                        batch_size=batch_size,
                        normalize_embeddings=True,
                        convert_to_numpy=True
                    )
                    
                    rows_to_insert = []
                    for idx, (full_path, mtime) in enumerate(valid_metadata):
                        vec = embeddings[idx].astype(np.float32)
                        blob_data = vec.tobytes()
                        rows_to_insert.append((full_path, mtime, blob_data))

                    conn.execute("BEGIN TRANSACTION")
                    conn.executemany(
                        """
                        INSERT INTO image_embeddings (file_path, last_modified, embedding)
                        VALUES (?, ?, ?)
                        ON CONFLICT(file_path) DO UPDATE SET
                            last_modified = excluded.last_modified,
                            embedding = excluded.embedding
                        """,
                        rows_to_insert,
                    )
                    conn.commit()

                    indexed_count += len(rows_to_insert)

                except Exception as e:
                    conn.rollback()
                    print(f"Error encoding batch starting at index {i}: {e}", flush=True)

            print(
                f"[Processed {processed_candidates}/{total_pending} candidates | Indexed {indexed_count} valid images...]",
                flush=True
            )

    elapsed = time.time() - start_time
    print(
        f"\n[SUCCESS] Successfully indexed {indexed_count} images in {elapsed:.2f} seconds!",
        flush=True
    )

    conn.close()
    return indexed_count


if __name__ == "__main__":
    index_images()
