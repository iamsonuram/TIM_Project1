import os
import fitz
from mistralai import Mistral
import re, json

from dotenv import load_dotenv
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

def extract_text(file) -> str:
    """
    Extracts raw text from PDF using PyMuPDF.
    """
    try:
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in pdf])
        return text.strip()
    except Exception as e:
        print(f"PDF Extraction Error: {str(e)}")
        return ""

def extract_metadata_from_text(markdown_text: str) -> dict:
    """
    Uses Mistral LLM to extract textbook metadata from OCR text.
    """
    client = Mistral(api_key=MISTRAL_API_KEY)
    prompt = f"""
You are an expert at reading school textbooks. Based on the content below, extract the following metadata:

- title
- subject
- grade
- language
- publisher
- year

Respond ONLY in strict JSON format. Do NOT wrap it in triple backticks or code block.

{{
  "title": "...",
  "subject": "...",
  "grade": "...",
  "language": "...",
  "publisher": "...",
  "year": "..."
}}

OCR Text:
\"\"\"
{markdown_text[:10000]}
\"\"\"
    """

    try:
        response = client.chat.complete(
            model="mistral-small",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        print("\n\n🔵 Mistral Metadata Response:\n", raw)

        # Robust cleanup of triple backticks and `json`
        cleaned = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        print("\n🧼 Cleaned JSON:\n", cleaned)

        return json.loads(cleaned)

    except Exception as e:
        print(f"Metadata extraction failed: {str(e)}")
        return {
            "title": "", "subject": "", "grade": "",
            "language": "", "publisher": "", "year": ""
        }

def extract_relevant_textbook_content(ocr_text: str) -> str:
    """
    Filters OCR text using Mistral LLM to retain relevant textbook content in markdown format.
    """
    client = Mistral(api_key=MISTRAL_API_KEY)
    prompt = f"""
You are a helpful assistant extracting educational content from an OCR dump of a textbook.
Here is the raw OCR text:
{ocr_text}

Your job is to remove irrelevant front-matter like publication info, forewords, acknowledgements, contributor lists, copyright, etc.
Retain all **useful learning content** starting from the first Unit, Chapter, Lesson, or Section header (e.g., "Unit 1: Title", "Chapter 1: Title") onward — including poems, activities, teacher notes, instructions, stories, and their headers.
Return the filtered content in markdown format, wrapped in ```markdown and ``` delimiters.
Use # for unit headers (e.g., # Unit 1: Title), ## for chapter headers (e.g., ## Chapter 1: Title), ### for subheadings, and #### for sub-subheadings.
Preserve all unit and chapter headers exactly as they appear. Include all content under these headers, including poems, lists, and notes.
No extra explanations.
"""

    try:
        response = client.chat.complete(
            model="mistral-medium",
            messages=[{"role": "user", "content": prompt}]
        )
        filtered_text = response.choices[0].message.content.strip()
        print("\n\n🟢 Mistral Filtered Markdown Response:\n", filtered_text[:1000], "...\n[truncated]")
        return filtered_text
    except Exception as e:
        print(f"LLM Filtering Error: {str(e)}")
        return ocr_text