"""SQLite data access for the Student Attendance Management System."""

import hashlib
import hmac
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path


DEFAULT_DATABASE = Path(__file__).resolve().parent / "database" / "attendance.db"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"


def hash_password(password, salt=None):
    """Return a salted PBKDF2 password hash suitable for storing in SQLite."""
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200000
    ).hex()
    return "{}${}".format(salt, digest)


def verify_password(password, stored_hash):
    """Safely compare a password with its stored salted hash."""
    try:
        salt, expected_digest = stored_hash.split("$", 1)
        actual_digest = hash_password(password, salt).split("$", 1)[1]
        return hmac.compare_digest(actual_digest, expected_digest)
    except (AttributeError, ValueError):
        return False


class AttendanceDatabase:
    """Small collection of clear database operations used by the GUI."""

    def __init__(self, database_path=DEFAULT_DATABASE):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS Admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS Students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_number TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    course TEXT NOT NULL,
                    semester TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    password_hash TEXT
                );
                CREATE TABLE IF NOT EXISTS Attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    attendance_date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('Present', 'Absent')),
                    UNIQUE (student_id, attendance_date),
                    FOREIGN KEY (student_id) REFERENCES Students(id)
                        ON DELETE CASCADE
                );
                """
            )
            student_columns = {
                row["name"] for row in
                connection.execute("PRAGMA table_info(Students)").fetchall()
            }
            if "password_hash" not in student_columns:
                connection.execute(
                    "ALTER TABLE Students ADD COLUMN password_hash TEXT"
                )
            admin = connection.execute(
                "SELECT id FROM Admin WHERE username = ?", (DEFAULT_USERNAME,)
            ).fetchone()
            if admin is None:
                connection.execute(
                    "INSERT INTO Admin (username, password_hash) VALUES (?, ?)",
                    (DEFAULT_USERNAME, hash_password(DEFAULT_PASSWORD)),
                )

    def validate_login(self, username, password):
        with self.connect() as connection:
            admin = connection.execute(
                "SELECT password_hash FROM Admin WHERE username = ?", (username,)
            ).fetchone()
        return admin is not None and verify_password(password, admin["password_hash"])

    def validate_student_login(self, roll_number, password):
        with self.connect() as connection:
            student = connection.execute(
                """SELECT id, roll_number, name, course, semester, phone,
                          password_hash
                   FROM Students WHERE roll_number = ?""",
                (roll_number.strip(),),
            ).fetchone()
        if student is None or not verify_password(password, student["password_hash"]):
            return None
        return {key: student[key] for key in
                ("id", "roll_number", "name", "course", "semester", "phone")}

    @staticmethod
    def _validate_date(attendance_date):
        try:
            return date.fromisoformat(attendance_date).isoformat()
        except (TypeError, ValueError):
            raise ValueError("Date must use the YYYY-MM-DD format.")

    @staticmethod
    def _validate_month(month):
        try:
            return datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
        except (TypeError, ValueError):
            raise ValueError("Month must use the YYYY-MM format.")

    @staticmethod
    def _validate_student(roll_number, name, course, semester, phone):
        values = {
            "Roll number": roll_number,
            "Name": name,
            "Course": course,
            "Semester": semester,
            "Phone number": phone,
        }
        for label, value in values.items():
            if not str(value).strip():
                raise ValueError("{} is required.".format(label))

    @staticmethod
    def _hash_student_password(password):
        if not password or not password.strip() or len(password) < 4:
            raise ValueError("Student password must be at least 4 characters.")
        return hash_password(password)

    def add_student(self, roll_number, name, course, semester, phone, password):
        self._validate_student(roll_number, name, course, semester, phone)
        password_hash = self._hash_student_password(password)
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO Students
                   (roll_number, name, course, semester, phone, password_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                tuple(str(value).strip() for value in
                      (roll_number, name, course, semester, phone))
                + (password_hash,),
            )
            return cursor.lastrowid

    def update_student(self, student_id, roll_number, name, course, semester, phone,
                       password=None):
        self._validate_student(roll_number, name, course, semester, phone)
        with self.connect() as connection:
            values = tuple(str(value).strip() for value in
                           (roll_number, name, course, semester, phone))
            if password:
                password_hash = self._hash_student_password(password)
                connection.execute(
                    """UPDATE Students SET roll_number = ?, name = ?, course = ?,
                       semester = ?, phone = ?, password_hash = ? WHERE id = ?""",
                    values + (password_hash, student_id),
                )
            else:
                connection.execute(
                    """UPDATE Students SET roll_number = ?, name = ?, course = ?,
                       semester = ?, phone = ? WHERE id = ?""",
                    values + (student_id,),
                )

    def delete_student(self, student_id):
        with self.connect() as connection:
            connection.execute("DELETE FROM Students WHERE id = ?", (student_id,))

    def get_students(self, search=""):
        search_text = "%{}%".format(search.strip())
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT id, roll_number, name, course, semester, phone
                   FROM Students
                   WHERE roll_number LIKE ? OR name LIKE ?
                   ORDER BY name COLLATE NOCASE""",
                (search_text, search_text),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_student(self, student_id):
        with self.connect() as connection:
            row = connection.execute(
                """SELECT id, roll_number, name, course, semester, phone
                   FROM Students WHERE id = ?""",
                (student_id,),
            ).fetchone()
        return dict(row) if row else None

    def save_attendance(self, attendance_date, attendance_records):
        attendance_date = self._validate_date(attendance_date)
        if not attendance_records:
            raise ValueError("There are no students to save attendance for.")
        for student_id, status in attendance_records.items():
            if status not in ("Present", "Absent"):
                raise ValueError("Choose Present or Absent for every student.")
        with self.connect() as connection:
            for student_id, status in attendance_records.items():
                connection.execute(
                    """INSERT INTO Attendance (student_id, attendance_date, status)
                       VALUES (?, ?, ?)
                       ON CONFLICT(student_id, attendance_date)
                       DO UPDATE SET status = excluded.status""",
                    (student_id, attendance_date, status),
                )

    def get_attendance_for_date(self, attendance_date):
        attendance_date = self._validate_date(attendance_date)
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT s.id, s.roll_number, s.name, s.course, s.semester,
                          a.status
                   FROM Students s
                   LEFT JOIN Attendance a ON a.student_id = s.id
                       AND a.attendance_date = ?
                   ORDER BY s.roll_number COLLATE NOCASE""",
                (attendance_date,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_attendance_records(self, attendance_date=None, month=None, student_id=None):
        query = """SELECT a.id, a.student_id, s.roll_number, s.name, s.course,
                          s.semester, a.attendance_date, a.status
                   FROM Attendance a JOIN Students s ON s.id = a.student_id
                   WHERE 1 = 1"""
        parameters = []
        if attendance_date:
            query += " AND a.attendance_date = ?"
            parameters.append(self._validate_date(attendance_date))
        if month:
            month = self._validate_month(month)
            query += " AND substr(a.attendance_date, 1, 7) = ?"
            parameters.append(month)
        if student_id is not None:
            query += " AND a.student_id = ?"
            parameters.append(student_id)
        query += " ORDER BY a.attendance_date DESC, s.roll_number COLLATE NOCASE"
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def student_report(self, student_id):
        with self.connect() as connection:
            student = connection.execute(
                """SELECT id, roll_number, name, course, semester, phone
                   FROM Students WHERE id = ?""",
                (student_id,),
            ).fetchone()
            totals = connection.execute(
                """SELECT COUNT(*) AS total_classes,
                          SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END)
                              AS present_days
                   FROM Attendance WHERE student_id = ?""",
                (student_id,),
            ).fetchone()
        return self._report_row(dict(student), totals) if student else None

    @staticmethod
    def _report_row(student, totals):
        total = totals["total_classes"] or 0
        present = totals["present_days"] or 0
        student.update(
            total_classes=total,
            present_days=present,
            absent_days=total - present,
            percentage=round((present / total) * 100, 2) if total else 0.0,
        )
        return student

    def attendance_report(self, month=None):
        month_filter = ""
        parameters = ()
        if month:
            month = self._validate_month(month)
            month_filter = "AND substr(a.attendance_date, 1, 7) = ?"
            parameters = (month,)
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT s.id, s.roll_number, s.name, s.course, s.semester,
                          COUNT(a.id) AS total_classes,
                          SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END)
                              AS present_days
                   FROM Students s
                   LEFT JOIN Attendance a ON a.student_id = s.id {}
                   GROUP BY s.id
                   ORDER BY s.roll_number COLLATE NOCASE""".format(month_filter),
                parameters,
            ).fetchall()
        return [self._report_row(dict(row), row) for row in rows]

    def dashboard_statistics(self):
        today = date.today().isoformat()
        with self.connect() as connection:
            total_students = connection.execute(
                "SELECT COUNT(*) AS count FROM Students"
            ).fetchone()["count"]
            counts = connection.execute(
                """SELECT
                       SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present,
                       SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent
                   FROM Attendance WHERE attendance_date = ?""",
                (today,),
            ).fetchone()
            recent = connection.execute(
                """SELECT s.roll_number, s.name, a.attendance_date, a.status
                   FROM Attendance a JOIN Students s ON s.id = a.student_id
                   ORDER BY a.attendance_date DESC, a.id DESC LIMIT 8"""
            ).fetchall()
            totals = connection.execute(
                """SELECT COUNT(*) AS classes,
                          SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END)
                              AS present
                   FROM Attendance"""
            ).fetchone()
        classes = totals["classes"] or 0
        return {
            "total_students": total_students,
            "present_today": counts["present"] or 0,
            "absent_today": counts["absent"] or 0,
            "overall_percentage": round(
                ((totals["present"] or 0) / classes) * 100, 2
            ) if classes else 0.0,
            "recent": [dict(row) for row in recent],
        }
