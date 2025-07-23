import streamlit as st
from db.database import init_db, SessionLocal
from db.models import Textbook, Content
from ocr_utils import extract_text_and_images, extract_metadata_from_text
from parser import parse_markdown_to_content
import datetime

init_db()

st.title("📘 PDF Textbook OCR App")
st.markdown("Upload a textbook PDF, extract content using Mistral OCR, and store in the database.")

file = st.file_uploader("Upload a PDF file", type=["pdf"])

# Initialize session state if not already
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = None
    st.session_state.images = []
    st.session_state.metadata = {
        "title": "",
        "subject": "",
        "grade": "",
        "language": "",
        "publisher": "",
        "year": ""
    }

# Step 1: When file is uploaded, run OCR and metadata
if file and st.session_state.ocr_text is None:
    with st.spinner("Running OCR and extracting metadata..."):
        markdown, images = extract_text_and_images(file)
        metadata = extract_metadata_from_text(markdown)

        st.session_state.ocr_text = markdown
        st.session_state.images = images
        st.session_state.metadata = metadata

# Step 2: Show fields (with editable pre-filled values)
if st.session_state.ocr_text:
    title = st.text_input("Title", value=st.session_state.metadata.get("title", ""))
    subject = st.text_input("Subject", value=st.session_state.metadata.get("subject", ""))
    grade = st.text_input("Grade", value=st.session_state.metadata.get("grade", ""))
    language = st.text_input("Language", value=st.session_state.metadata.get("language", ""))
    publisher = st.text_input("Publisher", value=st.session_state.metadata.get("publisher", ""))
    year = st.text_input("Year", value=st.session_state.metadata.get("year", ""))

    if st.button("Extract and Save"):
        with st.spinner("Parsing content and saving to database..."):
            content_blocks = parse_markdown_to_content(st.session_state.ocr_text)

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

            st.success("✅ Textbook content saved to database!")

            st.markdown("### Extracted Text")
            st.text_area("OCR Text", st.session_state.ocr_text, height=300)

            if st.session_state.images:
                st.markdown("### Extracted Images")
                for img in st.session_state.images:
                    st.image(img)
