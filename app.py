import streamlit as st
from db.database import init_db, SessionLocal
from db.models import Textbook, Content, Unit, Chapter
from ocr_utils import extract_text, extract_metadata_from_text, extract_relevant_textbook_content, classify_content_type
from parser import parse_markdown_to_units
import datetime
import re

# Initialize the database
init_db()

st.title("📘 PDF Textbook OCR App")
st.markdown("Upload a textbook PDF, extract content using Mistral OCR, and store in the database.")

file = st.file_uploader("Upload a PDF file", type=["pdf"])

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

def clean_surrogates(text) -> str:
    if not isinstance(text, str):
        return str(text)
    return text.encode('utf-16', 'surrogatepass').decode('utf-16', 'ignore')

if file and st.session_state.ocr_text is None:
    with st.spinner("Running OCR and extracting metadata..."):
        try:
            markdown_raw = extract_text(file)
            print("\n🟡 Raw OCR text extracted.")

            metadata = extract_metadata_from_text(markdown_raw)
            print("\n🟡 Metadata extracted:", metadata)

            filtered_markdown = extract_relevant_textbook_content(markdown_raw)
            print("\n🟡 Filtered markdown extracted.")

            st.session_state.ocr_text = filtered_markdown
            st.session_state.metadata = metadata

        except Exception as e:
            st.error(f"Error during OCR or metadata extraction: {str(e)}")
            st.session_state.ocr_text = None
            st.stop()

if st.session_state.ocr_text:
    title = st.text_input("Title", value=st.session_state.metadata.get("title", ""))
    subject = st.text_input("Subject", value=st.session_state.metadata.get("subject", ""))
    grade = st.text_input("Grade", value=st.session_state.metadata.get("grade", ""))
    language = st.text_input("Language", value=st.session_state.metadata.get("language", ""))
    publisher = st.text_input("Publisher", value=st.session_state.metadata.get("publisher", ""))
    year = st.text_input("Year", value=st.session_state.metadata.get("year", ""))

    if st.button("Extract and Save"):
        with st.spinner("Parsing content and saving to database..."):
            try:
                year_int = None
                if year.strip():
                    try:
                        year_int = int(year)
                    except ValueError:
                        st.error("Year must be a valid number.")
                        st.stop()

                parsed_units = parse_markdown_to_units(st.session_state.ocr_text)
                if not parsed_units or not isinstance(parsed_units, list):
                    st.error("Parsed content is empty or malformed. Please check your OCR input.")
                    st.stop()

                db = SessionLocal()
                new_book = Textbook(
                    subject=clean_surrogates(subject),
                    grade=clean_surrogates(grade),
                    language=clean_surrogates(language),
                    title=clean_surrogates(title),
                    publisher=clean_surrogates(publisher),
                    year=year_int,
                    source_file=clean_surrogates(file.name),
                    created_at=datetime.datetime.now()
                )
                db.add(new_book)
                db.commit()
                db.refresh(new_book)

                for unit in parsed_units:
                    if not unit:
                        continue

                    new_unit = Unit(
                        textbook_id=new_book.textbook_id,
                        unit_number=clean_surrogates(unit.get("unit_number", "")),
                        unit_title=clean_surrogates(unit.get("unit_title", "")), 
                        unit_description=None
                    )
                    db.add(new_unit)
                    db.commit()
                    db.refresh(new_unit)

                    for chapter in unit.get("chapters", []):
                        if not chapter:
                            continue

                        new_chapter = Chapter(
                            unit_id=new_unit.unit_id,
                            chapter_number=clean_surrogates(chapter.get("chapter_number", "1")),
                            chapter_title=clean_surrogates(chapter.get("chapter_title", "Untitled")),
                            chapter_description=None
                        )
                        db.add(new_chapter)
                        db.commit()
                        db.refresh(new_chapter)

                        for block in chapter.get("content_blocks", []):
                            if not block:
                                continue

                            full_content = clean_surrogates(block.get("content", ""))
                            heading = clean_surrogates(block.get("heading", ""))

                            sub_blocks = re.split(r"(?=\*\*Note|\*\*Activity|\*\*Let’s Do|\*\*Let’s Write|\*\*Exercise|\*\*Poem|\*\*Story)", full_content.strip(), flags=re.IGNORECASE)
                            for sub_content in sub_blocks:
                                sub_content = sub_content.strip()
                                if not sub_content:
                                    continue

                                content_type = classify_content_type(sub_content)

                            content_text = clean_surrogates(block.get("content", ""))
                            activity_heading = clean_surrogates(block.get("heading", ""))
                            content_type = classify_content_type(content_text)

                            content = Content(
                                chapter_id=new_chapter.chapter_id,
                                content_type=content_type,
                                text_content=content_text,
                                activity_description=activity_heading,
                                is_active=True,
                                created_at=datetime.datetime.now()
                            )
                            db.add(content)
                db.commit()
                db.close()

                st.markdown("### Extracted Text")
                st.text_area("OCR Text", st.session_state.ocr_text, height=300)

            except Exception as e:
                st.error(f"Error during parsing or saving: {str(e)}")