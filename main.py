"""Launch the Student Attendance Management System."""

import tkinter as tk
import sqlite3
from tkinter import filedialog, messagebox, ttk

from attendance import AttendanceFrame
from dashboard import DashboardFrame
from database import AttendanceDatabase
from export import export_attendance, export_students
from login import LoginWindow
from reports import ReportsFrame
from students import StudentsFrame
from student_dashboard import StudentDashboardFrame


class AttendanceApplication:
    def __init__(self, root):
        self.root = root
        self.database = AttendanceDatabase()
        self.root.title("Student Attendance Management System")
        self.root.configure(bg="#f3f6fb")
        self.root.state("zoomed")
        self._configure_styles()
        LoginWindow(root, self.database, self.show_application)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background="#f3f6fb")
        style.configure("Page.TFrame", background="#f3f6fb")
        style.configure("Sidebar.TFrame", background="#14213d")
        style.configure("Login.TFrame", background="white")
        style.configure("Login.TLabel", background="white", foreground="#24334d")
        style.configure("TLabel", background="#f3f6fb", foreground="#24334d")
        style.configure("PageTitle.TLabel", font=("Segoe UI", 23, "bold"),
                        foreground="#14213d", background="#f3f6fb")
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"),
                        foreground="#14213d", background="#f3f6fb")
        style.configure("Muted.TLabel", foreground="#718096", background="#f3f6fb")
        style.configure("Card.TFrame", background="white")
        style.configure("CardValue.TLabel", font=("Segoe UI", 24, "bold"),
                        foreground="#147d92", background="white")
        style.configure("Login.TFrame", background="white")
        style.configure("LoginTitle.TLabel", font=("Segoe UI", 19, "bold"),
                        foreground="#14213d", background="white")
        style.configure("LoginSubtitle.TLabel", foreground="#718096", background="white")
        style.configure("TButton", padding=(12, 8), background="#e6edf5",
                        foreground="#24334d")
        style.map("TButton", background=[("active", "#d4e0ed")])
        style.configure("Accent.TButton", background="#147d92", foreground="white",
                        font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#0f687a")])
        style.configure("Treeview", rowheight=32, background="white",
                        fieldbackground="white", foreground="#24334d")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#e8eef5", foreground="#24334d", padding=8)
        style.configure("TEntry", padding=7)
        style.configure("TCombobox", padding=6)

    def show_application(self, session):
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True)
        self.sidebar = ttk.Frame(self.container, style="Sidebar.TFrame", width=225)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ttk.Label(
            self.sidebar,
            text=("STUDENT\nPORTAL" if session["role"] == "student"
                  else "ATTENDANCE\nMANAGER"),
            font=("Segoe UI", 15, "bold"), foreground="white",
            background="#14213d", justify="left"
        ).pack(anchor="w", padx=22, pady=(28, 32))
        self.content = ttk.Frame(self.container, style="Page.TFrame")
        self.content.pack(side="left", fill="both", expand=True)
        if session["role"] == "student":
            page = StudentDashboardFrame(
                self.content, self.database, session["student"]
            )
            page.pack(fill="both", expand=True)
            ttk.Button(self.sidebar, text="Log out", command=self.logout).pack(
                side="bottom", fill="x", padx=12, pady=18
            )
            return

        self.pages = {}
        navigation = (
            ("Dashboard", DashboardFrame),
            ("Students", StudentsFrame),
            ("Attendance", AttendanceFrame),
            ("Reports", ReportsFrame),
        )
        for label, page_class in navigation:
            self.pages[label] = page_class(self.content, self.database)
            ttk.Button(
                self.sidebar, text=label, style="Nav.TButton",
                command=lambda selected=label: self.show_page(selected)
            ).pack(fill="x", padx=12, pady=4)
        ttk.Separator(self.sidebar).pack(fill="x", padx=16, pady=16)
        style = ttk.Style()
        style.configure("Nav.TButton", background="#14213d", foreground="white",
                        anchor="w", padding=(14, 11))
        style.map("Nav.TButton", background=[("active", "#20345a")])
        ttk.Button(self.sidebar, text="Export students to CSV",
                   command=self.export_student_file).pack(fill="x", padx=12, pady=4)
        ttk.Button(self.sidebar, text="Export attendance to CSV",
                   command=self.export_attendance_file).pack(fill="x", padx=12, pady=4)
        ttk.Button(self.sidebar, text="Log out", command=self.logout).pack(
            side="bottom", fill="x", padx=12, pady=18
        )
        self.show_page("Dashboard")

    def show_page(self, label):
        for page in self.pages.values():
            page.pack_forget()
        page = self.pages[label]
        page.pack(fill="both", expand=True)
        if label == "Dashboard":
            page.refresh()
        elif label == "Students":
            page.refresh()
        elif label == "Attendance":
            page.load_date()
        elif label == "Reports":
            page.generate()

    def export_student_file(self):
        path = filedialog.asksaveasfilename(
            title="Export student records", defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"),)
        )
        if path:
            try:
                export_students(self.database, path)
                messagebox.showinfo("Export complete", "Student records exported.")
            except (OSError, ValueError, sqlite3.Error) as error:
                messagebox.showerror("Export failed", str(error))

    def export_attendance_file(self):
        path = filedialog.asksaveasfilename(
            title="Export attendance records", defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"),)
        )
        if path:
            try:
                export_attendance(self.database, path)
                messagebox.showinfo("Export complete", "Attendance records exported.")
            except (OSError, ValueError, sqlite3.Error) as error:
                messagebox.showerror("Export failed", str(error))

    def logout(self):
        if messagebox.askyesno("Log out", "Do you want to log out?"):
            self.container.destroy()
            LoginWindow(self.root, self.database, self.show_application)


def main():
    root = tk.Tk()
    AttendanceApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
