import pytest
import os
from src.db import init_db, SessionLocal, add_student, add_exam, add_mark, get_student_name, get_mark_obtained, DB_PATH
from src.crypto import derive_key_from_password

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Ensure we start with a clean DB for tests
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            pass
    init_db()
    yield
    # Cleanup after tests
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            pass

def test_db_operations():
    session = SessionLocal()
    key, _ = derive_key_from_password("test_pass")
    
    # 1. Test adding student
    name = "Test Student"
    student = add_student(session, name, key)
    assert student.id is not None
    assert get_student_name(session, student.id, key) == name
    
    # 2. Test adding exam
    exam_type = "midterm"
    exam = add_exam(session, exam_type)
    assert exam.id is not None
    
    # 3. Test adding and retrieving mark
    subject = "Math"
    obtained = 75
    total = 80
    mark = add_mark(session, student.id, exam.id, subject, obtained, total, key)
    assert mark.id is not None
    assert get_mark_obtained(session, mark.id, key) == obtained
    
    session.close()
