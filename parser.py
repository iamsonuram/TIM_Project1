import re
import logging

logger = logging.getLogger(__name__)

def parse_markdown_to_units(markdown_text):
    """
    Splits markdown text into units (chapters/lessons), extracting headers.
    Returns a list of dicts: {unit_number, unit_title, content}
    """
    # Save markdown_text to a file for debugging
    with open("filtered_markdown.txt", "w", encoding="utf-8") as f:
        f.write(markdown_text)
    logger.debug("Saved filtered markdown to filtered_markdown.txt")

    markdown_text = markdown_text.strip()
    if markdown_text.startswith("```markdown"):
        markdown_text = markdown_text[len("```markdown"):].strip()
    if markdown_text.endswith("```"):
        markdown_text = markdown_text[:-3].strip()

    # Updated regex to match various header formats
    unit_pattern = re.compile(r"# Unit\s+(\d+)\s*[:\-\.]?\s*(.*)", re.IGNORECASE)
    chapter_pattern = re.compile(r"## Chapter\s+(\d+)\s*[:\-\.]?\s*(.*)", re.IGNORECASE)
    heading_pattern = re.compile(r"###\s+(.*)")

    units = []
    current_unit = None
    current_chapter = None
    current_heading = None
    current_content_lines = []

    def save_block():
        if current_heading and current_content_lines:
            block = {
                "heading": current_heading,
                "content": "\n".join(current_content_lines).strip()
            }
            current_chapter["content_blocks"].append(block)

    for line in markdown_text.splitlines():
        line = line.strip()
        if not line:
            continue

        unit_match = unit_pattern.match(line)
        chapter_match = chapter_pattern.match(line)
        heading_match = heading_pattern.match(line)

        if unit_match:
            # Save previous heading
            if current_chapter:
                save_block()
            if current_unit:
                if current_chapter:
                    current_unit["chapters"].append(current_chapter)
                units.append(current_unit)

            # Start new unit
            current_unit = {
                "unit_number": int(unit_match.group(1)),
                "unit_title": unit_match.group(2).strip(),
                "chapters": []
            }
            current_chapter = None
            current_heading = None
            current_content_lines = []

        elif chapter_match:
            if current_chapter:
                save_block()
                current_unit["chapters"].append(current_chapter)

            current_chapter = {
                "chapter_number": int(chapter_match.group(1)),
                "chapter_title": chapter_match.group(2).strip(),
                "content_blocks": []
            }
            current_heading = None
            current_content_lines = []

        elif heading_match:
            save_block()
            current_heading = heading_match.group(1).strip()
            current_content_lines = []

        else:
            current_content_lines.append(line)

    # Save last parts
    if current_chapter:
        save_block()
        current_unit["chapters"].append(current_chapter)
    if current_unit:
        units.append(current_unit)

    return units