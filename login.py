"""Separate sign-in screen for administrators and students."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


class LoginWindow:
    def __init__(self, root, database, on_success):
        self.root = root
        self.database = database
        self.on_success = on_success
        self.frame = ttk.Frame(root, style="Login.TFrame", padding=36)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(self.frame, text="STUDENT ATTENDANCE",
                  style="LoginTitle.TLabel").pack(pady=(0, 6))
        ttk.Label(
            self.frame, text="Management System", style="LoginSubtitle.TLabel"
        ).pack(pady=(0, 24))

        ttk.Label(self.frame, text="Sign in as", style="Login.TLabel").pack(anchor="w")
        self.role = ttk.Combobox(
            self.frame, state="readonly", width=31, values=("Administrator", "Student")
        )
        self.role.set("Administrator")
        self.role.pack(fill="x", pady=(5, 15))
        self.role.bind("<<ComboboxSelected>>", self.update_labels)
        self.username_label = ttk.Label(
            self.frame, text="Username", style="Login.TLabel"
        )
        self.username_label.pack(anchor="w")
        self.username = ttk.Entry(self.frame, width=34)
        self.username.pack(fill="x", pady=(5, 15))
        ttk.Label(self.frame, text="Password", style="Login.TLabel").pack(anchor="w")
        self.password = ttk.Entry(self.frame, width=34, show="*")
        self.password.pack(fill="x", pady=(5, 20))
        self.password.bind("<Return>", lambda _event: self.login())
        ttk.Button(self.frame, text="Sign in", style="Accent.TButton",
                   command=self.login).pack(fill="x", ipady=5)
        self.username.focus_set()

    def update_labels(self, _event=None):
        if self.role.get() == "Student":
            self.username_label.configure(text="Roll number")
        else:
            self.username_label.configure(text="Username")

    def login(self):
        try:
            if self.role.get() == "Student":
                student = self.database.validate_student_login(
                    self.username.get().strip(), self.password.get()
                )
                if student:
                    self.frame.destroy()
                    self.on_success({"role": "student", "student": student})
                    return
            elif self.database.validate_login(
                self.username.get().strip(), self.password.get()
            ):
                self.frame.destroy()
                self.on_success({"role": "admin"})
                return
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error), parent=self.frame)
            return
        messagebox.showerror(
            "Sign in failed",
            "Incorrect username or password, or the student account has no password.",
            parent=self.frame,
        )
        self.password.delete(0, "end")
        self.password.focus_set()
