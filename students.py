"""Student registration, search and maintenance screen."""

import tkinter as tk
import sqlite3
from tkinter import messagebox, ttk


class StudentsFrame(ttk.Frame):
    COLUMNS = ("roll_number", "name", "course", "semester", "phone")
    HEADINGS = ("Roll number", "Student name", "Course", "Semester", "Phone")

    def __init__(self, parent, database):
        super().__init__(parent, style="Page.TFrame", padding=24)
        self.database = database
        ttk.Label(self, text="Students", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, text="Register and manage student records.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 18))
        toolbar = ttk.Frame(self, style="Page.TFrame")
        toolbar.pack(fill="x", pady=(0, 12))
        self.search = ttk.Entry(toolbar, width=34)
        self.search.pack(side="left", ipady=4)
        self.search.insert(0, "")
        self.search.bind("<KeyRelease>", lambda _event: self.refresh())
        ttk.Button(toolbar, text="Add student", style="Accent.TButton",
                   command=self.add_student).pack(side="right")
        ttk.Button(toolbar, text="Edit selected", command=self.edit_student).pack(
            side="right", padx=8
        )
        ttk.Button(toolbar, text="Delete selected", command=self.delete_student).pack(
            side="right"
        )
        self.table = ttk.Treeview(self, columns=self.COLUMNS, show="headings", height=18)
        for column, heading in zip(self.COLUMNS, self.HEADINGS):
            self.table.heading(column, text=heading)
            self.table.column(column, width=145, anchor="w")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.refresh()

    def refresh(self):
        self.table.delete(*self.table.get_children())
        for student in self.database.get_students(self.search.get()):
            self.table.insert(
                "", "end", iid=str(student["id"]),
                values=tuple(student[column] for column in self.COLUMNS)
            )

    def _student_dialog(self, title, student=None):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)
        fields = (
            ("Roll number", "roll_number"),
            ("Student name", "name"),
            ("Course", "course"),
            ("Semester", "semester"),
            ("Phone number", "phone"),
            ("Login password", "password"),
        )
        entries = {}
        body = ttk.Frame(dialog, padding=22)
        body.pack(fill="both", expand=True)
        for row, (label, field) in enumerate(fields):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=6)
            entry = ttk.Entry(body, width=32)
            if field == "password":
                entry.configure(show="*")
            entry.grid(row=row, column=1, padx=(16, 0), pady=6)
            if student and field != "password":
                entry.insert(0, student[field])
            entries[field] = entry

        def save():
            values = [entries[field].get().strip()
                      for _label, field in fields[:5]]
            password = entries["password"].get()
            try:
                if student:
                    self.database.update_student(student["id"], *values, password)
                else:
                    self.database.add_student(*values, password)
                dialog.destroy()
                self.refresh()
            except (ValueError, sqlite3.Error) as error:
                messagebox.showerror("Could not save student", str(error), parent=dialog)

        buttons = ttk.Frame(body)
        buttons.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(15, 0))
        ttk.Label(
            body,
            text=("Required for student sign-in; leave blank to keep current password."
                  if student else "Students use their roll number and this password to sign in."),
            style="Muted.TLabel",
        ).grid(row=len(fields) + 1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="left", padx=6)
        ttk.Button(buttons, text="Save student", style="Accent.TButton",
                   command=save).pack(side="left")
        entries["roll_number"].focus_set()

    def add_student(self):
        self._student_dialog("Add student")

    def edit_student(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Select a student", "Choose a student to edit.")
            return
        student = self.database.get_student(int(selection[0]))
        if student:
            self._student_dialog("Edit student", student)

    def delete_student(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Select a student", "Choose a student to delete.")
            return
        if messagebox.askyesno(
            "Delete student",
            "Delete this student and their attendance records? This cannot be undone.",
            parent=self,
        ):
            self.database.delete_student(int(selection[0]))
            self.refresh()
