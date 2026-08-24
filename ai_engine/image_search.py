import os
import sys
import sqlite3
import argparse
import numpy as np
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
            print(f"Loading '{self.model_name}' vision model...", flush=True)
            self.model = SentenceTransformer(self.model_name)

    def _load_data(self):
        if not os.path.exists(self.db_path):
            print(f"Error: Database file not found at {self.db_path}", flush=True)
            return

        print(f"Loading image embeddings from database: {self.db_path}", flush=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='image_embeddings';")
        if not cursor.fetchone():
            print("Warning: Table 'image_embeddings' does not exist in database.", flush=True)
            conn.close()
            return

        cursor.execute("SELECT file_path, embedding FROM image_embeddings")
        rows = cursor.fetchall()
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
            print(f"Loaded {len(paths)} image embeddings into search index.", flush=True)
        else:
            self.embeddings_matrix = np.empty((0, 512), dtype=np.float32)
            print("No valid image embeddings found in database.", flush=True)

    def search(self, query_text: str, top_k: int = 10, min_threshold: float = 0.20):
        if not query_text or not query_text.strip():
            return []

        if self.embeddings_matrix is None or len(self.file_paths) == 0:
            print("No image embeddings available to search. Please run indexer first.", flush=True)
            return []

        self._load_model()

        # Encode query text into normalized 512-dim vector
        query_vec = self.model.encode(
            query_text, normalize_embeddings=True, convert_to_numpy=True
        ).astype(np.float32)

        # Compute cosine similarity via matrix dot product
        scores = np.dot(self.embeddings_matrix, query_vec)

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


def search_images(query_text: str, top_k: int = 10, min_threshold: float = 0.20, db_path=None, searcher=None):
    if searcher is None:
        searcher = ImageSearcher(db_path=db_path)
    return searcher.search(query_text=query_text, top_k=top_k, min_threshold=min_threshold)


def run_cli():
    parser = argparse.ArgumentParser(description="Offline Semantic Image Search using CLIP")
    parser.add_argument("--query", "-q", type=str, help="Search query for semantic image search")
    parser.add_argument("--top_k", "-k", type=int, default=10, help="Number of results to return")
    parser.add_argument("--threshold", "-t", type=float, default=0.20, help="Minimum similarity score threshold")
    args = parser.parse_args()

    searcher = ImageSearcher()

    if args.query:
        print(f"\n--- Searching for: '{args.query}' ---", flush=True)
        results = searcher.search(args.query, top_k=args.top_k, min_threshold=args.threshold)
        _print_results(results)
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
