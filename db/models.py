from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Textbook(Base):
    __tablename__ = "textbooks"
    textbook_id = Column(Integer, primary_key=True)
    subject = Column(String)
    grade = Column(String)
    language = Column(String)
    title = Column(String)
    publisher = Column(String)
    year = Column(Integer)
    source_file = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Unit(Base):
    __tablename__ = "units"
    unit_id = Column(Integer, primary_key=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.textbook_id"))
    unit_number = Column(Integer)
    unit_title = Column(String)
    unit_description = Column(Text)

class Content(Base):
    __tablename__ = "content"
    content_id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.chapter_id"))
    content_type = Column(String)
    text_content = Column(Text)
    question = Column(Text)
    answer = Column(Text)
    activity_description = Column(Text)
    bloom_level = Column(String)
    difficulty_level = Column(String)
    learning_objective = Column(String)
    keywords = Column(String)
    source_page = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Translation(Base):
    __tablename__ = "translations"
    translation_id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey("content.content_id"))
    english_translation = Column(Text)
    transliteration = Column(Text)

class Media(Base):
    __tablename__ = "media"
    media_id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey("content.content_id"))
    media_type = Column(String)
    image_path = Column(String)
    audio_path = Column(String)
    media_description = Column(Text)
    duration = Column(String)

class Chapter(Base):
    __tablename__ = "chapters"
    chapter_id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.unit_id"))
    chapter_number = Column(Integer)
    chapter_title = Column(String)
    chapter_description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

