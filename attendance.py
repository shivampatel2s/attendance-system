"""Daily attendance entry and history screen."""

from datetime import date
import sqlite3
from tkinter import messagebox, ttk


class AttendanceFrame(ttk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent, style="Page.TFrame", padding=24)
        self.database = database
        ttk.Label(self, text="Attendance", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, text="Select a date and mark each registered student.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 15))
        toolbar = ttk.Frame(self, style="Page.TFrame")
        toolbar.pack(fill="x", pady=(0, 12))
        ttk.Label(toolbar, text="Attendance date (YYYY-MM-DD)").pack(side="left")
        self.date_entry = ttk.Entry(toolbar, width=14)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.pack(side="left", padx=9, ipady=3)
        ttk.Button(toolbar, text="Load date", command=self.load_date).pack(side="left")
        ttk.Button(toolbar, text="Save attendance", style="Accent.TButton",
                   command=self.save).pack(side="right")
        status_bar = ttk.Frame(self, style="Page.TFrame")
        status_bar.pack(fill="x", pady=(0, 10))
        ttk.Button(status_bar, text="Mark selected Present",
                   command=lambda: self.mark_selected("Present")).pack(side="left")
        ttk.Button(status_bar, text="Mark selected Absent",
                   command=lambda: self.mark_selected("Absent")).pack(side="left", padx=8)
        ttk.Button(status_bar, text="Mark all Present",
                   command=lambda: self.mark_all("Present")).pack(side="left")
        ttk.Button(status_bar, text="Mark all Absent",
                   command=lambda: self.mark_all("Absent")).pack(side="left", padx=8)
        self.table = ttk.Treeview(
            self, columns=("roll_number", "name", "course", "status"),
            show="headings", height=16, selectmode="extended"
        )
        for column, heading in (
            ("roll_number", "Roll number"), ("name", "Student"),
            ("course", "Course"), ("status", "Status"),
        ):
            self.table.heading(column, text=heading)
            self.table.column(column, width=180, anchor="w")
        self.table.bind("<Double-1>", self.toggle_status)
        self.table.pack(fill="both", expand=True)
        ttk.Label(self, text="Tip: double-click a student row to switch Present/Absent.",
                  style="Muted.TLabel").pack(anchor="w", pady=(8, 0))
        self.load_date()

    def load_date(self):
        try:
            records = self.database.get_attendance_for_date(self.date_entry.get().strip())
            self.table.delete(*self.table.get_children())
            for record in records:
                self.table.insert(
                    "", "end", iid=str(record["id"]),
                    values=(record["roll_number"], record["name"], record["course"],
                            record["status"] or "Not marked")
                )
        except ValueError as error:
            messagebox.showerror("Invalid date", str(error), parent=self)
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error), parent=self)

    def toggle_status(self, event):
        row_id = self.table.identify_row(event.y)
        if not row_id:
            return
        values = list(self.table.item(row_id, "values"))
        values[3] = "Absent" if values[3] == "Present" else "Present"
        self.table.item(row_id, values=values)

    def mark_selected(self, status):
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo(
                "Select students", "Select one or more student rows first.", parent=self
            )
            return
        for row_id in selected:
            values = list(self.table.item(row_id, "values"))
            values[3] = status
            self.table.item(row_id, values=values)

    def mark_all(self, status):
        for row_id in self.table.get_children():
            values = list(self.table.item(row_id, "values"))
            values[3] = status
            self.table.item(row_id, values=values)

    def save(self):
        try:
            attendance_date = self.database._validate_date(self.date_entry.get().strip())
            existing = self.database.get_attendance_records(attendance_date)
            if existing and not messagebox.askyesno(
                "Correct attendance?",
                "Attendance already exists for this date. Save these values as a correction?",
                parent=self,
            ):
                return
            records = {
                int(row_id): self.table.item(row_id, "values")[3]
                for row_id in self.table.get_children()
            }
            self.database.save_attendance(attendance_date, records)
            messagebox.showinfo("Attendance saved", "Attendance was saved successfully.",
                                parent=self)
            self.load_date()
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not save attendance", str(error), parent=self)
