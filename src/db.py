import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Path to SQLite DB (placed in project root)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'percent_calc.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False, future=True)
Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name_enc = Column(String, nullable=False)  # encrypted JSON payload
    # Relationship
    marks = relationship('Mark', back_populates='student')

class Exam(Base):
    __tablename__ = 'exams'
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)  # e.g., 'midterm', 'preboard1', ...
    marks = relationship('Mark', back_populates='exam')

class Mark(Base):
    __tablename__ = 'marks'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    exam_id = Column(Integer, ForeignKey('exams.id'), nullable=False)
    subject = Column(String, nullable=False)  # 'Math', 'Science', etc.
    obtained_enc = Column(String, nullable=False)  # encrypted JSON payload (integer as string)
    total = Column(Integer, nullable=False)  # max marks for the subject (80 or 50)
    student = relationship('Student', back_populates='marks')
    exam = relationship('Exam', back_populates='marks')

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

# Helper functions for adding entries (using encryption functions from src.crypto)
from .crypto import encrypt_field, decrypt_field

def add_student(session, name: str, key: bytes):
    encrypted_name = encrypt_field(name, key)
    student = Student(name_enc=encrypted_name)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

def add_exam(session, exam_type: str):
    exam = Exam(type=exam_type)
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam

def add_mark(session, student_id: int, exam_id: int, subject: str, obtained: int, total: int, key: bytes):
    # Store the integer as a string before encryption
    encrypted_obtained = encrypt_field(str(obtained), key)
    mark = Mark(
        student_id=student_id,
        exam_id=exam_id,
        subject=subject,
        obtained_enc=encrypted_obtained,
        total=total,
    )
    session.add(mark)
    session.commit()
    session.refresh(mark)
    return mark

def get_student_name(session, student_id: int, key: bytes) -> str:
    student = session.query(Student).filter_by(id=student_id).first()
    if not student:
        return None
    return decrypt_field(student.name_enc, key)

def get_mark_obtained(session, mark_id: int, key: bytes):
    mark = session.query(Mark).filter_by(id=mark_id).first()
    if not mark:
        return None
    val = float(decrypt_field(mark.obtained_enc, key))
    return int(val) if val.is_integer() else val
