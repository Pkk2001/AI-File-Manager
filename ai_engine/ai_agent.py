import sqlite3
import os
import json
import re
import sys
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

Database Table: `Files`
Available Columns ONLY:
- FileName (TEXT)
- FullPath (TEXT)
- Extension (TEXT, e.g., '.mkv', '.mp4', '.pdf', '.zip', '.rar', '.jpg', '.png')
- FileSizeBytes (INTEGER)

CRITICAL RULES:
1. ONLY use the available columns: FileName, FullPath, Extension, FileSizeBytes.
2. DO NOT use 'Category' or any non-existent columns.
3. Extension values MUST start with a dot (e.g., '.mkv', '.mp4', '.pdf', '.jpg', '.png').
4. When filtering extensions alongside keyword searches, ALWAYS wrap multiple extension ORs in parentheses, e.g.: (Extension = '.jpg' OR Extension = '.png' OR Extension = '.jpeg' OR Extension = '.webp').
5. Return ONLY the single raw SQL WHERE condition text. NO extra comments, NO follow-thru text, NO markdown, NO semicolons, NO 'Query:' / 'Output:' tags.

Examples:
Query: "find Blade Runner 2049 mkv video files"
Output: FileName LIKE '%Blade%Runner%' AND Extension = '.mkv'

Query: "show me all pdf or word documents"
Output: Extension = '.pdf' OR Extension = '.docx' OR Extension = '.doc'

Query: "find large zip or rar files"
Output: (Extension = '.zip' OR Extension = '.rar') AND FileSizeBytes > 10485760

Query: "find dark souls knight cathedral wallpaper cover"
Output: (FileName LIKE '%Dark%Souls%' OR FileName LIKE '%wallpaper%' OR FileName LIKE '%knight%' OR FileName LIKE '%cathedral%') AND (Extension = '.jpg' OR Extension = '.png' OR Extension = '.jpeg' OR Extension = '.webp')
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

        # Clean AI response: Remove markdown, extra comments, and unwanted prefixes
        where_clause = re.sub(r'```sql|```', '', where_clause, flags=re.IGNORECASE).strip()
        where_clause = re.sub(r'^\s*WHERE\s+', '', where_clause, flags=re.IGNORECASE).strip()
        where_clause = re.split(r'---|\n|Query:|Output:', where_clause, flags=re.IGNORECASE)[0].strip() # Take only the first valid clause line

        # Remove trailing semicolons and replace internal semicolons with ' AND '
        where_clause = where_clause.rstrip(';').strip()
        where_clause = re.sub(r'\s*;\s*', ' AND ', where_clause)

        # Connect to SQLite Database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Determine table name dynamically
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        table_name = "Files" if "Files" in tables else ("IndexedFiles" if "IndexedFiles" in tables else tables[0])

        sql = f"SELECT FileName, FullPath, FileSizeBytes, Extension FROM {table_name} WHERE {where_clause} LIMIT 10;"
        print(f"Executing SQL: {sql}\n")
        
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()

        return results

    except Exception as e:
        print(f"Error executing AI Agent Search: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "find Blade Runner 2049 mkv video files"

    print(f"User Query: '{prompt}'")
    results = query_files_with_ai(prompt)
    
    print(f"--- Search Results ({len(results)}) ---")
    for row in results:
        print(f"File: {row[0]} | Path: {row[1]} | Size: {round(row[2]/1024/1024, 2)} MB | Extension: {row[3]}")