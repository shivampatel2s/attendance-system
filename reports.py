"""Attendance reports and report filtering."""

import sqlite3
from tkinter import messagebox, ttk


class ReportsFrame(ttk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent, style="Page.TFrame", padding=24)
        self.database = database
        ttk.Label(self, text="Reports", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, text="Review attendance by date, month or student.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 16))
        controls = ttk.Frame(self, style="Page.TFrame")
        controls.pack(fill="x", pady=(0, 12))
        ttk.Label(controls, text="Report").pack(side="left")
        self.report_type = ttk.Combobox(
            controls, state="readonly", width=18,
            values=("Overall", "Daily", "Monthly", "Individual student")
        )
        self.report_type.set("Overall")
        self.report_type.pack(side="left", padx=(8, 14))
        ttk.Label(controls, text="Date / month / roll number").pack(side="left")
        self.filter_entry = ttk.Entry(controls, width=18)
        self.filter_entry.pack(side="left", padx=8, ipady=3)
        ttk.Button(controls, text="Generate", style="Accent.TButton",
                   command=self.generate).pack(side="left", padx=4)
        ttk.Button(controls, text="Below 75%", command=self.show_low_attendance).pack(
            side="left", padx=4
        )
        self.summary = ttk.Label(self, text="", style="Section.TLabel")
        self.summary.pack(anchor="w", pady=(0, 10))
        self.table = ttk.Treeview(self, show="headings", height=17)
        self.table.pack(fill="both", expand=True)
        self.generate()

    def _display(self, rows, columns, headings, summary=""):
        self.table.delete(*self.table.get_children())
        self.table["columns"] = columns
        for column, heading in zip(columns, headings):
            self.table.heading(column, text=heading)
            self.table.column(column, width=135, anchor="w")
        for row in rows:
            self.table.insert("", "end", values=tuple(row.get(c, "") for c in columns))
        self.summary.configure(text=summary)

    def generate(self):
        report_type = self.report_type.get()
        value = self.filter_entry.get().strip()
        try:
            if report_type == "Daily":
                records = self.database.get_attendance_records(attendance_date=value)
                self._display(records, ("roll_number", "name", "attendance_date", "status"),
                              ("Roll number", "Student", "Date", "Status"),
                              "{} attendance records".format(len(records)))
            elif report_type == "Monthly":
                if not value:
                    raise ValueError("Enter a month in YYYY-MM format.")
                rows = self.database.attendance_report(month=value)
                self._display(rows, ("roll_number", "name", "total_classes",
                                     "present_days", "absent_days", "percentage"),
                              ("Roll number", "Student", "Classes", "Present",
                               "Absent", "Attendance %"),
                              "Monthly attendance summary for {}".format(value))
            elif report_type == "Individual student":
                if not value:
                    raise ValueError("Enter the student's roll number.")
                matches = [s for s in self.database.get_students(value)
                           if s["roll_number"].lower() == value.lower()]
                if not matches:
                    raise ValueError("No student found with that roll number.")
                report = self.database.student_report(matches[0]["id"])
                self._display([report], ("roll_number", "name", "total_classes",
                                         "present_days", "absent_days", "percentage"),
                              ("Roll number", "Student", "Classes", "Present",
                               "Absent", "Attendance %"),
                              "Individual attendance summary")
            else:
                rows = self.database.attendance_report()
                self._display(rows, ("roll_number", "name", "total_classes",
                                     "present_days", "absent_days", "percentage"),
                              ("Roll number", "Student", "Classes", "Present",
                               "Absent", "Attendance %"),
                              "Overall attendance summary")
        except ValueError as error:
            messagebox.showerror("Report filter", str(error), parent=self)
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error), parent=self)

    def show_low_attendance(self):
        try:
            rows = [row for row in self.database.attendance_report()
                    if row["total_classes"] and row["percentage"] < 75]
            self._display(rows, ("roll_number", "name", "total_classes", "present_days",
                                 "absent_days", "percentage"),
                          ("Roll number", "Student", "Classes", "Present", "Absent",
                           "Attendance %"),
                          "{} student(s) below 75% attendance".format(len(rows)))
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error), parent=self)
