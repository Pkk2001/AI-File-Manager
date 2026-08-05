import sqlite3
import os

# Database Path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "FileManager.Core", "files.db")

# Category Rule Mapping based on Extensions
CATEGORY_MAP = {
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.pptx', '.csv'],
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'],
    'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.flv'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Source Code': ['.cs', '.js', '.ts', '.py', '.html', '.css', '.json', '.cpp', '.java'],
    'Executable/Apps': ['.exe', '.msi', '.apk']
}

def get_category(extension):
    ext = extension.lower()
    for category, extensions in CATEGORY_MAP.items():
        if ext in extensions:
            return category
    return 'Other'

def categorize_indexed_files():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all uncategorized files or all files
    cursor.execute("SELECT Id, Extension FROM IndexedFiles")
    rows = cursor.fetchall()

    print(f"Categorizing {len(rows)} files in SQLite Database...")

    updated_count = 0
    for file_id, ext in rows:
        if ext:
            category = get_category(ext)
            cursor.execute("UPDATE IndexedFiles SET Category = ? WHERE Id = ?", (category, file_id))
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Successfully updated categories for {updated_count} files!")

if __name__ == "__main__":
    categorize_indexed_files()