"""
dashboard.py - Main Dashboard Screen
Shows summary cards: sugar, water, exercise, BMI
Includes weekly blood sugar line chart
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import database as db

# Matplotlib for embedded chart
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime

# ── Colors (shared palette) ──────────────────────────────────────────────────
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
    "normal":   "#27AE60",
    "high":     "#E74C3C",
}

SUGAR_LOW  = 70    # mg/dL — alert if below
SUGAR_HIGH = 180   # mg/dL — alert if above


class DashboardFrame(tk.Frame):
    """Main dashboard embedded inside the notebook/tab."""

    def __init__(self, parent, user, app_ref):
        super().__init__(parent, bg=COLORS["bg"])
        self.user = user
        self.app  = app_ref   # Reference to main app for navigation
        self._build()

    def refresh(self):
        """Reload all widgets with fresh DB data."""
        for widget in self.winfo_children():
            widget.destroy()
        self._build()

    # ── BUILD ────────────────────────────────────────────────────────────────

    def _build(self):
        """Construct dashboard layout."""
        # Header bar
        self._header()

        # Scrollable content
        canvas = tk.Canvas(self, bg=COLORS["bg"],
                           highlightthickness=0)
        vsb = tk.Scrollbar(self, orient="vertical",
                           command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        content = tk.Frame(canvas, bg=COLORS["bg"])
        cw = canvas.create_window((0, 0), window=content,
                                  anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cw, width=e.width))
        content.bind("<Configure>",
                     lambda e: canvas.configure(
                         scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            -1 * (e.delta // 120), "units"))

        self._summary_cards(content)
        self._sugar_chart(content)
        self._quick_log_buttons(content)
        self._recent_readings(content)

    def _header(self):
        """Top greeting bar."""
        hdr = tk.Frame(self, bg=COLORS["primary"], height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        name = self.user.get("full_name", "Patient")
        hour = datetime.now().hour
        greet = "Good Morning" if hour < 12 else \
                "Good Afternoon" if hour < 17 else "Good Evening"

        tk.Label(hdr, text=f"👋  {greet}, {name.split()[0]}!",
                 font=("Helvetica", 16, "bold"),
                 bg=COLORS["primary"], fg="white").pack(side="left",
                                                        padx=24, pady=16)

        date_str = datetime.now().strftime("%A, %d %B %Y")
        tk.Label(hdr, text=f"📅  {date_str}",
                 font=("Helvetica", 11),
                 bg=COLORS["primary"], fg="#A8D4FF").pack(side="right",
                                                           padx=24)

    # ── SUMMARY CARDS ────────────────────────────────────────────────────────

    def _summary_cards(self, parent):
        """4 KPI cards across the top."""
        row = tk.Frame(parent, bg=COLORS["bg"])
        row.pack(fill="x", padx=20, pady=20)

        # 1. Latest blood sugar
        sugar = db.get_latest_sugar_reading(self.user["id"])
        if sugar:
            val  = sugar["reading"]
            rtype = sugar["reading_type"]
            if val < SUGAR_LOW:
                sc, sl, icon = COLORS["low"],  "LOW",    "⬇️"
            elif val > SUGAR_HIGH:
                sc, sl, icon = COLORS["high"], "HIGH",   "⬆️"
            else:
                sc, sl, icon = COLORS["normal"],"Normal","✅"
            sugar_text  = f"{val} mg/dL"
            sugar_sub   = f"{icon} {sl} · {rtype}"
            sugar_color = sc
        else:
            sugar_text  = "No data"
            sugar_sub   = "Add a reading"
            sugar_color = COLORS["subtext"]

        # 2. Today's water
        water_ml   = db.get_water_today(self.user["id"])
        water_pct  = min(int((water_ml / 2500) * 100), 100)
        water_text = f"{water_ml} ml"
        water_sub  = f"💧 {water_pct}% of daily goal"

        # 3. Today's exercise
        exercises  = db.get_exercise_today(self.user["id"])
        total_min  = sum(e["duration_min"] for e in exercises)
        ex_text    = f"{total_min} min"
        ex_sub     = f"🏃 {len(exercises)} session(s) today"

        # 4. BMI
        bmi_rec    = db.get_latest_bmi(self.user["id"])
        if bmi_rec:
            bmi_text = f"{bmi_rec['bmi']}"
            bmi_sub  = f"⚖️  {bmi_rec['category']}"
        else:
            bmi_text = "N/A"
            bmi_sub  = "Calculate BMI"

        cards = [
            ("🩸 Blood Sugar", sugar_text, sugar_sub,  sugar_color),
            ("💧 Water Today", water_text, water_sub,  COLORS["low"]),
            ("🏃 Exercise",    ex_text,    ex_sub,     COLORS["accent"]),
            ("⚖️  BMI",        bmi_text,   bmi_sub,    COLORS["warn"]),
        ]

        for i, (title, val, sub, color) in enumerate(cards):
            card = tk.Frame(row, bg=COLORS["panel"],
                            highlightbackground=color,
                            highlightthickness=2)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            row.columnconfigure(i, weight=1)

            # Colour accent stripe
            stripe = tk.Frame(card, bg=color, height=5)
            stripe.pack(fill="x")

            tk.Label(card, text=title,
                     font=("Helvetica", 10, "bold"),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(
                         anchor="w", padx=16, pady=(12, 2))

            tk.Label(card, text=val,
                     font=("Helvetica", 22, "bold"),
                     bg=COLORS["panel"], fg=color).pack(
                         anchor="w", padx=16)

            tk.Label(card, text=sub,
                     font=("Helvetica", 9),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(
                         anchor="w", padx=16, pady=(2, 14))

    # ── SUGAR CHART ──────────────────────────────────────────────────────────

    def _sugar_chart(self, parent):
        """Embedded Matplotlib chart: 7-day blood sugar trend."""
        section = tk.Frame(parent, bg=COLORS["panel"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
        section.pack(fill="x", padx=20, pady=(0, 16))

        # Section header
        hdr = tk.Frame(section, bg=COLORS["primary"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="📊  Weekly Blood Sugar Trend",
                 font=("Helvetica", 12, "bold"),
                 bg=COLORS["primary"], fg="white").pack(
                     side="left", padx=16, pady=10)

        records = db.get_blood_sugar_last7days(self.user["id"])

        if not records:
            tk.Label(section, text="No blood sugar data yet.\n"
                     "Go to Tracker → Blood Sugar to add readings.",
                     font=("Helvetica", 11),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(pady=40)
            return

        # Parse data
        times    = [datetime.strptime(r["recorded_at"], "%Y-%m-%d %H:%M:%S")
                    for r in records]
        readings = [r["reading"] for r in records]

        # Draw chart
        fig, ax = plt.subplots(figsize=(10, 3.2), facecolor=COLORS["panel"])
        ax.set_facecolor("#F8FCFF")

        # Danger zones
        ax.axhspan(0,   SUGAR_LOW,  alpha=0.12, color=COLORS["low"],
                   label="Low (<70)")
        ax.axhspan(SUGAR_HIGH, 400, alpha=0.12, color=COLORS["high"],
                   label="High (>180)")
        ax.axhline(SUGAR_LOW,  color=COLORS["low"],  linewidth=1,
                   linestyle="--", alpha=0.6)
        ax.axhline(SUGAR_HIGH, color=COLORS["high"], linewidth=1,
                   linestyle="--", alpha=0.6)

        ax.plot(times, readings, color=COLORS["primary"],
                linewidth=2.5, marker="o", markersize=5,
                markerfacecolor="white", markeredgecolor=COLORS["primary"],
                markeredgewidth=2, label="Blood Sugar")

        # Colour fill under curve
        ax.fill_between(times, readings,
                        alpha=0.15, color=COLORS["primary"])

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        fig.autofmt_xdate()

        ax.set_ylabel("mg/dL", fontsize=9, color=COLORS["subtext"])
        ax.set_ylim(0, max(400, max(readings) + 40))
        ax.tick_params(colors=COLORS["subtext"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["border"])

        ax.legend(loc="upper right", fontsize=8, framealpha=0.8)
        plt.tight_layout(pad=0.5)

        canvas = FigureCanvasTkAgg(fig, master=section)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
        plt.close(fig)

    # ── QUICK LOG BUTTONS ────────────────────────────────────────────────────

    def _quick_log_buttons(self, parent):
        """Quick-action row for most common tasks."""
        section = tk.Frame(parent, bg=COLORS["bg"])
        section.pack(fill="x", padx=20, pady=(0, 16))

        tk.Label(section, text="⚡  Quick Actions",
                 font=("Helvetica", 11, "bold"),
                 bg=COLORS["bg"], fg=COLORS["primary"]).pack(
                     anchor="w", pady=(0, 8))

        btn_row = tk.Frame(section, bg=COLORS["bg"])
        btn_row.pack(fill="x")

        quick = [
            ("🩸 Log Sugar",    COLORS["primary"], lambda: self.app.switch_tab("tracker")),
            ("💧 Log Water",    COLORS["low"],     lambda: self.app.switch_tab("tracker")),
            ("🥗 Log Meal",     COLORS["accent"],  lambda: self.app.switch_tab("tracker")),
            ("🏃 Log Exercise", "#9B59B6",         lambda: self.app.switch_tab("tracker")),
            ("🚨 Emergency",    COLORS["danger"],  self._emergency_alert),
        ]

        for label, color, cmd in quick:
            btn = tk.Button(btn_row, text=label, command=cmd,
                            bg=color, fg="white",
                            font=("Helvetica", 10, "bold"),
                            relief="flat", cursor="hand2",
                            activebackground=color,
                            activeforeground="white")
            btn.pack(side="left", padx=4, ipady=8, ipadx=6)

    # ── RECENT READINGS ──────────────────────────────────────────────────────

    def _recent_readings(self, parent):
        """Table of last 8 blood sugar readings."""
        section = tk.Frame(parent, bg=COLORS["panel"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
        section.pack(fill="x", padx=20, pady=(0, 20))

        hdr = tk.Frame(section, bg=COLORS["accent"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="🩸  Recent Blood Sugar Readings",
                 font=("Helvetica", 12, "bold"),
                 bg=COLORS["accent"], fg="white").pack(
                     side="left", padx=16, pady=10)

        records = db.get_blood_sugar_records(self.user["id"], limit=8)

        if not records:
            tk.Label(section, text="No readings yet.",
                     font=("Helvetica", 10),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(pady=20)
            return

        # Column headers
        cols = ["Date & Time", "Reading (mg/dL)", "Type", "Status", "Notes"]
        widths = [180, 130, 120, 100, 200]
        col_frame = tk.Frame(section, bg=COLORS["border"])
        col_frame.pack(fill="x")
        for col, w in zip(cols, widths):
            tk.Label(col_frame, text=col, width=w // 8,
                     font=("Helvetica", 9, "bold"),
                     bg=COLORS["border"], fg=COLORS["text"],
                     anchor="w").pack(side="left", padx=8, pady=6)

        # Rows
        for i, rec in enumerate(records):
            bg = COLORS["panel"] if i % 2 == 0 else "#F5F9FF"
            row = tk.Frame(section, bg=bg)
            row.pack(fill="x")

            v = rec["reading"]
            if v < SUGAR_LOW:
                status, sc = "Low",    COLORS["low"]
            elif v > SUGAR_HIGH:
                status, sc = "High",   COLORS["high"]
            else:
                status, sc = "Normal", COLORS["accent"]

            dt = rec["recorded_at"][:16]  # Trim seconds

            cells = [dt, f"{v} mg/dL", rec["reading_type"],
                     status, rec.get("notes", "") or "—"]
            for j, (cell, w) in enumerate(zip(cells, widths)):
                color = sc if j == 3 else COLORS["text"]
                tk.Label(row, text=cell, width=w // 8,
                         font=("Helvetica", 9),
                         bg=bg, fg=color,
                         anchor="w").pack(side="left", padx=8, pady=5)

    # ── EMERGENCY ALERT ──────────────────────────────────────────────────────

    def _emergency_alert(self):
        """Show emergency popup with doctor info."""
        user = db.get_user(self.user["id"])
        doctor = user.get("doctor_name", "Your Doctor")
        doc_ph = user.get("doctor_phone", "N/A")

        win = tk.Toplevel(self)
        win.title("🚨 Emergency Alert")
        win.geometry("400x320")
        win.resizable(False, False)
        win.configure(bg=COLORS["danger"])
        win.grab_set()

        tk.Label(win, text="🚨", font=("Helvetica", 48),
                 bg=COLORS["danger"], fg="white").pack(pady=(30, 5))
        tk.Label(win, text="EMERGENCY ALERT",
                 font=("Helvetica", 18, "bold"),
                 bg=COLORS["danger"], fg="white").pack()
        tk.Label(win, text="Contact your doctor or call emergency services!",
                 font=("Helvetica", 10),
                 bg=COLORS["danger"], fg="#FFD0D0",
                 wraplength=340).pack(pady=8)

        info = tk.Frame(win, bg="#C0392B", padx=16, pady=12)
        info.pack(fill="x", padx=24)
        tk.Label(info, text=f"👨‍⚕️  Doctor: {doctor}",
                 font=("Helvetica", 12, "bold"),
                 bg="#C0392B", fg="white").pack(anchor="w")
        tk.Label(info, text=f"📞  Phone: {doc_ph}",
                 font=("Helvetica", 12),
                 bg="#C0392B", fg="white").pack(anchor="w", pady=(4, 0))
        tk.Label(info, text="🆘  Emergency: 112",
                 font=("Helvetica", 12),
                 bg="#C0392B", fg="white").pack(anchor="w", pady=(4, 0))

        tk.Button(win, text="Close",
                  command=win.destroy,
                  bg="white", fg=COLORS["danger"],
                  font=("Helvetica", 11, "bold"),
                  relief="flat").pack(pady=16, ipadx=20, ipady=6)
