import sqlite3
import os
import json
import ollama # pyrefly: ignore [missing-import]

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "FileManager.Core", "files.db")

SYSTEM_PROMPT = """
You are an AI File Manager Search Agent. Your job is to convert natural language queries into a SQL WHERE clause for SQLite.
The database table is named `IndexedFiles` with columns:
- FileName (TEXT)
- FilePath (TEXT)
- Extension (TEXT, e.g., '.mp4', '.pdf', '.zip')
- FileSizeBytes (INTEGER)
- CreatedDate (TEXT, ISO format)
- ModifiedDate (TEXT, ISO format)
- Category (TEXT, e.g., 'Videos', 'Documents', 'Archives', 'Images')

Respond ONLY with a valid JSON object with a single key "where_clause". Do NOT include markdown code blocks, explanations, or any extra text.

Examples:
Query: "find large zip files downloaded recently"
JSON: {"where_clause": "Category = 'Archives' AND FileSizeBytes > 104857600 ORDER BY ModifiedDate DESC"}

Query: "show me videos"
JSON: {"where_clause": "Category = 'Videos'"}
"""

def query_files_with_ai(user_prompt, model_name="phi3"):
    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        content = response['message']['content'].strip()
        print(f"AI LLM Response: {content}")

        # Parse JSON
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(content)
        where_clause = data.get("where_clause", "")

        # Execute Query on SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        sql = f"SELECT FileName, FilePath, FileSizeBytes, Category FROM IndexedFiles WHERE {where_clause} LIMIT 10;"
        print(f"Executing SQL: {sql}")
        
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()

        return results

    except Exception as e:
        print(f"Error executing AI Agent Search: {e}")
        return []

if __name__ == "__main__":
    prompt = "find large zip or rar files"
    print(f"\nUser Query: '{prompt}'")
    results = query_files_with_ai(prompt)
    
    print(f"\n--- Search Results ({len(results)}) ---")
    for row in results:
        print(f"File: {row[0]} | Path: {row[1]} | Category: {row[3]}")