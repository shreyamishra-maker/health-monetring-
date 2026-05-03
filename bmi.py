"""
bmi.py - BMI Calculator with history tracking
"""

import tkinter as tk
from tkinter import messagebox
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


def calculate_bmi(weight_kg, height_cm):
    """Return (bmi_value, category_string)."""
    if height_cm <= 0 or weight_kg <= 0:
        return None, None
    h_m  = height_cm / 100
    bmi  = round(weight_kg / (h_m ** 2), 1)
    if bmi < 18.5:
        cat = "Underweight"
    elif bmi < 25:
        cat = "Normal weight"
    elif bmi < 30:
        cat = "Overweight"
    elif bmi < 35:
        cat = "Obese (Class I)"
    elif bmi < 40:
        cat = "Obese (Class II)"
    else:
        cat = "Obese (Class III)"
    return bmi, cat


def _entry(parent, var, **kw):
    return tk.Entry(parent, textvariable=var,
                    bg=COLORS["entry_bg"], fg=COLORS["text"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=COLORS["border"],
                    highlightcolor=COLORS["primary"],
                    font=("Helvetica", 11), bd=0,
                    insertbackground=COLORS["primary"], **kw)


class BMIFrame(tk.Frame):
    """BMI calculator screen."""

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
        hdr = tk.Frame(self, bg="#8E44AD", height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚖️  BMI Calculator",
                 font=("Helvetica", 14, "bold"),
                 bg="#8E44AD", fg="white").pack(
                     side="left", padx=20, pady=12)

        # Main layout
        content = tk.Frame(self, bg=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        left  = tk.Frame(content, bg=COLORS["panel"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1, width=340)
        right = tk.Frame(content, bg=COLORS["bg"])
        left.pack(side="left", fill="y", padx=(0, 16))
        right.pack(side="right", fill="both", expand=True)
        left.pack_propagate(False)

        self._calculator(left)
        self._bmi_chart(right)
        self._history(right)

    # ── CALCULATOR PANEL ─────────────────────────────────────────────────────

    def _calculator(self, parent):
        hdr = tk.Frame(parent, bg="#8E44AD")
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚖️  Calculate BMI",
                 font=("Helvetica", 12, "bold"),
                 bg="#8E44AD", fg="white").pack(
                     side="left", padx=16, pady=10)

        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()

        for lbl, var, unit in [
            ("Weight", self.weight_var, "kg"),
            ("Height", self.height_var, "cm"),
        ]:
            tk.Label(parent, text=f"📏  {lbl} ({unit}) *",
                     font=("Helvetica", 10, "bold"),
                     bg=COLORS["panel"], fg=COLORS["text"],
                     anchor="w").pack(fill="x", padx=16, pady=(16, 2))
            _entry(parent, var).pack(fill="x", padx=16, ipady=8)

        tk.Button(parent, text="⚖️  Calculate BMI",
                  command=self._calculate,
                  bg="#8E44AD", fg="white",
                  font=("Helvetica", 11, "bold"),
                  relief="flat", cursor="hand2").pack(
                      fill="x", padx=16, ipady=10, pady=20)

        # Result display
        self.bmi_result_frame = tk.Frame(parent, bg=COLORS["panel"])
        self.bmi_result_frame.pack(fill="x", padx=16)

        # Last recorded BMI
        last = db.get_latest_bmi(self.user["id"])
        if last:
            tk.Label(parent, text="Last Recorded:",
                     font=("Helvetica", 9),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(
                         anchor="w", padx=16, pady=(16, 2))
            tk.Label(parent,
                     text=f"BMI {last['bmi']} · {last['category']}\n"
                          f"Weight: {last['weight_kg']} kg  "
                          f"Height: {last['height_cm']} cm",
                     font=("Helvetica", 10),
                     bg=COLORS["panel"], fg=COLORS["text"]).pack(
                         anchor="w", padx=16)

        # BMI Reference chart
        ref = tk.Frame(parent, bg="#F0F7FF",
                       highlightbackground=COLORS["border"],
                       highlightthickness=1)
        ref.pack(fill="x", padx=16, pady=20)

        tk.Label(ref, text="BMI Categories",
                 font=("Helvetica", 10, "bold"),
                 bg="#F0F7FF", fg=COLORS["primary"]).pack(
                     anchor="w", padx=10, pady=(8, 4))

        categories = [
            ("< 18.5",  "Underweight", COLORS["low"]),
            ("18.5–24.9", "Normal",      COLORS["accent"]),
            ("25–29.9",  "Overweight",   COLORS["warn"]),
            ("30–34.9",  "Obese (I)",    "#E67E22"),
            ("≥ 35",     "Obese (II+)",  COLORS["danger"]),
        ]
        for rng, cat, color in categories:
            row = tk.Frame(ref, bg="#F0F7FF")
            row.pack(fill="x", padx=10, pady=2)

            # Color dot
            dot = tk.Frame(row, bg=color, width=10, height=10)
            dot.pack(side="left", padx=(0, 6))

            tk.Label(row, text=f"{rng:<12} {cat}",
                     font=("Helvetica", 9),
                     bg="#F0F7FF", fg=COLORS["text"]).pack(side="left")

        tk.Label(ref, text="", bg="#F0F7FF").pack(pady=4)

    def _calculate(self):
        try:
            w = float(self.weight_var.get().strip())
            h = float(self.height_var.get().strip())
            if w <= 0 or h <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Please enter valid weight and height.")
            return

        bmi, cat = calculate_bmi(w, h)

        # Color by category
        colors_map = {
            "Underweight": COLORS["low"],
            "Normal weight": COLORS["accent"],
            "Overweight": COLORS["warn"],
            "Obese (Class I)": "#E67E22",
            "Obese (Class II)": COLORS["danger"],
            "Obese (Class III)": COLORS["danger"],
        }
        color = colors_map.get(cat, COLORS["text"])

        # Clear and show result
        for widget in self.bmi_result_frame.winfo_children():
            widget.destroy()

        result_card = tk.Frame(self.bmi_result_frame,
                               bg=color, padx=20, pady=16)
        result_card.pack(fill="x")

        tk.Label(result_card, text="Your BMI",
                 font=("Helvetica", 10),
                 bg=color, fg="white").pack()
        tk.Label(result_card, text=str(bmi),
                 font=("Helvetica", 36, "bold"),
                 bg=color, fg="white").pack()
        tk.Label(result_card, text=cat,
                 font=("Helvetica", 12, "bold"),
                 bg=color, fg="white").pack()

        # Save to database
        db.add_bmi_record(self.user["id"], w, h, bmi, cat)
        self.refresh()

    # ── BMI HISTORY ──────────────────────────────────────────────────────────

    def _bmi_chart(self, parent):
        """Quick visual bar of BMI scale."""
        pass  # Keeps it clean; history table is sufficient

    def _history(self, parent):
        hdr = tk.Frame(parent, bg=COLORS["primary"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  BMI History",
                 font=("Helvetica", 12, "bold"),
                 bg=COLORS["primary"], fg="white").pack(
                     side="left", padx=16, pady=10)

        records = db.get_bmi_history(self.user["id"], limit=8)
        if not records:
            tk.Label(parent, text="No BMI records yet.",
                     font=("Helvetica", 10),
                     bg=COLORS["bg"], fg=COLORS["subtext"]).pack(pady=20)
            return

        cols = ["Date", "Weight (kg)", "Height (cm)", "BMI", "Category"]
        widths = [18, 12, 12, 10, 16]
        col_frame = tk.Frame(parent, bg=COLORS["border"])
        col_frame.pack(fill="x")
        for col, w in zip(cols, widths):
            tk.Label(col_frame, text=col, width=w,
                     font=("Helvetica", 9, "bold"),
                     bg=COLORS["border"], fg=COLORS["text"],
                     anchor="w").pack(side="left", padx=6, pady=6)

        for i, rec in enumerate(records):
            bg = COLORS["panel"] if i % 2 == 0 else "#F0F7FF"
            row = tk.Frame(parent, bg=bg)
            row.pack(fill="x")

            cat_colors = {
                "Normal weight": COLORS["accent"],
                "Underweight":   COLORS["low"],
            }
            cc = COLORS["warn"] if "Overweight" in rec["category"] else \
                 COLORS["danger"] if "Obese" in rec["category"] else \
                 cat_colors.get(rec["category"], COLORS["text"])

            cells = [
                (rec["recorded_at"][:10], 18, COLORS["text"]),
                (str(rec["weight_kg"]),   12, COLORS["text"]),
                (str(rec["height_cm"]),   12, COLORS["text"]),
                (str(rec["bmi"]),         10, cc),
                (rec["category"],         16, cc),
            ]
            for val, w, clr in cells:
                tk.Label(row, text=val, width=w,
                         font=("Helvetica", 9),
                         bg=bg, fg=clr, anchor="w").pack(
                             side="left", padx=6, pady=5)
