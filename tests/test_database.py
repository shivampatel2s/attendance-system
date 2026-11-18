"""Core workflow tests using a temporary SQLite database."""

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import AttendanceDatabase, DEFAULT_PASSWORD, DEFAULT_USERNAME
from export import export_attendance, export_students


class AttendanceDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = AttendanceDatabase(Path(self.temp_dir.name) / "test.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_student(self, roll="BCA001", name="Asha"):
        return self.database.add_student(
            roll, name, "BCA", "1", "9876543210", "student123"
        )

    def test_login_password_hash_and_validation(self):
        self.assertTrue(self.database.validate_login(DEFAULT_USERNAME, DEFAULT_PASSWORD))
        self.assertFalse(self.database.validate_login(DEFAULT_USERNAME, "wrong"))

    def test_student_login_is_separate_and_password_is_hashed(self):
        student_id = self.add_student()
        self.assertIsNone(self.database.validate_student_login("BCA001", "wrong"))
        student = self.database.validate_student_login("BCA001", "student123")
        self.assertEqual(student["id"], student_id)
        self.assertNotIn("password_hash", student)
        with self.database.connect() as connection:
            stored_hash = connection.execute(
                "SELECT password_hash FROM Students WHERE id = ?", (student_id,)
            ).fetchone()["password_hash"]
        self.assertNotEqual(stored_hash, "student123")

    def test_student_add_update_delete(self):
        student_id = self.add_student()
        self.database.update_student(student_id, "BCA001", "Asha Rao", "BCA", "2",
                                     "9999999999")
        self.assertEqual(self.database.get_student(student_id)["name"], "Asha Rao")
        self.database.delete_student(student_id)
        self.assertEqual(self.database.get_students(), [])

    def test_duplicate_roll_number_is_rejected(self):
        self.add_student()
        with self.assertRaises(Exception):
            self.add_student("BCA001", "Other")

    def test_attendance_correction_and_unique_student_date(self):
        student_id = self.add_student()
        self.database.save_attendance("2026-03-01", {student_id: "Present"})
        self.database.save_attendance("2026-03-01", {student_id: "Absent"})
        records = self.database.get_attendance_records("2026-03-01")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "Absent")
        with self.assertRaises(ValueError):
            self.database.save_attendance("2026-03-02", {student_id: "Not marked"})

    def test_existing_database_is_migrated_for_student_login(self):
        legacy_path = Path(self.temp_dir.name) / "legacy.db"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.execute(
                """CREATE TABLE Students (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   roll_number TEXT NOT NULL UNIQUE,
                   name TEXT NOT NULL,
                   course TEXT NOT NULL,
                   semester TEXT NOT NULL,
                   phone TEXT NOT NULL
                )"""
            )
            connection.execute(
                """INSERT INTO Students
                   (roll_number, name, course, semester, phone)
                   VALUES ('OLD001', 'Legacy Student', 'BCA', '1', '1234567890')"""
            )
            connection.commit()
        finally:
            connection.close()
        migrated = AttendanceDatabase(legacy_path)
        self.assertIsNone(migrated.validate_student_login("OLD001", "newpass"))
        migrated.update_student(
            1, "OLD001", "Legacy Student", "BCA", "1", "1234567890", "newpass"
        )
        self.assertEqual(
            migrated.validate_student_login("OLD001", "newpass")["id"], 1
        )

    def test_report_percentage_and_month_filter(self):
        student_id = self.add_student()
        self.database.save_attendance(
            "2026-03-01", {student_id: "Present"}
        )
        self.database.save_attendance(
            "2026-03-02", {student_id: "Absent"}
        )
        report = self.database.student_report(student_id)
        self.assertEqual(report["total_classes"], 2)
        self.assertEqual(report["present_days"], 1)
        self.assertEqual(report["absent_days"], 1)
        self.assertEqual(report["percentage"], 50.0)
        self.assertEqual(self.database.attendance_report("2026-03")[0]["percentage"],
                         50.0)
        with self.assertRaises(ValueError):
            self.database.attendance_report("2026-99")

    def test_student_and_attendance_csv_exports(self):
        student_id = self.add_student()
        self.database.save_attendance("2026-03-01", {student_id: "Present"})
        with tempfile.TemporaryDirectory() as output_dir:
            students_file = Path(output_dir) / "students.csv"
            attendance_file = Path(output_dir) / "attendance.csv"
            export_students(self.database, students_file)
            export_attendance(self.database, attendance_file)
            with students_file.open(encoding="utf-8-sig", newline="") as stream:
                self.assertEqual(len(list(csv.reader(stream))), 2)
            with attendance_file.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows[1][-1], "Present")


if __name__ == "__main__":
    unittest.main()
