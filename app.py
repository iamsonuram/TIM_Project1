import streamlit as st
from db.database import init_db, SessionLocal
from db.models import Textbook, Content, Unit
from ocr_utils import extract_text, extract_metadata_from_text, extract_relevant_textbook_content
from parser import parse_markdown_to_units
import datetime

init_db()

st.title("📘 PDF Textbook OCR App")
st.markdown("Upload a textbook PDF, extract content using Mistral OCR, and store in the database.")

file = st.file_uploader("Upload a PDF file", type=["pdf"])

# Initialize session state if not already
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = None
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
        # Extract raw OCR text from PDF
        markdown_raw = extract_text(file)

        # Step 1.1: Use full raw OCR to detect metadata
        metadata = extract_metadata_from_text(markdown_raw)

        # Step 1.2: Use LLM to extract only textbook content (skip preface/index/etc.)
        filtered_markdown = extract_relevant_textbook_content(markdown_raw)

        # Step 1.3: Store in session for use later
        st.session_state.ocr_text = filtered_markdown
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
            units = parse_markdown_to_units(st.session_state.ocr_text)
            content_blocks = parse_markdown_to_units(st.session_state.ocr_text)
            
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

            for unit in units:
                new_unit = Unit(
                    textbook_id=new_book.textbook_id,
                    unit_number=int(unit["unit_number"]),
                    unit_title=unit["unit_title"],
                    unit_description=None
                )
                db.add(new_unit)
                db.commit()
                db.refresh(new_unit)

                content = Content(
                    unit_id=new_unit.unit_id,
                    content_type="paragraph",
                    text_content=unit["content"],
                    is_active=True
                )
                db.add(content)

            db.commit()
            db.close()

            st.success("✅ Textbook content saved to database!")

            st.markdown("### Extracted Text")
            st.text_area("OCR Text", st.session_state.ocr_text, height=300)
