import os
import sqlite3
import time
import numpy as np
from PIL import Image, ImageFile
from sentence_transformers import SentenceTransformer

# Allow PIL to load truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Allowed image extensions for semantic search
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
BATCH_SIZE = 32


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

    # Filter for pending/modified images that exist on disk
    pending_items = []
    for full_path, _ in image_records:
        if not full_path or not os.path.isfile(full_path):
            continue

        try:
            mtime = int(os.path.getmtime(full_path))
        except OSError:
            continue

        # Skip if already indexed and mtime hasn't changed
        if full_path in existing_embeddings and existing_embeddings[full_path] == mtime:
            continue

        pending_items.append((full_path, mtime))

    total_pending = len(pending_items)
    if total_pending == 0:
        print("All image files are already indexed and up-to-date!", flush=True)
        conn.close()
        return 0

    print(f"Found {total_pending} images pending indexing/update.", flush=True)
    print(f"Loading '{model_name}' vision model...", flush=True)
    model = SentenceTransformer(model_name)

    start_time = time.time()
    indexed_count = 0

    for i in range(0, total_pending, batch_size):
        batch = pending_items[i : i + batch_size]
        valid_images = []
        valid_metadata = []

        for full_path, mtime in batch:
            try:
                img = Image.open(full_path)
                img = img.convert("RGB")
                valid_images.append(img)
                valid_metadata.append((full_path, mtime))
            except Exception as e:
                print(f"Warning: Failed to open image {full_path}: {e}", flush=True)

        if valid_images:
            try:
                embeddings = model.encode(
                    valid_images, normalize_embeddings=True, convert_to_numpy=True
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

        print(f"[Indexed {min(i + batch_size, total_pending)}/{total_pending} images...]", flush=True)

    elapsed = time.time() - start_time
    print(
        f"\n[SUCCESS] Successfully indexed {indexed_count} images in {elapsed:.2f} seconds!",
        flush=True
    )


    conn.close()
    return indexed_count


if __name__ == "__main__":
    index_images()
