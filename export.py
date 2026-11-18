"""CSV export helpers. UTF-8 with a BOM opens cleanly in Microsoft Excel."""

import csv


def export_students(database, file_path):
    fields = ("roll_number", "name", "course", "semester", "phone")
    headers = ("Roll Number", "Name", "Course", "Semester", "Phone Number")
    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        for student in database.get_students():
            writer.writerow([student[field] for field in fields])


def export_attendance(database, file_path, attendance_date=None, month=None):
    headers = ("Roll Number", "Name", "Course", "Semester", "Date", "Status")
    fields = ("roll_number", "name", "course", "semester", "attendance_date", "status")
    records = database.get_attendance_records(attendance_date, month)
    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        for record in records:
            writer.writerow([record[field] for field in fields])
