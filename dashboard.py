"""Dashboard view."""

import tkinter as tk
from tkinter import ttk


class DashboardFrame(ttk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent, style="Page.TFrame", padding=24)
        self.database = database
        ttk.Label(self, text="Dashboard", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, text="A quick overview of your class attendance.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 20))
        self.cards = ttk.Frame(self, style="Page.TFrame")
        self.cards.pack(fill="x", pady=(0, 22))
        self.card_values = {}
        ttk.Label(self, text="Recent attendance", style="Section.TLabel").pack(
            anchor="w", pady=(0, 10)
        )
        self.recent_table = self._table(
            self, ("roll_number", "name", "attendance_date", "status"),
            ("Roll number", "Student", "Date", "Status"), height=9
        )
        self.refresh()

    @staticmethod
    def _table(parent, columns, headings, height=8):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        table = ttk.Treeview(container, columns=columns, show="headings", height=height)
        for column, heading in zip(columns, headings):
            table.heading(column, text=heading)
            table.column(column, width=150, anchor="w")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return table

    def refresh(self):
        stats = self.database.dashboard_statistics()
        for child in self.cards.winfo_children():
            child.destroy()
        items = (
            ("Total students", stats["total_students"]),
            ("Present today", stats["present_today"]),
            ("Absent today", stats["absent_today"]),
            ("Overall attendance", "{}%".format(stats["overall_percentage"])),
        )
        for index, (label, value) in enumerate(items):
            card = ttk.Frame(self.cards, style="Card.TFrame", padding=18)
            card.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 10, 0))
            ttk.Label(card, text=label, style="Muted.TLabel").pack(anchor="w")
            ttk.Label(card, text=str(value), style="CardValue.TLabel").pack(
                anchor="w", pady=(8, 0)
            )
            self.cards.columnconfigure(index, weight=1)
        self.recent_table.delete(*self.recent_table.get_children())
        for row in stats["recent"]:
            self.recent_table.insert(
                "", "end",
                values=(row["roll_number"], row["name"], row["attendance_date"],
                        row["status"])
            )
