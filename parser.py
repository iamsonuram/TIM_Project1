def parse_markdown_to_content(markdown_text):
    content_blocks = markdown_text.split("\n\n")
    parsed = []

    for block in content_blocks:
        block = block.strip()
        if block.startswith("Q:") or "?" in block:
            question = block
            answer = ""  # Placeholder
            parsed.append({"type": "qa", "question": question, "answer": answer})
        else:
            parsed.append({"type": "text", "text": block})

    return parsed
