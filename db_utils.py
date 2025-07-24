import sqlite3
import re
from datetime import datetime

def initialize_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create textbooks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS textbooks (
        textbook_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT, grade TEXT, language TEXT, title TEXT,
        publisher TEXT, year TEXT, source_file TEXT,
        created_at TEXT, updated_at TEXT
    )
    """)

    # Create units table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS units (
        unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        textbook_id INTEGER, unit_number INTEGER,
        unit_title TEXT, unit_description TEXT
    )
    """)

    # Create content table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS content (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_id INTEGER, content_type TEXT, text_content TEXT,
        is_active INTEGER, created_at TEXT, updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def parse_markdown_to_structure(markdown_text):
    lines = markdown_text.splitlines()
    current_unit = None
    current_chapter = None

    for line in lines:
        line = line.strip()

        if line.startswith("# Unit"):
            match = re.match(r"# Unit (\d+): (.+)", line)
            if match:
                unit_number = int(match.group(1))
                unit_title = match.group(2)
                current_unit = {
                    "unit_number": unit_number,
                    "unit_title": unit_title,
                    "chapters": []
                }

        elif line.startswith("## Chapter"):
            match = re.match(r"## Chapter (\d+): (.+)", line)
            if match and current_unit:
                current_chapter = {
                    "chapter_title": match.group(2),
                    "content_blocks": []
                }
                current_unit["chapters"].append(current_chapter)

        elif line.startswith("###"):
            section_title = line.replace("###", "").strip()
            if current_chapter:
                current_chapter["content_blocks"].append({
                    "section": section_title,
                    "text": ""
                })

        elif line:  # append lines to the last content block
            if current_chapter and current_chapter["content_blocks"]:
                current_chapter["content_blocks"][-1]["text"] += line + "\n"

    return current_unit


def save_textbook_content_to_db(db_path, metadata, parsed_unit):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    # Save textbook
    cursor.execute("""
        INSERT INTO textbooks (subject, grade, language, title, publisher, year, source_file, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (metadata['subject'], metadata['grade'], metadata['language'], metadata['title'], metadata['publisher'],
          metadata.get('year'), metadata.get('source_file'), now, now))
    textbook_id = cursor.lastrowid

    # Save unit
    cursor.execute("""
        INSERT INTO units (textbook_id, unit_number, unit_title, unit_description)
        VALUES (?, ?, ?, ?)
    """, (textbook_id, parsed_unit['unit_number'], parsed_unit['unit_title'], parsed_unit['unit_title']))
    unit_id = cursor.lastrowid

    # Save content blocks
    for chapter in parsed_unit['chapters']:
        for block in chapter['content_blocks']:
            cursor.execute("""
                INSERT INTO content (
                    unit_id, content_type, text_content,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (unit_id, block['section'], block['text'].strip(), 1, now, now))

    conn.commit()
    conn.close()

    return textbook_id, unit_id
