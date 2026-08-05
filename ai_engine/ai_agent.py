import sqlite3
import os
import json
import re
import ollama  # pyrefly: ignore [missing-import]

# Dynamic SQLite database file path resolution
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

SYSTEM_PROMPT = """
You are an AI File Manager Search Agent. Convert natural language queries into a SQLite WHERE clause.
Database Table Columns:
- FileName (TEXT)
- FilePath (TEXT)
- Extension (TEXT, e.g., '.zip', '.rar', '.pdf', '.mp4')
- FileSizeBytes (INTEGER)
- Category (TEXT)

CRITICAL RULES:
1. Return ONLY the raw SQL WHERE condition text.
2. DO NOT use JSON, DO NOT use markdown, DO NOT use escape quotes or backslashes.
3. Extension values MUST include the dot (e.g. '.zip', '.rar').
4. Always spell Extension correctly.

Example Output:
(Extension = '.zip' OR Extension = '.rar') AND FileSizeBytes > 10485760
"""

def query_files_with_ai(user_prompt, model_name="phi3"):
    db_path = get_db_path()
    try:
        if not os.path.exists(db_path):
            print(f"Error: Database file not found at {os.path.abspath(db_path)}")
            return []

        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        where_clause = response['message']['content'].strip()
        print(f"\nAI LLM Raw Response:\n{where_clause}\n")

        # Clean markdown codeblocks or 'WHERE' prefix if present
        where_clause = re.sub(r'```sql|```', '', where_clause, flags=re.IGNORECASE).strip()
        where_clause = re.sub(r'^\s*WHERE\s+', '', where_clause, flags=re.IGNORECASE).strip()

        # Connect to SQLite Database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Determine table name and columns dynamically
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        table_name = "IndexedFiles" if "IndexedFiles" in tables else ("Files" if "Files" in tables else tables[0])

        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = [r[1] for r in cursor.fetchall()]
        path_col = "FilePath" if "FilePath" in cols else ("FullPath" if "FullPath" in cols else "FilePath")
        cat_col = "Category" if "Category" in cols else "Extension"

        sql = f"SELECT FileName, {path_col}, FileSizeBytes, {cat_col} FROM {table_name} WHERE {where_clause} LIMIT 10;"
        print(f"Executing SQL: {sql}\n")
        
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()

        return results

    except Exception as e:
        print(f"Error executing AI Agent Search: {e}")
        return []

if __name__ == "__main__":
    prompt = "find large zip or rar files"
    print(f"User Query: '{prompt}'")
    results = query_files_with_ai(prompt)
    
    print(f"--- Search Results ({len(results)}) ---")
    for row in results:
        print(f"File: {row[0]} | Path: {row[1]} | Size: {round(row[2]/1024/1024, 2)} MB | Category/Ext: {row[3]}")