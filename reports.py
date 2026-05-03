"""
reports.py - Health Reports & Analytics
Generates weekly/monthly charts and summary reports
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import database as db

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

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
}

SUGAR_LOW  = 70
SUGAR_HIGH = 180


class ReportsFrame(tk.Frame):
    """Reports and analytics screen."""

    def __init__(self, parent, user, app_ref):
        super().__init__(parent, bg=COLORS["bg"])
        self.user    = user
        self.app     = app_ref
        self.current_period = tk.StringVar(value="7")
        self._build()

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg="#16A085", height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📊  Health Reports & Analytics",
                 font=("Helvetica", 14, "bold"),
                 bg="#16A085", fg="white").pack(
                     side="left", padx=20, pady=12)

        # Controls bar
        ctrl = tk.Frame(self, bg=COLORS["border"], height=44)
        ctrl.pack(fill="x")
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="Period:",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["border"], fg=COLORS["text"]).pack(
                     side="left", padx=(20, 8), pady=12)

        for label, val in [("7 Days", "7"), ("30 Days", "30"), ("All Time", "all")]:
            rb = tk.Radiobutton(ctrl, text=label,
                                variable=self.current_period, value=val,
                                command=self._redraw_charts,
                                bg=COLORS["border"], fg=COLORS["text"],
                                selectcolor=COLORS["border"],
                                font=("Helvetica", 10))
            rb.pack(side="left", padx=8, pady=10)

        tk.Button(ctrl, text="💾  Save Charts as Image",
                  command=self._save_charts,
                  bg=COLORS["primary"], fg="white",
                  font=("Helvetica", 9, "bold"),
                  relief="flat", cursor="hand2").pack(
                      side="right", padx=20, ipady=4)

        # Scrollable chart area
        canvas_outer = tk.Canvas(self, bg=COLORS["bg"],
                                  highlightthickness=0)
        vsb = tk.Scrollbar(self, orient="vertical",
                           command=canvas_outer.yview)
        canvas_outer.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas_outer.pack(fill="both", expand=True)

        self.content = tk.Frame(canvas_outer, bg=COLORS["bg"])
        cw = canvas_outer.create_window((0, 0), window=self.content,
                                         anchor="nw")
        canvas_outer.bind("<Configure>",
                          lambda e: canvas_outer.itemconfig(cw, width=e.width))
        self.content.bind("<Configure>",
                          lambda e: canvas_outer.configure(
                              scrollregion=canvas_outer.bbox("all")))
        canvas_outer.bind_all("<MouseWheel>",
                              lambda e: canvas_outer.yview_scroll(
                                  -1 * (e.delta // 120), "units"))

        self._draw_summary_cards()
        self._redraw_charts()

    # ── SUMMARY STATS ────────────────────────────────────────────────────────

    def _draw_summary_cards(self):
        """Stats overview cards."""
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="x", padx=20, pady=16)

        records = db.get_blood_sugar_last30days(self.user["id"])

        if records:
            readings = [r["reading"] for r in records]
            avg      = round(sum(readings) / len(readings), 1)
            lo       = round(min(readings), 1)
            hi       = round(max(readings), 1)
            high_cnt = sum(1 for r in readings if r > SUGAR_HIGH)
            low_cnt  = sum(1 for r in readings if r < SUGAR_LOW)
        else:
            avg = lo = hi = high_cnt = low_cnt = "N/A"

        stats = [
            ("📊 Avg Sugar (30d)", str(avg) + (" mg/dL" if avg != "N/A" else ""),
             COLORS["primary"]),
            ("⬇️  Min Reading",   str(lo) + (" mg/dL" if lo != "N/A" else ""),
             COLORS["accent"]),
            ("⬆️  Max Reading",   str(hi) + (" mg/dL" if hi != "N/A" else ""),
             COLORS["danger"]),
            ("🔴 High Events",    str(high_cnt), COLORS["warn"]),
            ("🔵 Low Events",     str(low_cnt),  COLORS["low"]),
        ]

        for i, (title, val, color) in enumerate(stats):
            card = tk.Frame(frame, bg=COLORS["panel"],
                            highlightbackground=color,
                            highlightthickness=2, width=120)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            frame.columnconfigure(i, weight=1)

            tk.Frame(card, bg=color, height=4).pack(fill="x")
            tk.Label(card, text=title,
                     font=("Helvetica", 9),
                     bg=COLORS["panel"], fg=COLORS["subtext"],
                     wraplength=110).pack(padx=10, pady=(8, 2))
            tk.Label(card, text=val,
                     font=("Helvetica", 15, "bold"),
                     bg=COLORS["panel"], fg=color).pack(padx=10, pady=(0, 10))

    # ── CHARTS ───────────────────────────────────────────────────────────────

    def _redraw_charts(self):
        """Clear and redraw all charts."""
        # Remove old chart frames
        for w in self.content.winfo_children():
            if hasattr(w, "_is_chart"):
                w.destroy()

        period = self.current_period.get()
        if period == "7":
            records = db.get_blood_sugar_last7days(self.user["id"])
            title_suf = "– Last 7 Days"
        elif period == "30":
            records = db.get_blood_sugar_last30days(self.user["id"])
            title_suf = "– Last 30 Days"
        else:
            records = db.get_blood_sugar_records(self.user["id"], limit=200)
            title_suf = "– All Time"

        self._sugar_line_chart(records, title_suf)
        self._sugar_distribution_chart(records)
        self._water_exercise_chart()

    def _sugar_line_chart(self, records, title_suf):
        """Line chart of blood sugar over time."""
        frame = tk.Frame(self.content, bg=COLORS["panel"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        frame._is_chart = True
        frame.pack(fill="x", padx=20, pady=(0, 16))

        hdr = tk.Frame(frame, bg=COLORS["primary"])
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"🩸  Blood Sugar Trend {title_suf}",
                 font=("Helvetica", 11, "bold"),
                 bg=COLORS["primary"], fg="white").pack(
                     side="left", padx=16, pady=8)

        if not records:
            tk.Label(frame, text="No data available.",
                     font=("Helvetica", 10),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(pady=30)
            return

        # Handle different record formats
        try:
            times    = [datetime.strptime(r["recorded_at"], "%Y-%m-%d %H:%M:%S")
                        for r in records]
        except Exception:
            times = list(range(len(records)))

        readings = [r["reading"] for r in records]

        fig, ax = plt.subplots(figsize=(11, 3.5),
                                facecolor=COLORS["panel"])
        ax.set_facecolor("#F8FCFF")

        ax.axhspan(0, SUGAR_LOW, alpha=0.1, color=COLORS["low"])
        ax.axhspan(SUGAR_HIGH, 500, alpha=0.1, color=COLORS["danger"])
        ax.axhline(SUGAR_LOW,  color=COLORS["low"],    lw=1, ls="--", alpha=0.7)
        ax.axhline(SUGAR_HIGH, color=COLORS["danger"], lw=1, ls="--", alpha=0.7)

        ax.plot(times, readings,
                color=COLORS["primary"], lw=2, marker="o",
                ms=4, markerfacecolor="white",
                markeredgecolor=COLORS["primary"], markeredgewidth=1.5)
        ax.fill_between(times, readings, alpha=0.12, color=COLORS["primary"])

        if isinstance(times[0], datetime):
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
            fig.autofmt_xdate()

        ax.set_ylabel("mg/dL", color=COLORS["subtext"], fontsize=9)
        ax.set_ylim(0, max(400, max(readings) + 40))
        ax.tick_params(colors=COLORS["subtext"], labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor(COLORS["border"])

        plt.tight_layout(pad=0.6)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
        plt.close(fig)

    def _sugar_distribution_chart(self, records):
        """Pie chart: Low / Normal / High distribution."""
        frame = tk.Frame(self.content, bg=COLORS["panel"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        frame._is_chart = True
        frame.pack(fill="x", padx=20, pady=(0, 16))

        hdr = tk.Frame(frame, bg="#8E44AD")
        hdr.pack(fill="x")
        tk.Label(hdr, text="🥧  Blood Sugar Distribution",
                 font=("Helvetica", 11, "bold"),
                 bg="#8E44AD", fg="white").pack(
                     side="left", padx=16, pady=8)

        if not records:
            tk.Label(frame, text="No data available.",
                     font=("Helvetica", 10),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(pady=30)
            return

        readings = [r["reading"] for r in records]
        low_c    = sum(1 for r in readings if r < SUGAR_LOW)
        norm_c   = sum(1 for r in readings if SUGAR_LOW <= r <= SUGAR_HIGH)
        high_c   = sum(1 for r in readings if r > SUGAR_HIGH)
        total    = len(readings)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.2),
                                        facecolor=COLORS["panel"])

        # Pie
        sizes  = [low_c, norm_c, high_c]
        labels = [f"Low (<{SUGAR_LOW})",
                  f"Normal ({SUGAR_LOW}–{SUGAR_HIGH})",
                  f"High (>{SUGAR_HIGH})"]
        colors = [COLORS["low"], COLORS["accent"], COLORS["danger"]]

        non_zero = [(s, l, c) for s, l, c in zip(sizes, labels, colors) if s > 0]
        if non_zero:
            s, l, c = zip(*non_zero)
            ax1.pie(s, labels=l, colors=c, autopct="%1.1f%%",
                    startangle=90, textprops={"fontsize": 9})
        ax1.set_facecolor(COLORS["panel"])
        ax1.set_title("Readings Breakdown", fontsize=10,
                      color=COLORS["text"])

        # Horizontal bar
        bars = ax2.barh(["Low", "Normal", "High"],
                        [low_c, norm_c, high_c],
                        color=[COLORS["low"], COLORS["accent"],
                               COLORS["danger"]],
                        height=0.5)
        for bar, count in zip(bars, [low_c, norm_c, high_c]):
            ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                     f"{count} ({count/total*100:.1f}%)" if total else "0",
                     va="center", fontsize=9, color=COLORS["text"])
        ax2.set_facecolor("#F8FCFF")
        ax2.set_xlabel("Count", fontsize=9, color=COLORS["subtext"])
        ax2.set_title(f"Counts out of {total} readings",
                      fontsize=10, color=COLORS["text"])
        ax2.tick_params(colors=COLORS["subtext"], labelsize=8)
        for sp in ax2.spines.values():
            sp.set_edgecolor(COLORS["border"])

        fig.patch.set_facecolor(COLORS["panel"])
        plt.tight_layout(pad=0.6)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
        plt.close(fig)

    def _water_exercise_chart(self):
        """Bar charts for water intake and exercise over past week."""
        frame = tk.Frame(self.content, bg=COLORS["panel"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        frame._is_chart = True
        frame.pack(fill="x", padx=20, pady=(0, 24))

        hdr = tk.Frame(frame, bg=COLORS["accent"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="💧🏃  Water & Exercise – Last 7 Days",
                 font=("Helvetica", 11, "bold"),
                 bg=COLORS["accent"], fg="white").pack(
                     side="left", padx=16, pady=8)

        water_data = db.get_water_week(self.user["id"])
        ex_data    = db.get_exercise_recent(self.user["id"], limit=30)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3),
                                        facecolor=COLORS["panel"])

        # Water bars
        if water_data:
            days  = [r["day"] for r in water_data]
            amts  = [r["total"] / 1000 for r in water_data]  # litres
            bars  = ax1.bar(range(len(days)), amts,
                            color=COLORS["low"], alpha=0.8, width=0.6)
            ax1.axhline(2.5, color=COLORS["warn"], lw=1.5,
                        ls="--", label="Goal 2.5L")
            ax1.set_xticks(range(len(days)))
            ax1.set_xticklabels([d[-5:] for d in days],
                                 fontsize=8, rotation=30)
            ax1.set_ylabel("Litres", fontsize=9, color=COLORS["subtext"])
            ax1.legend(fontsize=8)
        else:
            ax1.text(0.5, 0.5, "No data", ha="center", va="center",
                     transform=ax1.transAxes,
                     fontsize=10, color=COLORS["subtext"])

        ax1.set_facecolor("#F8FCFF")
        ax1.set_title("Daily Water Intake", fontsize=10, color=COLORS["text"])
        ax1.tick_params(colors=COLORS["subtext"], labelsize=8)
        for sp in ax1.spines.values():
            sp.set_edgecolor(COLORS["border"])

        # Exercise bars – by activity
        if ex_data:
            from collections import defaultdict
            act_dur = defaultdict(int)
            for e in ex_data:
                act_dur[e["activity"]] += e["duration_min"]
            acts = list(act_dur.keys())
            durs = list(act_dur.values())
            colors_ex = ["#9B59B6", COLORS["accent"],
                         COLORS["primary"], COLORS["warn"],
                         COLORS["low"]][:len(acts)]
            ax2.barh(acts, durs, color=colors_ex, alpha=0.85, height=0.5)
            ax2.set_xlabel("Minutes", fontsize=9, color=COLORS["subtext"])
        else:
            ax2.text(0.5, 0.5, "No data", ha="center", va="center",
                     transform=ax2.transAxes,
                     fontsize=10, color=COLORS["subtext"])

        ax2.set_facecolor("#F8FCFF")
        ax2.set_title("Exercise by Activity (7 days)", fontsize=10,
                      color=COLORS["text"])
        ax2.tick_params(colors=COLORS["subtext"], labelsize=8)
        for sp in ax2.spines.values():
            sp.set_edgecolor(COLORS["border"])

        fig.patch.set_facecolor(COLORS["panel"])
        plt.tight_layout(pad=0.6)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
        plt.close(fig)

    # ── SAVE CHARTS ──────────────────────────────────────────────────────────

    def _save_charts(self):
        """Export a combined chart image."""
        records = db.get_blood_sugar_last30days(self.user["id"])

        if not records:
            messagebox.showwarning("No Data",
                                   "No data available to generate a chart.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="Save Health Report Chart"
        )
        if not filepath:
            return

        readings = [r["reading"] for r in records]
        try:
            times = [datetime.strptime(r["recorded_at"], "%Y-%m-%d %H:%M:%S")
                     for r in records]
        except Exception:
            times = list(range(len(records)))

        fig = plt.figure(figsize=(14, 8),
                         facecolor=COLORS["panel"])
        fig.suptitle(
            f"Health Report — {self.user.get('full_name', 'Patient')}\n"
            f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
            fontsize=14, color=COLORS["primary"], y=0.98
        )

        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

        # 1. Line chart
        ax1 = fig.add_subplot(gs[0, :])
        ax1.axhspan(0, SUGAR_LOW, alpha=0.1, color=COLORS["low"])
        ax1.axhspan(SUGAR_HIGH, 500, alpha=0.1, color=COLORS["danger"])
        ax1.plot(times, readings, color=COLORS["primary"],
                 lw=2, marker="o", ms=4)
        ax1.fill_between(times, readings, alpha=0.12, color=COLORS["primary"])
        ax1.set_title("Blood Sugar Trend (30 Days)", color=COLORS["text"])
        ax1.set_ylabel("mg/dL", color=COLORS["subtext"])
        ax1.set_facecolor("#F8FCFF")
        if isinstance(times[0], datetime):
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
            fig.autofmt_xdate()

        # 2. Distribution pie
        low_c  = sum(1 for r in readings if r < SUGAR_LOW)
        norm_c = sum(1 for r in readings if SUGAR_LOW <= r <= SUGAR_HIGH)
        high_c = sum(1 for r in readings if r > SUGAR_HIGH)
        ax2 = fig.add_subplot(gs[1, 0])
        non_zero = [(v, l, c) for v, l, c in [
            (low_c, "Low", COLORS["low"]),
            (norm_c, "Normal", COLORS["accent"]),
            (high_c, "High", COLORS["danger"]),
        ] if v > 0]
        if non_zero:
            vs, ls, cs = zip(*non_zero)
            ax2.pie(vs, labels=ls, colors=cs, autopct="%1.0f%%",
                    textprops={"fontsize": 9})
        ax2.set_title("Reading Distribution", color=COLORS["text"])

        # 3. Water
        water_data = db.get_water_week(self.user["id"])
        ax3 = fig.add_subplot(gs[1, 1])
        if water_data:
            days = [r["day"][-5:] for r in water_data]
            amts = [r["total"] / 1000 for r in water_data]
            ax3.bar(days, amts, color=COLORS["low"], alpha=0.8)
            ax3.axhline(2.5, color=COLORS["warn"], lw=1.5, ls="--", label="Goal")
            ax3.set_ylabel("Litres")
            ax3.tick_params(labelsize=8)
        ax3.set_title("Daily Water Intake (7d)", color=COLORS["text"])
        ax3.set_facecolor("#F8FCFF")

        plt.savefig(filepath, dpi=150, bbox_inches="tight",
                    facecolor=COLORS["panel"])
        plt.close(fig)
        messagebox.showinfo("✅ Saved",
                            f"Report saved to:\n{filepath}")
