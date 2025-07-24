import os
import base64
from io import BytesIO
from mistralai import Mistral
from PIL import Image
from dotenv import load_dotenv
import json
import re
import fitz  # from PyMuPDF
import logging

logger = logging.getLogger(__name__)

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

VALID_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

def upload_pdf(content, filename):
    client = Mistral(api_key=MISTRAL_API_KEY)
    try:
        uploaded = client.files.upload(file={"file_name": filename, "content": content}, purpose="ocr")
        signed_url = client.files.get_signed_url(file_id=uploaded.id)
        return signed_url.url
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise

def process_ocr(document_url):
    client = Mistral(api_key=MISTRAL_API_KEY)
    try:
        return client.ocr.process(model="mistral-ocr-2505", document={"type": "document_url", "document_url": document_url}, include_image_base64=True)
    except Exception as e:
        logger.error(f"Error processing OCR: {str(e)}")
        raise

def extract_text(file) -> str:
    try:
        # Try PyMuPDF first for text-based PDFs
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in pdf])
        logger.debug(f"PyMuPDF extracted text length: {len(text)}")

        # If little or no text is extracted, assume image-based PDF and use Mistral OCR
        if len(text.strip()) < 100:  # Arbitrary threshold
            logger.info("Minimal text detected, switching to Mistral OCR")
            file.seek(0)  # Reset file pointer
            content = file.read()
            document_url = upload_pdf(content, file.name)
            ocr_result = process_ocr(document_url)
            text = ocr_result.text if hasattr(ocr_result, 'text') else ""
            logger.debug(f"Mistral OCR extracted text length: {len(text)}")

        return text
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise

def extract_metadata_from_text(markdown_text):
    api_key = os.getenv("MISTRAL_API_KEY")
    model = "mistral-medium-2505"

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
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)

    except Exception as e:
        logger.error(f"Metadata LLM Error: {str(e)}")
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
        filtered_text = response.choices[0].message.content.strip()
        logger.debug(f"Filtered content length: {len(filtered_text)}")
        return filtered_text
        
    except Exception as e:
        logger.error(f"LLM Filtering Error: {str(e)}")
        return ocr_text
        
