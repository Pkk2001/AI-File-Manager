import os
import sys
import gc
os.environ["TQDM_DISABLE"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import sqlite3
import argparse
import numpy as np
import torch
from sentence_transformers import SentenceTransformer 


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


class ImageSearcher:
    def __init__(self, db_path=None, model_name="clip-ViT-B-32"):
        if db_path is None:
            db_path = get_db_path()
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.file_paths = []
        self.embeddings_matrix = None
        self._load_data()

    def _load_model(self):
        if self.model is None:
            sys.stderr.write(f"Loading '{self.model_name}' vision model...\n")
            self.model = SentenceTransformer(self.model_name)

    def _load_data(self):
        if not os.path.exists(self.db_path):
            sys.stderr.write(f"Error: Database file not found at {self.db_path}\n")
            return

        sys.stderr.write(f"Loading image embeddings from database: {self.db_path}\n")
        conn = None
        rows = []
        try:
            db_uri = f"file:{os.path.abspath(self.db_path)}?mode=ro" if os.path.exists(self.db_path) else self.db_path
            conn = sqlite3.connect(db_uri, uri=True, timeout=30.0)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='image_embeddings';")
            if not cursor.fetchone():
                sys.stderr.write("Warning: Table 'image_embeddings' does not exist in database.\n")
                return

            cursor.execute("SELECT file_path, embedding FROM image_embeddings")
            rows = cursor.fetchall()
        except Exception as e:
            sys.stderr.write(f"Error loading image embeddings from database: {e}\n")
            rows = []
        finally:
            if conn:
                conn.close()

        paths = []
        vectors = []
        for path, blob in rows:
            vec = np.frombuffer(blob, dtype=np.float32)
            if vec.shape[0] == 512:
                paths.append(path)
                vectors.append(vec)

        self.file_paths = paths
        if vectors:
            self.embeddings_matrix = np.vstack(vectors)
            sys.stderr.write(f"Loaded {len(paths)} image embeddings into search index.\n")
        else:
            self.embeddings_matrix = np.empty((0, 512), dtype=np.float32)
            sys.stderr.write("No valid image embeddings found in database.\n")

    def search(self, query_text: str, top_k: int = 25, min_threshold: float = 0.20):
        if not query_text or not query_text.strip():
            return []

        if self.embeddings_matrix is None or len(self.file_paths) == 0:
            sys.stderr.write("No image embeddings available to search. Please run indexer first.\n")
            return []

        self._load_model()

        # Encode query text into normalized 512-dim vector strictly with torch.no_grad()
        with torch.no_grad():
            query_vec = self.model.encode(
                query_text, normalize_embeddings=True, convert_to_numpy=True
            ).astype(np.float32)

        # Compute cosine similarity via matrix dot product
        scores = np.dot(self.embeddings_matrix, query_vec)

        # Perform explicit GC cleanup after computing similarities
        gc.collect()

        # Sort top-K indices descending
        sorted_indices = np.argsort(scores)[::-1]

        results = []
        for idx in sorted_indices[:top_k]:
            score = float(scores[idx])
            if score < min_threshold:
                break
            results.append({
                "file_path": self.file_paths[idx],
                "score": round(score, 4)
            })

        return results


def search_images(query_text: str, top_k: int = 25, min_threshold: float = 0.20, db_path=None, searcher=None):
    if searcher is None:
        searcher = ImageSearcher(db_path=db_path)
    return searcher.search(query_text=query_text, top_k=top_k, min_threshold=min_threshold)


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

def run_cli():
    parser = argparse.ArgumentParser(description="Offline Semantic Image Search using CLIP")
    parser.add_argument("--query", "-q", type=str, help="Search query for semantic image search")
    parser.add_argument("--top_k", "-k", type=int, default=25, help="Number of results to return")
    parser.add_argument("--threshold", "-t", type=float, default=0.15, help="Minimum similarity score threshold")
    parser.add_argument("--drive", type=str, default=None, help="Filter results by target drive letter (e.g. C:)")
    parser.add_argument("--db_path", type=str, default=None, help="SQLite database path override")
    parser.add_argument("--json", action="store_true", help="Output pure JSON format on stdout")
    args = parser.parse_args()

    if args.json and not args.query:
        import json
        print(json.dumps({"query": "", "mode": "clip", "count": 0, "results": []}), flush=True)
        sys.exit(0)

    searcher = ImageSearcher(db_path=args.db_path)

    if args.query:
        if not args.json:
            sys.stderr.write(f"\n--- Searching for: '{args.query}' ---\n")
        raw_results = searcher.search(args.query, top_k=args.top_k, min_threshold=args.threshold)

        # Filter by drive if specified
        if args.drive and args.drive.lower() != 'all':
            clean_d = args.drive.rstrip('\\/').rstrip(':').upper() + ":"
            raw_results = [r for r in raw_results if r["file_path"].upper().startswith(clean_d)]

        if args.json:
            import json
            db_p = searcher.db_path
            conn = None
            cursor = None
            if db_p and os.path.exists(db_p):
                try:
                    db_uri = f"file:{os.path.abspath(db_p)}?mode=ro"
                    conn = sqlite3.connect(db_uri, uri=True, timeout=30.0)
                    cursor = conn.cursor()
                except Exception as e:
                    sys.stderr.write(f"Warning: Could not open DB for metadata enrichment: {e}\n")
                    conn = None
                    cursor = None

            results = []
            try:
                for item in raw_results:
                    path = item["file_path"]
                    score = round(float(item["score"]) * 100, 1)
                    size = 0
                    ext = os.path.splitext(path)[1]
                    mod = ""
                    name = os.path.basename(path)

                    if cursor:
                        cursor.execute("SELECT FileName, FileSizeBytes, Extension, LastModifiedTime FROM Files WHERE FullPath = ? LIMIT 1", (path,))
                        row = cursor.fetchone()
                        if row:
                            name = row[0] or name
                            size = row[1] or 0
                            ext = row[2] or ext
                            mod = row[3] or ""

                    results.append({
                        "name": name,
                        "path": path,
                        "size": size,
                        "formatted_size": format_size(size),
                        "extension": ext,
                        "category": "Images",
                        "modified": mod,
                        "score": score
                    })
            finally:
                if conn:
                    conn.close()

            print(json.dumps({"query": args.query, "mode": "clip", "count": len(results), "results": results}, ensure_ascii=False), flush=True)
            sys.exit(0)
        else:
            _print_results(raw_results)
    else:
        print("\n=== Offline Semantic Image Search Interactive CLI ===", flush=True)
        print("Type your search query (or 'exit' / 'quit' to stop):", flush=True)
        while True:
            try:
                user_input = input("\nImage Search > ").strip()
                if not user_input or user_input.lower() in ("exit", "quit"):
                    print("Exiting image search.", flush=True)
                    break
                results = searcher.search(user_input, top_k=args.top_k, min_threshold=args.threshold)
                _print_results(results)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting image search.", flush=True)
                break

def _print_results(results):
    if not results:
        print("No matching images found above threshold.", flush=True)
        return

    print(f"Found {len(results)} matching image(s):\n", flush=True)
    for idx, item in enumerate(results, 1):
        similarity_pct = item["score"] * 100
        print(f" {idx:2d}. [{similarity_pct:5.1f}% match | Score: {item['score']:.4f}] {item['file_path']}", flush=True)

if __name__ == "__main__":
    run_cli()

