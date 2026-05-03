"""
reminder.py - Medicine Reminder System
Add, view, delete medicines with reminder times
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import database as db

COLORS = {
    "bg":       "#F0F7FF",
    "panel":    "#FFFFFF",
    "primary":  "#1A6FB5",
    "accent":   "#27AE60",
    "text":     "#2C3E50",
    "subtext":  "#7F8C8D",
    "border":   "#D5E8F7",
    "danger":   "#E74C3C",
    "warn":     "#F39C12",
    "entry_bg": "#F8FCFF",
}


def _entry(parent, var, **kw):
    return tk.Entry(parent, textvariable=var,
                    bg=COLORS["entry_bg"], fg=COLORS["text"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=COLORS["border"],
                    highlightcolor=COLORS["primary"],
                    font=("Helvetica", 11), bd=0,
                    insertbackground=COLORS["primary"], **kw)


class ReminderFrame(tk.Frame):
    """Medicine reminder management screen."""

    def __init__(self, parent, user, app_ref):
        super().__init__(parent, bg=COLORS["bg"])
        self.user = user
        self.app  = app_ref
        self._build()

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=COLORS["warn"], height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="💊  Medicine Reminders",
                 font=("Helvetica", 14, "bold"),
                 bg=COLORS["warn"], fg="white").pack(
                     side="left", padx=20, pady=12)

        # Split layout
        panes = tk.Frame(self, bg=COLORS["bg"])
        panes.pack(fill="both", expand=True)

        left  = tk.Frame(panes, bg=COLORS["panel"], width=340)
        right = tk.Frame(panes, bg=COLORS["bg"])
        left.pack(side="left", fill="y", padx=(20, 10), pady=20)
        right.pack(side="right", fill="both", expand=True, pady=20,
                   padx=(0, 20))
        left.pack_propagate(False)

        self._add_form(left)
        self._med_list(right)

    # ── ADD MEDICINE FORM ────────────────────────────────────────────────────

    def _add_form(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=COLORS["warn"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="➕  Add Medicine",
                 font=("Helvetica", 12, "bold"),
                 bg=COLORS["warn"], fg="white").pack(
                     side="left", padx=16, pady=10)

        self.med_name_var  = tk.StringVar()
        self.med_dose_var  = tk.StringVar()
        self.med_freq_var  = tk.StringVar(value="Once daily")

        # Time checkboxes
        self.time_vars = {}
        for t in ["06:00", "08:00", "12:00", "14:00",
                  "18:00", "20:00", "22:00"]:
            self.time_vars[t] = tk.BooleanVar()

        # Fields
        fields = [
            ("💊  Medicine Name *",  self.med_name_var),
            ("💉  Dosage (e.g. 500mg)", self.med_dose_var),
        ]
        for lbl, var in fields:
            tk.Label(parent, text=lbl,
                     font=("Helvetica", 10, "bold"),
                     bg=COLORS["panel"], fg=COLORS["text"],
                     anchor="w").pack(fill="x", padx=16, pady=(12, 2))
            _entry(parent, var).pack(fill="x", padx=16, ipady=7)

        # Frequency
        tk.Label(parent, text="🔁  Frequency",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"],
                 anchor="w").pack(fill="x", padx=16, pady=(12, 2))
        freqs = ["Once daily", "Twice daily", "Three times daily",
                 "Every 6 hours", "Before meals", "After meals",
                 "As needed"]
        ttk.Combobox(parent, textvariable=self.med_freq_var,
                     values=freqs, state="readonly",
                     font=("Helvetica", 10)).pack(
                         fill="x", padx=16, ipady=4, pady=(0, 8))

        # Reminder times
        tk.Label(parent, text="⏰  Reminder Times (select all that apply):",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"],
                 anchor="w").pack(fill="x", padx=16, pady=(10, 4))

        time_grid = tk.Frame(parent, bg=COLORS["panel"])
        time_grid.pack(fill="x", padx=16)
        for i, (t, var) in enumerate(self.time_vars.items()):
            row = i // 3
            col = i % 3
            cb = tk.Checkbutton(time_grid, text=t, variable=var,
                                 bg=COLORS["panel"], fg=COLORS["text"],
                                 selectcolor=COLORS["panel"],
                                 activebackground=COLORS["panel"],
                                 font=("Helvetica", 9))
            cb.grid(row=row, column=col, sticky="w", padx=4, pady=2)

        # Save button
        tk.Button(parent, text="💾  Add Medicine",
                  command=self._save_medicine,
                  bg=COLORS["warn"], fg="white",
                  font=("Helvetica", 11, "bold"),
                  relief="flat", cursor="hand2").pack(
                      fill="x", padx=16, ipady=10, pady=(16, 8))

        # Info box
        info = tk.Frame(parent, bg="#FFF8E1",
                        highlightbackground=COLORS["warn"],
                        highlightthickness=1)
        info.pack(fill="x", padx=16, pady=(0, 16))
        tk.Label(info, text="ℹ️  Desktop notifications are sent\n"
                 "at reminder times via system alerts.",
                 font=("Helvetica", 9),
                 bg="#FFF8E1", fg=COLORS["warn"],
                 justify="left").pack(padx=10, pady=8)

    def _save_medicine(self):
        name = self.med_name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Please enter a medicine name.")
            return

        selected_times = [t for t, v in self.time_vars.items() if v.get()]
        times_json = json.dumps(selected_times)

        db.add_medicine(self.user["id"], name,
                        self.med_dose_var.get().strip(),
                        self.med_freq_var.get(),
                        times_json)

        messagebox.showinfo("✅ Saved",
                            f"Medicine '{name}' added!\n"
                            f"Reminder times: {', '.join(selected_times) or 'None set'}")
        self.med_name_var.set("")
        self.med_dose_var.set("")
        for v in self.time_vars.values():
            v.set(False)
        self._refresh_list()

    # ── MEDICINE LIST ────────────────────────────────────────────────────────

    def _med_list(self, parent):
        hdr = tk.Frame(parent, bg=COLORS["primary"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  Current Medicines",
                 font=("Helvetica", 12, "bold"),
                 bg=COLORS["primary"], fg="white").pack(
                     side="left", padx=16, pady=10)

        self.list_frame = tk.Frame(parent, bg=COLORS["bg"])
        self.list_frame.pack(fill="both", expand=True)
        self._refresh_list()

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        meds = db.get_medicines(self.user["id"])
        if not meds:
            tk.Label(self.list_frame,
                     text="No medicines added yet.\n"
                     "Add your first medicine on the left.",
                     font=("Helvetica", 10),
                     bg=COLORS["bg"], fg=COLORS["subtext"]).pack(pady=40)
            return

        for i, med in enumerate(meds):
            bg = COLORS["panel"] if i % 2 == 0 else "#F0F7FF"
            card = tk.Frame(self.list_frame, bg=bg,
                            highlightbackground=COLORS["border"],
                            highlightthickness=1)
            card.pack(fill="x", padx=4, pady=3)

            # Icon + name
            top_row = tk.Frame(card, bg=bg)
            top_row.pack(fill="x", padx=12, pady=(10, 4))

            tk.Label(top_row, text=f"💊  {med['name']}",
                     font=("Helvetica", 13, "bold"),
                     bg=bg, fg=COLORS["warn"]).pack(side="left")

            # Delete button
            tk.Button(top_row, text="🗑",
                      command=lambda m=med["id"]: self._delete_med(m),
                      bg=COLORS["danger"], fg="white",
                      font=("Helvetica", 10),
                      relief="flat", cursor="hand2",
                      width=3).pack(side="right")

            # Details
            det = tk.Frame(card, bg=bg)
            det.pack(fill="x", padx=12, pady=(0, 10))

            tk.Label(det, text=f"Dosage: {med['dosage'] or 'N/A'}",
                     font=("Helvetica", 9),
                     bg=bg, fg=COLORS["text"]).pack(side="left", padx=(0, 16))
            tk.Label(det, text=f"Frequency: {med['frequency']}",
                     font=("Helvetica", 9),
                     bg=bg, fg=COLORS["text"]).pack(side="left", padx=(0, 16))

            # Times
            try:
                times = json.loads(med.get("reminder_times", "[]"))
                times_str = ", ".join(times) if times else "No times set"
            except Exception:
                times_str = "No times set"

            tk.Label(det, text=f"⏰ {times_str}",
                     font=("Helvetica", 9, "bold"),
                     bg=bg, fg=COLORS["primary"]).pack(side="left")

    def _delete_med(self, med_id):
        if messagebox.askyesno("Confirm Delete",
                                "Remove this medicine from your list?"):
            db.delete_medicine(med_id)
            messagebox.showinfo("Deleted", "Medicine removed.")
            self._refresh_list()
