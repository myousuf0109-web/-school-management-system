"""
Database layer for the Student Management System.
Uses SQLite (single file, zero setup). All access goes through this module.
"""
import sqlite3
import bcrypt
from datetime import date
from contextlib import contextmanager

DB_PATH = "sms.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def check_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','teacher','student')),
    linked_id INTEGER  -- FK to teachers.id or students.id depending on role
);

CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    teacher_id INTEGER REFERENCES teachers(id)
);

CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT,
    contact TEXT,
    monthly_salary REAL DEFAULT 0,
    joined_date TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    class_id INTEGER REFERENCES classes(id),
    teacher_id INTEGER REFERENCES teachers(id)
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    class_id INTEGER REFERENCES classes(id),
    admission_date TEXT,
    contact TEXT,
    guardian_name TEXT,
    total_fee REAL DEFAULT 0,
    fee_paid REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fee_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id),
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id),
    att_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('present','absent','leave')),
    UNIQUE(student_id, att_date)
);

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id),
    course_id INTEGER REFERENCES courses(id),
    exam_name TEXT NOT NULL,
    marks REAL NOT NULL,
    max_marks REAL NOT NULL DEFAULT 100,
    exam_date TEXT
);

CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    entry_type TEXT CHECK(entry_type IN ('income','expense')),
    amount REAL NOT NULL,
    entry_date TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS teacher_salary_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER REFERENCES teachers(id),
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    posted_by TEXT,
    posted_date TEXT NOT NULL
);
"""


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # seed only if empty
        cur = conn.execute("SELECT COUNT(*) c FROM users")
        if cur.fetchone()["c"] == 0:
            seed(conn)


def seed(conn):
    today = date.today().isoformat()

    # Admin
    conn.execute(
        "INSERT INTO users(username,password_hash,role,linked_id) VALUES (?,?,?,?)",
        ("admin", hash_pw("admin123"), "admin", None),
    )

    # Teachers
    teachers = [
        ("Mr. Ahsan Raza", "Mathematics", "0300-1111111", 60000),
        ("Ms. Sara Khan", "English", "0300-2222222", 55000),
        ("Mr. Bilal Ahmed", "Physics", "0300-3333333", 58000),
    ]
    teacher_ids = []
    for name, subj, contact, salary in teachers:
        cur = conn.execute(
            "INSERT INTO teachers(name,subject,contact,monthly_salary,joined_date) VALUES (?,?,?,?,?)",
            (name, subj, contact, salary, today),
        )
        tid = cur.lastrowid
        teacher_ids.append(tid)
        uname = name.lower().split()[1] if len(name.split()) > 1 else name.lower()
        conn.execute(
            "INSERT INTO users(username,password_hash,role,linked_id) VALUES (?,?,?,?)",
            (uname, hash_pw("teacher123"), "teacher", tid),
        )

    # Classes
    classes = [("Class 9-A", teacher_ids[0]), ("Class 10-B", teacher_ids[1])]
    class_ids = []
    for name, tid in classes:
        cur = conn.execute("INSERT INTO classes(name,teacher_id) VALUES (?,?)", (name, tid))
        class_ids.append(cur.lastrowid)

    # Courses
    courses = [
        ("Mathematics", class_ids[0], teacher_ids[0]),
        ("Physics", class_ids[0], teacher_ids[2]),
        ("English", class_ids[1], teacher_ids[1]),
    ]
    course_ids = []
    for name, cid, tid in courses:
        cur = conn.execute(
            "INSERT INTO courses(name,class_id,teacher_id) VALUES (?,?,?)", (name, cid, tid)
        )
        course_ids.append(cur.lastrowid)

    # Students
    students = [
        ("Ali Hassan", class_ids[0], "0301-1111111", "Hassan Sr.", 50000, 50000),
        ("Fatima Noor", class_ids[0], "0301-2222222", "Noor Sr.", 50000, 20000),
        ("Zainab Iqbal", class_ids[1], "0301-3333333", "Iqbal Sr.", 45000, 45000),
        ("Usman Tariq", class_ids[1], "0301-4444444", "Tariq Sr.", 45000, 0),
    ]
    student_ids = []
    for name, cid, contact, guardian, total, paid in students:
        cur = conn.execute(
            """INSERT INTO students(name,class_id,admission_date,contact,guardian_name,total_fee,fee_paid)
               VALUES (?,?,?,?,?,?,?)""",
            (name, cid, today, contact, guardian, total, paid),
        )
        sid = cur.lastrowid
        student_ids.append(sid)
        uname = name.lower().split()[0]
        conn.execute(
            "INSERT INTO users(username,password_hash,role,linked_id) VALUES (?,?,?,?)",
            (uname, hash_pw("student123"), "student", sid),
        )
        if paid > 0:
            conn.execute(
                "INSERT INTO fee_payments(student_id,amount,payment_date,note) VALUES (?,?,?,?)",
                (sid, paid, today, "Initial payment"),
            )

    # Grades (sample)
    sample_grades = [
        (student_ids[0], course_ids[0], "Midterm", 85, 100),
        (student_ids[0], course_ids[1], "Midterm", 78, 100),
        (student_ids[1], course_ids[0], "Midterm", 92, 100),
        (student_ids[1], course_ids[1], "Midterm", 88, 100),
        (student_ids[2], course_ids[2], "Midterm", 74, 100),
        (student_ids[3], course_ids[2], "Midterm", 65, 100),
    ]
    for sid, cid, exam, marks, maxm in sample_grades:
        conn.execute(
            "INSERT INTO grades(student_id,course_id,exam_name,marks,max_marks,exam_date) VALUES (?,?,?,?,?,?)",
            (sid, cid, exam, marks, maxm, today),
        )

    # Attendance (sample)
    for sid in student_ids:
        conn.execute(
            "INSERT OR IGNORE INTO attendance(student_id,att_date,status) VALUES (?,?,?)",
            (sid, today, "present"),
        )

    # Budget
    budget_entries = [
        ("Tuition Fees", "income", 115000, "Term fee collection"),
        ("Admission Fees", "income", 20000, "New admissions"),
        ("Teacher Salaries", "expense", 173000, "Monthly payroll"),
        ("Utilities", "expense", 15000, "Electricity & water"),
        ("Maintenance", "expense", 8000, "Building upkeep"),
    ]
    for cat, etype, amt, note in budget_entries:
        conn.execute(
            "INSERT INTO budget(category,entry_type,amount,entry_date,note) VALUES (?,?,?,?,?)",
            (cat, etype, amt, today, note),
        )

    # Notices
    conn.execute(
        "INSERT INTO notices(title,content,posted_by,posted_date) VALUES (?,?,?,?)",
        ("Welcome!", "Welcome to the new term. Check your dashboard for updates.", "admin", today),
    )


def get_user(username):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(row) if row else None
