import re

def parse_markdown_to_units(markdown_text):
    """
    Splits markdown text into units (chapters/lessons), extracting headers.
    Returns a list of dicts: {unit_number, unit_title, content}
    """
    unit_pattern = re.compile(r"(?:Unit|Lesson|Chapter)\s+(\d+)\s*[:\-\.]?\s*(.*)", re.IGNORECASE)

    units = []
    current_unit = None
    current_content = []

    for line in markdown_text.splitlines():
        match = unit_pattern.match(line.strip())
        if match:
            # Save previous unit
            if current_unit:
                current_unit["content"] = "\n".join(current_content).strip()
                units.append(current_unit)

            # Start new unit
            unit_number = match.group(1)
            unit_title = match.group(2).strip()
            current_unit = {"unit_number": unit_number, "unit_title": unit_title}
            current_content = []

        elif current_unit:
            current_content.append(line)

    # Save last unit
    if current_unit:
        current_unit["content"] = "\n".join(current_content).strip()
        units.append(current_unit)

    return units
