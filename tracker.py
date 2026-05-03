"""
tracker.py - Health Tracker Module
Tabs: Blood Sugar | Water | Meals | Exercise
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
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
    "low":      "#3498DB",
    "entry_bg": "#F8FCFF",
}

SUGAR_LOW  = 70
SUGAR_HIGH = 180


def _entry(parent, var, **kw):
    e = tk.Entry(parent, textvariable=var,
                 bg=COLORS["entry_bg"], fg=COLORS["text"],
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=COLORS["border"],
                 highlightcolor=COLORS["primary"],
                 font=("Helvetica", 11), bd=0,
                 insertbackground=COLORS["primary"], **kw)
    return e


def _label(parent, text, bold=False, color=None, size=10):
    font = ("Helvetica", size, "bold") if bold else ("Helvetica", size)
    return tk.Label(parent, text=text,
                    font=font,
                    bg=COLORS["panel"],
                    fg=color or COLORS["text"])


def _section_header(parent, text, color):
    hdr = tk.Frame(parent, bg=color)
    hdr.pack(fill="x")
    tk.Label(hdr, text=text,
             font=("Helvetica", 12, "bold"),
             bg=color, fg="white").pack(side="left", padx=16, pady=10)
    return hdr


class TrackerFrame(tk.Frame):
    """Combined tracker for blood sugar, water, meals, exercise."""

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
        # Page title
        hdr = tk.Frame(self, bg=COLORS["primary"], height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📝  Health Tracker",
                 font=("Helvetica", 14, "bold"),
                 bg=COLORS["primary"], fg="white").pack(
                     side="left", padx=20, pady=12)

        # Sub-tab notebook
        style = ttk.Style()
        style.configure("T.TNotebook", background=COLORS["bg"],
                        borderwidth=0)
        style.configure("T.TNotebook.Tab",
                        background=COLORS["border"],
                        foreground=COLORS["text"],
                        padding=[16, 7],
                        font=("Helvetica", 10, "bold"))
        style.map("T.TNotebook.Tab",
                  background=[("selected", COLORS["panel"])],
                  foreground=[("selected", COLORS["primary"])])

        nb = ttk.Notebook(self, style="T.TNotebook")
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        # Build sub-tabs
        self._blood_sugar_tab(nb)
        self._water_tab(nb)
        self._meals_tab(nb)
        self._exercise_tab(nb)

    # ════════════════════════════════════════════════════════════
    #  BLOOD SUGAR TAB
    # ════════════════════════════════════════════════════════════

    def _blood_sugar_tab(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(frame, text="🩸  Blood Sugar")

        # Split: left=form, right=list
        left  = tk.Frame(frame, bg=COLORS["panel"], width=320)
        right = tk.Frame(frame, bg=COLORS["bg"])
        left.pack(side="left", fill="y", padx=(20, 10), pady=20)
        right.pack(side="right", fill="both", expand=True, pady=20, padx=(0, 20))
        left.pack_propagate(False)

        # ── Log Form ──────────────────────────────────────────
        _section_header(left, "🩸  Log Blood Sugar", COLORS["primary"])

        self.sugar_var     = tk.StringVar()
        self.sugar_type_var = tk.StringVar(value="Random")
        self.sugar_note_var = tk.StringVar()

        for lbl, var, opts in [
            ("Reading (mg/dL) *", self.sugar_var, None),
            ("Notes",             self.sugar_note_var, None),
        ]:
            _label(left, lbl, bold=True).pack(anchor="w", padx=16, pady=(12, 2))
            _entry(left, var).pack(fill="x", padx=16, ipady=7)

        _label(left, "Reading Type *", bold=True).pack(
            anchor="w", padx=16, pady=(12, 2))
        for t in ["Fasting", "Post-Meal", "Random", "Bedtime"]:
            tk.Radiobutton(left, text=t,
                           variable=self.sugar_type_var, value=t,
                           bg=COLORS["panel"], fg=COLORS["text"],
                           selectcolor=COLORS["panel"],
                           font=("Helvetica", 10)).pack(
                               anchor="w", padx=20)

        # Sugar status indicator
        self.sugar_status_lbl = tk.Label(left, text="",
                                          font=("Helvetica", 10),
                                          bg=COLORS["panel"],
                                          fg=COLORS["subtext"])
        self.sugar_status_lbl.pack(anchor="w", padx=16, pady=(8, 0))
        self.sugar_var.trace("w", self._update_sugar_status)

        tk.Button(left, text="💾  Save Reading",
                  command=self._save_sugar,
                  bg=COLORS["primary"], fg="white",
                  font=("Helvetica", 11, "bold"),
                  relief="flat", cursor="hand2").pack(
                      fill="x", padx=16, ipady=10, pady=16)

        # ── History List ───────────────────────────────────────
        _section_header(right, "📋  Recent Readings", COLORS["accent"])
        self.sugar_list_frame = tk.Frame(right, bg=COLORS["bg"])
        self.sugar_list_frame.pack(fill="both", expand=True)
        self._render_sugar_list()

    def _update_sugar_status(self, *_):
        try:
            v = float(self.sugar_var.get())
            if v < SUGAR_LOW:
                self.sugar_status_lbl.config(
                    text="⚠️  LOW – Below normal", fg=COLORS["low"])
            elif v > SUGAR_HIGH:
                self.sugar_status_lbl.config(
                    text="⚠️  HIGH – Above normal", fg=COLORS["danger"])
            else:
                self.sugar_status_lbl.config(
                    text="✅  Normal range", fg=COLORS["accent"])
        except ValueError:
            self.sugar_status_lbl.config(text="", fg=COLORS["subtext"])

    def _save_sugar(self):
        try:
            val = float(self.sugar_var.get().strip())
            if val <= 0 or val > 1000:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Please enter a valid sugar reading (1-1000 mg/dL).")
            return

        db.add_blood_sugar(self.user["id"], val,
                           self.sugar_type_var.get(),
                           self.sugar_note_var.get().strip())

        # Show alert if abnormal
        if val < SUGAR_LOW:
            messagebox.showwarning("⚠️  Low Sugar Alert",
                                   f"Blood sugar is LOW: {val} mg/dL\n"
                                   "Please eat something or contact your doctor!")
        elif val > SUGAR_HIGH:
            messagebox.showwarning("⚠️  High Sugar Alert",
                                   f"Blood sugar is HIGH: {val} mg/dL\n"
                                   "Please take your medication and consult your doctor!")
        else:
            messagebox.showinfo("✅  Saved",
                                f"Reading of {val} mg/dL logged successfully!")

        self.sugar_var.set("")
        self.sugar_note_var.set("")
        self._render_sugar_list()

    def _render_sugar_list(self):
        for w in self.sugar_list_frame.winfo_children():
            w.destroy()

        records = db.get_blood_sugar_records(self.user["id"], limit=15)
        if not records:
            tk.Label(self.sugar_list_frame,
                     text="No readings yet. Add your first reading!",
                     font=("Helvetica", 10),
                     bg=COLORS["bg"], fg=COLORS["subtext"]).pack(pady=30)
            return

        cols = ["Date & Time", "mg/dL", "Type", "Status"]
        widths = [20, 10, 12, 10]
        hdr = tk.Frame(self.sugar_list_frame, bg=COLORS["border"])
        hdr.pack(fill="x")
        for col, w in zip(cols, widths):
            tk.Label(hdr, text=col, width=w,
                     font=("Helvetica", 9, "bold"),
                     bg=COLORS["border"], fg=COLORS["text"],
                     anchor="w").pack(side="left", padx=6, pady=6)

        for i, rec in enumerate(records):
            bg = COLORS["panel"] if i % 2 == 0 else "#F0F7FF"
            row = tk.Frame(self.sugar_list_frame, bg=bg)
            row.pack(fill="x")

            v = rec["reading"]
            if v < SUGAR_LOW:
                status, sc = "Low",    COLORS["low"]
            elif v > SUGAR_HIGH:
                status, sc = "High",   COLORS["danger"]
            else:
                status, sc = "Normal", COLORS["accent"]

            for val, w, clr in [
                (rec["recorded_at"][:16], 20, COLORS["text"]),
                (f"{v:.1f}", 10, sc),
                (rec["reading_type"], 12, COLORS["subtext"]),
                (status, 10, sc),
            ]:
                tk.Label(row, text=val, width=w,
                         font=("Helvetica", 9),
                         bg=bg, fg=clr,
                         anchor="w").pack(side="left", padx=6, pady=5)

    # ════════════════════════════════════════════════════════════
    #  WATER TAB
    # ════════════════════════════════════════════════════════════

    def _water_tab(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(frame, text="💧  Water Intake")

        content = tk.Frame(frame, bg=COLORS["bg"])
        content.pack(expand=True, pady=30)

        # Big water display
        total = db.get_water_today(self.user["id"])
        goal  = 2500
        pct   = min(int((total / goal) * 100), 100)

        tk.Label(content, text="💧",
                 font=("Helvetica", 64),
                 bg=COLORS["bg"]).pack()

        self.water_total_lbl = tk.Label(
            content, text=f"{total} ml",
            font=("Helvetica", 36, "bold"),
            bg=COLORS["bg"], fg=COLORS["low"])
        self.water_total_lbl.pack()

        self.water_pct_lbl = tk.Label(
            content, text=f"{pct}% of daily goal (2500 ml)",
            font=("Helvetica", 12),
            bg=COLORS["bg"], fg=COLORS["subtext"])
        self.water_pct_lbl.pack(pady=(4, 24))

        # Progress bar
        pb_frame = tk.Frame(content, bg=COLORS["border"],
                            height=18, width=380)
        pb_frame.pack()
        pb_frame.pack_propagate(False)
        self.water_pb = tk.Frame(pb_frame,
                                  bg=COLORS["low"],
                                  height=18,
                                  width=int(380 * pct / 100))
        self.water_pb.pack(side="left")

        # Quick add buttons
        tk.Label(content, text="Add Water Intake:",
                 font=("Helvetica", 11, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(24, 8))

        btn_row = tk.Frame(content, bg=COLORS["bg"])
        btn_row.pack()

        for ml in [150, 200, 250, 300, 500]:
            tk.Button(btn_row, text=f"{ml} ml",
                      command=lambda m=ml: self._add_water(m),
                      bg=COLORS["low"], fg="white",
                      font=("Helvetica", 11, "bold"),
                      relief="flat", cursor="hand2",
                      width=7).pack(side="left", padx=5, ipady=8)

        # Custom amount
        tk.Label(content, text="Custom amount (ml):",
                 font=("Helvetica", 10),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(16, 4))
        custom_row = tk.Frame(content, bg=COLORS["bg"])
        custom_row.pack()

        self.custom_water_var = tk.StringVar()
        _entry(custom_row, self.custom_water_var,
               width=12).pack(side="left", ipady=7, padx=(0, 8))
        tk.Button(custom_row, text="Add",
                  command=self._add_custom_water,
                  bg=COLORS["accent"], fg="white",
                  font=("Helvetica", 10, "bold"),
                  relief="flat", cursor="hand2").pack(
                      side="left", ipady=7, ipadx=16)

    def _add_water(self, ml):
        db.add_water(self.user["id"], ml)
        self._refresh_water_display()
        messagebox.showinfo("💧 Logged", f"{ml} ml of water added!")

    def _add_custom_water(self):
        try:
            ml = int(self.custom_water_var.get().strip())
            if ml <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Enter a valid amount in ml.")
            return
        db.add_water(self.user["id"], ml)
        self.custom_water_var.set("")
        self._refresh_water_display()
        messagebox.showinfo("💧 Logged", f"{ml} ml of water added!")

    def _refresh_water_display(self):
        total = db.get_water_today(self.user["id"])
        pct   = min(int((total / 2500) * 100), 100)
        self.water_total_lbl.config(text=f"{total} ml")
        self.water_pct_lbl.config(text=f"{pct}% of daily goal (2500 ml)")
        self.water_pb.config(width=int(380 * pct / 100))

    # ════════════════════════════════════════════════════════════
    #  MEALS TAB
    # ════════════════════════════════════════════════════════════

    def _meals_tab(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(frame, text="🥗  Meal & Diet")

        left  = tk.Frame(frame, bg=COLORS["panel"], width=320)
        right = tk.Frame(frame, bg=COLORS["bg"])
        left.pack(side="left", fill="y", padx=(20, 10), pady=20)
        right.pack(side="right", fill="both", expand=True, pady=20, padx=(0, 20))
        left.pack_propagate(False)

        _section_header(left, "🥗  Log Meal", COLORS["accent"])

        self.meal_type_var  = tk.StringVar(value="Breakfast")
        self.meal_food_var  = tk.StringVar()
        self.meal_cal_var   = tk.StringVar()
        self.meal_carb_var  = tk.StringVar()
        self.meal_note_var  = tk.StringVar()

        _label(left, "Meal Type *", bold=True).pack(anchor="w", padx=16, pady=(12, 2))
        meal_types = ["Breakfast", "Lunch", "Dinner", "Snack", "Pre-workout", "Other"]
        meal_dd = ttk.Combobox(left, textvariable=self.meal_type_var,
                               values=meal_types, state="readonly",
                               font=("Helvetica", 10))
        meal_dd.pack(fill="x", padx=16, ipady=4, pady=(0, 8))

        for lbl, var in [
            ("Food Items *",  self.meal_food_var),
            ("Calories",      self.meal_cal_var),
            ("Carbs (g)",     self.meal_carb_var),
            ("Notes",         self.meal_note_var),
        ]:
            _label(left, lbl, bold=True).pack(anchor="w", padx=16, pady=(8, 2))
            _entry(left, var).pack(fill="x", padx=16, ipady=7)

        tk.Button(left, text="💾  Log Meal",
                  command=self._save_meal,
                  bg=COLORS["accent"], fg="white",
                  font=("Helvetica", 11, "bold"),
                  relief="flat", cursor="hand2").pack(
                      fill="x", padx=16, ipady=10, pady=16)

        # Today's summary
        _section_header(right, "📋  Today's Meals", COLORS["primary"])
        self.meal_list_frame = tk.Frame(right, bg=COLORS["bg"])
        self.meal_list_frame.pack(fill="both", expand=True)
        self._render_meal_list()

    def _save_meal(self):
        food = self.meal_food_var.get().strip()
        if not food:
            messagebox.showwarning("Missing", "Please enter food items.")
            return

        try:
            cal  = int(self.meal_cal_var.get().strip() or 0)
            carb = float(self.meal_carb_var.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid", "Calories must be a number.")
            return

        db.add_meal(self.user["id"], self.meal_type_var.get(),
                    food, cal, carb, self.meal_note_var.get().strip())

        messagebox.showinfo("✅ Saved", "Meal logged successfully!")
        self.meal_food_var.set("")
        self.meal_cal_var.set("")
        self.meal_carb_var.set("")
        self.meal_note_var.set("")
        self._render_meal_list()

    def _render_meal_list(self):
        for w in self.meal_list_frame.winfo_children():
            w.destroy()

        records = db.get_meals_today(self.user["id"])
        if not records:
            tk.Label(self.meal_list_frame,
                     text="No meals logged today.",
                     font=("Helvetica", 10),
                     bg=COLORS["bg"], fg=COLORS["subtext"]).pack(pady=30)
            return

        total_cal  = sum(m["calories"] or 0 for m in records)
        total_carb = sum(m["carbs"] or 0 for m in records)

        # Totals bar
        tot = tk.Frame(self.meal_list_frame, bg=COLORS["border"])
        tot.pack(fill="x")
        tk.Label(tot, text=f"Total Today: {total_cal} kcal  |  {total_carb}g carbs",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["border"], fg=COLORS["text"]).pack(
                     side="left", padx=12, pady=6)

        for i, m in enumerate(records):
            bg = COLORS["panel"] if i % 2 == 0 else "#F0F7FF"
            row = tk.Frame(self.meal_list_frame, bg=bg)
            row.pack(fill="x", padx=4, pady=1)

            tk.Label(row, text=m["meal_type"], width=12,
                     font=("Helvetica", 10, "bold"),
                     bg=bg, fg=COLORS["primary"],
                     anchor="w").pack(side="left", padx=8, pady=6)
            tk.Label(row, text=m["food_items"], width=30,
                     font=("Helvetica", 9), bg=bg,
                     fg=COLORS["text"], anchor="w",
                     wraplength=220).pack(side="left")
            tk.Label(row, text=f"{m['calories'] or 0} kcal",
                     font=("Helvetica", 9),
                     bg=bg, fg=COLORS["warn"]).pack(side="left", padx=8)
            tk.Label(row, text=f"{m['carbs'] or 0}g",
                     font=("Helvetica", 9),
                     bg=bg, fg=COLORS["accent"]).pack(side="left")

    # ════════════════════════════════════════════════════════════
    #  EXERCISE TAB
    # ════════════════════════════════════════════════════════════

    def _exercise_tab(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(frame, text="🏃  Exercise")

        left  = tk.Frame(frame, bg=COLORS["panel"], width=320)
        right = tk.Frame(frame, bg=COLORS["bg"])
        left.pack(side="left", fill="y", padx=(20, 10), pady=20)
        right.pack(side="right", fill="both", expand=True, pady=20, padx=(0, 20))
        left.pack_propagate(False)

        _section_header(left, "🏃  Log Exercise", "#9B59B6")

        self.ex_activity_var = tk.StringVar(value="Walking")
        self.ex_duration_var = tk.StringVar()
        self.ex_dist_var     = tk.StringVar()
        self.ex_cal_var      = tk.StringVar()
        self.ex_note_var     = tk.StringVar()

        _label(left, "Activity *", bold=True).pack(anchor="w", padx=16, pady=(12, 2))
        activities = ["Walking", "Running", "Cycling", "Swimming",
                      "Yoga", "Gym", "Dancing", "Other"]
        ttk.Combobox(left, textvariable=self.ex_activity_var,
                     values=activities, state="readonly",
                     font=("Helvetica", 10)).pack(
                         fill="x", padx=16, ipady=4, pady=(0, 8))

        for lbl, var in [
            ("Duration (min) *",    self.ex_duration_var),
            ("Distance (km)",       self.ex_dist_var),
            ("Calories Burned",     self.ex_cal_var),
            ("Notes",               self.ex_note_var),
        ]:
            _label(left, lbl, bold=True).pack(anchor="w", padx=16, pady=(8, 2))
            _entry(left, var).pack(fill="x", padx=16, ipady=7)

        tk.Button(left, text="💾  Log Exercise",
                  command=self._save_exercise,
                  bg="#9B59B6", fg="white",
                  font=("Helvetica", 11, "bold"),
                  relief="flat", cursor="hand2").pack(
                      fill="x", padx=16, ipady=10, pady=16)

        # Today's sessions
        _section_header(right, "📋  Today's Exercise", COLORS["primary"])
        self.ex_list_frame = tk.Frame(right, bg=COLORS["bg"])
        self.ex_list_frame.pack(fill="both", expand=True)
        self._render_exercise_list()

    def _save_exercise(self):
        try:
            dur = int(self.ex_duration_var.get().strip())
            if dur <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Enter a valid duration in minutes.")
            return

        dist = 0.0
        try:
            dist = float(self.ex_dist_var.get().strip() or 0)
        except ValueError:
            pass

        cal = 0
        try:
            cal = int(self.ex_cal_var.get().strip() or 0)
        except ValueError:
            pass

        db.add_exercise(self.user["id"],
                        self.ex_activity_var.get(),
                        dur, dist, cal,
                        self.ex_note_var.get().strip())

        messagebox.showinfo("✅ Saved", "Exercise session logged!")
        self.ex_duration_var.set("")
        self.ex_dist_var.set("")
        self.ex_cal_var.set("")
        self.ex_note_var.set("")
        self._render_exercise_list()

    def _render_exercise_list(self):
        for w in self.ex_list_frame.winfo_children():
            w.destroy()

        records = db.get_exercise_today(self.user["id"])
        if not records:
            tk.Label(self.ex_list_frame,
                     text="No exercise logged today.",
                     font=("Helvetica", 10),
                     bg=COLORS["bg"], fg=COLORS["subtext"]).pack(pady=30)
            return

        total_min = sum(e["duration_min"] for e in records)
        total_cal = sum(e["calories_burned"] or 0 for e in records)

        tot = tk.Frame(self.ex_list_frame, bg=COLORS["border"])
        tot.pack(fill="x")
        tk.Label(tot, text=f"Today: {total_min} min  |  ~{total_cal} cal burned",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["border"], fg=COLORS["text"]).pack(
                     side="left", padx=12, pady=6)

        for i, ex in enumerate(records):
            bg = COLORS["panel"] if i % 2 == 0 else "#F0F7FF"
            row = tk.Frame(self.ex_list_frame, bg=bg)
            row.pack(fill="x", padx=4, pady=1)

            tk.Label(row, text=f"🏃 {ex['activity']}", width=14,
                     font=("Helvetica", 10, "bold"),
                     bg=bg, fg="#9B59B6", anchor="w").pack(
                         side="left", padx=8, pady=6)
            tk.Label(row, text=f"{ex['duration_min']} min",
                     font=("Helvetica", 10),
                     bg=bg, fg=COLORS["text"]).pack(side="left", padx=8)
            tk.Label(row, text=f"{ex['distance_km'] or 0} km",
                     font=("Helvetica", 10),
                     bg=bg, fg=COLORS["subtext"]).pack(side="left", padx=8)
            tk.Label(row, text=f"{ex['calories_burned'] or 0} cal",
                     font=("Helvetica", 10),
                     bg=bg, fg=COLORS["warn"]).pack(side="left", padx=8)
