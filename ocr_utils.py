import os
import base64
from io import BytesIO
from mistralai import Mistral
from PIL import Image
from dotenv import load_dotenv
import json

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

def extract_text_and_images(file):
    filename = file.name
    extension = os.path.splitext(filename)[1].lower()
    if extension not in VALID_EXTENSIONS:
        return None, []

    if extension == ".pdf":
        content = file.read()
        signed_url = upload_pdf(content, filename)
        ocr_result = process_ocr(signed_url)
        markdown_text = "\n\n".join(page.markdown for page in ocr_result.pages)

        images = []
        for page in ocr_result.pages:
            for img in page.images:
                if img.image_base64:
                    image_data = base64.b64decode(img.image_base64.split(",")[-1])
                    images.append(Image.open(BytesIO(image_data)))

        return markdown_text.strip(), images

    return None, []


def extract_metadata_from_text(markdown_text):
    api_key = os.getenv("MISTRAL_API_KEY")
    model = "mistral-medium"  # or "mistral-large-latest" if you have access

    client = Mistral(api_key=api_key)

    prompt = f"""
You are an expert at reading school textbooks. Based on the content below, extract the following metadata:

- title
- subject
- grade
- language
- publisher
- year

Strictly respond in JSON format like:
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
        content = response.choices[0].message.content.strip()
        return json.loads(content)

    except Exception as e:
        print(f"[Metadata LLM Error] {e}")
        return {
            "title": "", "subject": "", "grade": "",
            "language": "", "publisher": "", "year": ""
        }