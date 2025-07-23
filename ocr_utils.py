import os
import base64
from io import BytesIO
from mistralai import Mistral
from PIL import Image
from dotenv import load_dotenv
import json
import re
import fitz  # from PyMuPDF

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

VALID_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

def upload_pdf(content, filename):
    client = Mistral(api_key=MISTRAL_API_KEY)
    uploaded = client.files.upload(file={"file_name": filename, "content": content}, purpose="ocr")
    signed_url = client.files.get_signed_url(file_id=uploaded.id)
    return signed_url.url

def process_ocr(document_url):
    client = Mistral(api_key=MISTRAL_API_KEY)
    return client.ocr.process(model="mistral-ocr-2505", document={"type": "document_url", "document_url": document_url}, include_image_base64=True)

# ocr_utils.py
def extract_text(file) -> str:
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in pdf])
    return text

def extract_metadata_from_text(markdown_text):
    api_key = os.getenv("MISTRAL_API_KEY")
    model = "mistral-medium-2505"  # or "mistral-large-latest" if you have access

    client = Mistral(api_key=api_key)

    prompt = f"""
You are an expert at reading school textbooks. Based on the content below, extract the following metadata:

- title
- subject
- grade
- language
- publisher
- year

Respond **only** in this strict JSON format (no explanations):

```json
{{
  "title": "...",
  "subject": "...",
  "grade": "...",
  "language": "...",
  "publisher": "...",
  "year": "..."
}}

Here is the OCR text:
\"\"\"
{markdown_text[:3000]}
\"\"\"
"""

    try:
        response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        raw = response.choices[0].message.content.strip()
        print("🚨 RAW LLM RESPONSE:\n", raw)

        # Remove wrapping triple backticks if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)  # remove opening ```
            raw = re.sub(r"\s*```$", "", raw)           # remove closing ```

        return json.loads(raw)

    except Exception as e:
        print(f"[Metadata LLM Error] {e}")
        return {
            "title": "", "subject": "", "grade": "",
            "language": "", "publisher": "", "year": ""
        }

def extract_relevant_textbook_content(ocr_text: str) -> str:
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    prompt = f"""
You are a helpful assistant extracting educational content from an OCR dump of a textbook.
Here is the raw OCR text:
{ocr_text}
Your job is to remove all irrelevant front-matter like publication info, forewords, acknowledgements, contributor lists, copyright, etc.
Retain only **useful learning content** starting from first Unit/Chapter onward — including poems, activities, teacher notes, instructions, stories.
Return ONLY the filtered content in clear markdown format (e.g., headers, bullet points, etc). No extra explanations.
    """
    try:
        response = client.chat.complete(
            model="mistral-medium",
            messages=[{"role": "user", "content": prompt}]
        )
        r = response.choices[0].message.content.strip()
        print("🚨 RAW LLM RESPONSE:\n", r)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("[LLM Filtering Error]", e)
        return ocr_text  # fallback: return raw OCR
