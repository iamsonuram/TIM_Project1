import streamlit as st
from db.database import init_db, SessionLocal
from db.models import Textbook, Content
from ocr_utils import extract_text_and_images, extract_metadata_from_text
from parser import parse_markdown_to_content
import datetime

init_db()

st.title("📘 PDF Textbook OCR App")
st.markdown("Upload a textbook PDF, extract content using Mistral OCR, and store in database.")

file = st.file_uploader("Upload a PDF file", type=["pdf"])

# Only process after upload
if file:
    with st.spinner("Running OCR and extracting metadata..."):
        markdown, images = extract_text_and_images(file)
        metadata = extract_metadata_from_text(markdown)

    # Streamlit editable fields pre-filled
    title = st.text_input("Title", value=metadata.get("title", ""))
    subject = st.text_input("Subject", value=metadata.get("subject", ""))
    grade = st.text_input("Grade", value=metadata.get("grade", ""))
    language = st.text_input("Language", value=metadata.get("language", ""))
    publisher = st.text_input("Publisher", value=metadata.get("publisher", ""))
    year = st.text_input("Year", value=metadata.get("year", ""))

    if st.button("Extract and Save"):
        with st.spinner("Parsing content and saving to database..."):
            content_blocks = parse_markdown_to_content(markdown)

            db = SessionLocal()
            new_book = Textbook(
                subject=subject,
                grade=grade,
                language=language,
                title=title,
                publisher=publisher,
                year=int(year) if year else None,
                source_file=file.name,
                created_at=datetime.datetime.now()
            )
            db.add(new_book)
            db.commit()
            db.refresh(new_book)

            for block in content_blocks:
                content = Content(
                    unit_id=None,
                    content_type=block["type"],
                    text_content=block.get("text", ""),
                    question=block.get("question", ""),
                    answer=block.get("answer", ""),
                    is_active=True
                )
                db.add(content)

            db.commit()
            db.close()

            st.success("Textbook content saved successfully!")

            st.markdown("### Extracted Text")
            st.text_area("OCR Text", markdown, height=300)

            if images:
                st.markdown("### Extracted Images")
                for img in images:
                    st.image(img)
