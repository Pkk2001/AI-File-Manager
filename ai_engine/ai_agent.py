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

CRITICAL RULES FOR SQL GENERATION:
1. ONLY use the available columns: FileName, FullPath, Extension, FileSizeBytes.
2. DO NOT use 'Category' or any non-existent columns.
3. Extension values MUST start with a dot (e.g., '.mkv', '.mp4', '.pdf', '.zip', '.rar', '.jpg', '.png').
4. WILDCARDS: Always wrap keywords with '%' on BOTH sides (e.g., `FileName LIKE '%minecraft%'` or `FullPath LIKE '%minecraft%'`). NEVER use single-sided wildcards like `'minecraft%'`.
5. KEYWORD MATCHING: Match keywords against BOTH `FileName` and `FullPath` using `(FileName LIKE '%term%' OR FullPath LIKE '%term%')` because folder names in `FullPath` often contain key context.
6. NO DUMMY PATHS: DO NOT generate imaginary or dummy file paths (such as `/path/to/...`, `/home/...`, or `C:\\...`) in `FullPath`. Only search for path keywords if specified by the user.
7. NO ASSUMED FILE SIZES: DO NOT filter by `FileSizeBytes` unless the user explicitly specifies size constraints (e.g., "larger than 10MB", "less than 1GB"). Never invent size boundaries like `FileSizeBytes < 104857600`.
8. MULTIPLE EXTENSIONS: When filtering extensions alongside keyword searches, ALWAYS wrap multiple extension ORs in parentheses, e.g.: (Extension = '.jpg' OR Extension = '.png' OR Extension = '.jpeg').
9. OUTPUT FORMAT: Return ONLY the single raw SQL WHERE condition text. NO extra comments, NO markdown formatting (no ```sql), NO semicolons, NO 'Query:' / 'Output:' tags.

Examples:
Query: "find minecraft save file"
Output: (FileName LIKE '%minecraft%' OR FullPath LIKE '%minecraft%') AND (FileName LIKE '%save%' OR FullPath LIKE '%save%')

Query: "find Blade Runner 2049 mkv video files"
Output: (FileName LIKE '%Blade%' OR FullPath LIKE '%Blade%') AND (FileName LIKE '%Runner%' OR FullPath LIKE '%Runner%') AND Extension = '.mkv'

Query: "show me all pdf or word documents"
Output: Extension = '.pdf' OR Extension = '.docx' OR Extension = '.doc'

Query: "find zip files in Downloads folder"
Output: Extension = '.zip' AND FullPath LIKE '%Downloads%'

Query: "find video files larger than 500MB"
Output: (Extension = '.mp4' OR Extension = '.mkv' OR Extension = '.avi') AND FileSizeBytes > 524288000
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

        # Remove dummy path clauses if present (e.g., /path/to/..., /home/...)
        where_clause = re.sub(r'\s*AND\s+FullPath\s+LIKE\s+[\'"]%?/(path|home|example)/[^\'"]*[\'"]', '', where_clause, flags=re.IGNORECASE)
        where_clause = re.sub(r'FullPath\s+LIKE\s+[\'"]%?/(path|home|example)/[^\'"]*[\'"]\s*AND\s*', '', where_clause, flags=re.IGNORECASE)

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