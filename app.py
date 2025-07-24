import streamlit as st
from db.database import init_db, SessionLocal
from db.models import Textbook, Content, Unit
from ocr_utils import extract_text, extract_metadata_from_text, extract_relevant_textbook_content
from parser import parse_markdown_to_units
import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        try:
            # Extract raw OCR text from PDF
            markdown_raw = extract_text(file)
            logger.debug(f"Raw OCR text length: {len(markdown_raw)}")

            # Step 1.1: Use full raw OCR to detect metadata
            metadata = extract_metadata_from_text(markdown_raw)
            logger.debug(f"Extracted metadata: {metadata}")

            # Step 1.2: Use LLM to extract only textbook content
            filtered_markdown = extract_relevant_textbook_content(markdown_raw)
            logger.debug(f"Filtered markdown length: {len(filtered_markdown)}")

            # Step 1.3: Store in session for use later
            st.session_state.ocr_text = filtered_markdown
            st.session_state.metadata = metadata
        except Exception as e:
            st.error(f"Error during OCR or metadata extraction: {str(e)}")
            logger.error(f"OCR/Metadata error: {str(e)}")
            st.session_state.ocr_text = None  # Reset to allow retry
            st.stop()

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
            try:
                # Validate year
                year_int = None
                if year.strip():
                    try:
                        year_int = int(year)
                    except ValueError:
                        st.error("Year must be a valid number.")
                        st.stop()

                # Parse units
                units = parse_markdown_to_units(st.session_state.ocr_text)
                logger.debug(f"Parsed {len(units)} units: {units}")

                if not units:
                    st.error("No units found in the textbook content. Check the OCR output or unit parsing logic.")
                    st.stop()

                # Save to database
                db = SessionLocal()
                try:
                    new_book = Textbook(
                        subject=subject,
                        grade=grade,
                        language=language,
                        title=title,
                        publisher=publisher,
                        year=year_int,
                        source_file=file.name,
                        created_at=datetime.datetime.now()
                    )
                    db.add(new_book)
                    db.commit()
                    db.refresh(new_book)
                    logger.debug(f"Saved textbook: {new_book.textbook_id}")

                    for unit in units:
                        # Validate unit_number
                        try:
                            unit_number = int(unit["unit_number"])
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid unit number: {unit['unit_number']}. Skipping unit.")
                            continue

                        new_unit = Unit(
                            textbook_id=new_book.textbook_id,
                            unit_number=unit_number,
                            unit_title=unit["unit_title"] or "Untitled",
                            unit_description=None
                        )
                        db.add(new_unit)
                        db.commit()
                        db.refresh(new_unit)
                        logger.debug(f"Saved unit: {new_unit.unit_id}")

                        if unit["content"].strip():
                            content = Content(
                                unit_id=new_unit.unit_id,
                                content_type="paragraph",
                                text_content=unit["content"],
                                is_active=True
                            )
                            db.add(content)
                            logger.debug(f"Saved content for unit: {new_unit.unit_id}")
                        else:
                            logger.warning(f"No content for unit {unit_number}. Skipping content save.")

                    db.commit()
                    st.success("✅ Textbook content saved to database!")
                except Exception as e:
                    db.rollback()
                    st.error(f"Database error: {str(e)}")
                    logger.error(f"Database error: {str(e)}")
                finally:
                    db.close()

                st.markdown("### Extracted Text")
                st.text_area("OCR Text", st.session_state.ocr_text, height=300)
            except Exception as e:
                st.error(f"Error during parsing or saving: {str(e)}")
                logger.error(f"Parsing/Saving error: {str(e)}")