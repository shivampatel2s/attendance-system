"""Read-only attendance portal for the signed-in student."""

from tkinter import ttk


class StudentDashboardFrame(ttk.Frame):
    def __init__(self, parent, database, student):
        super().__init__(parent, style="Page.TFrame", padding=24)
        self.database = database
        self.student = student
        ttk.Label(self, text="My attendance", style="PageTitle.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            self,
            text="{}  |  {}  |  Semester {}".format(
                student["name"], student["course"], student["semester"]
            ),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 20))

        self.cards = ttk.Frame(self, style="Page.TFrame")
        self.cards.pack(fill="x", pady=(0, 24))
        ttk.Label(self, text="Attendance history", style="Section.TLabel").pack(
            anchor="w", pady=(0, 10)
        )
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        columns = ("attendance_date", "status")
        self.table = ttk.Treeview(container, columns=columns, show="headings", height=14)
        self.table.heading("attendance_date", text="Date")
        self.table.heading("status", text="Attendance")
        self.table.column("attendance_date", width=200, anchor="w")
        self.table.column("status", width=180, anchor="w")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.refresh()

    def refresh(self):
        report = self.database.student_report(self.student["id"])
        if report is None:
            return
        for child in self.cards.winfo_children():
            child.destroy()
        stats = (
            ("Total classes", report["total_classes"]),
            ("Present", report["present_days"]),
            ("Absent", report["absent_days"]),
            ("Attendance", "{}%".format(report["percentage"])),
        )
        for index, (label, value) in enumerate(stats):
            card = ttk.Frame(self.cards, style="Card.TFrame", padding=18)
            card.grid(row=0, column=index, sticky="ew",
                      padx=(0 if index == 0 else 10, 0))
            ttk.Label(card, text=label, style="Muted.TLabel").pack(anchor="w")
            ttk.Label(card, text=str(value), style="CardValue.TLabel").pack(
                anchor="w", pady=(8, 0)
            )
            self.cards.columnconfigure(index, weight=1)

        records = self.database.get_attendance_records(student_id=self.student["id"])
        self.table.delete(*self.table.get_children())
        for record in records:
            self.table.insert(
                "", "end", values=(record["attendance_date"], record["status"])
            )
