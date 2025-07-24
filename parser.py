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

    # Updated regex to match various header formats
    unit_pattern = re.compile(
        r"^(?:(?:Unit|Lesson|Chapter|Section)\s+(?:\d+|[A-Za-z]+)\s*[:\-\.]?\s*(.*?)$|"  # Unit 1, Chapter One, etc.
        r"^(?:\d+\.?\s*(.*?)$)|"  # 1. Introduction, 2 Title
        r"^(#+\s*(.*?)$))",  # Markdown headers like # Introduction
        re.IGNORECASE | re.MULTILINE
    )

    units = []
    current_unit = None
    current_content = []

    lines = markdown_text.splitlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        match = unit_pattern.match(line)
        if match:
            # Extract the matched groups (one of the three patterns)
            matched_groups = [g for g in match.groups() if g is not None]
            if len(matched_groups) >= 2:
                unit_number = matched_groups[-2]  # Number or word (e.g., "1" or "One")
                unit_title = matched_groups[-1].strip() or "Untitled"  # Title
            else:
                unit_number = str(len(units) + 1)  # Fallback: assign sequential number
                unit_title = matched_groups[-1].strip() or "Untitled"

            # Save previous unit
            if current_unit:
                current_unit["content"] = "\n".join(current_content).strip()
                if current_unit["content"]:
                    units.append(current_unit)

            # Start new unit
            current_unit = {"unit_number": unit_number, "unit_title": unit_title}
            current_content = []
        elif current_unit:
            current_content.append(line)

    # Save last unit
    if current_unit:
        current_unit["content"] = "\n".join(current_content).strip()
        if current_unit["content"]:
            units.append(current_unit)

    logger.debug(f"Parsed units: {units}")
    return units