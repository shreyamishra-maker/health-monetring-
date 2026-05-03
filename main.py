"""
main.py - DiabeteCare Patient Management Application
Entry point: initialises DB, shows login, launches main app
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
from datetime import datetime

# ── Module imports ────────────────────────────────────────────────────────────
import database as db
from login     import LoginWindow
from dashboard import DashboardFrame
from tracker   import TrackerFrame
from reminder  import ReminderFrame
from bmi       import BMIFrame
from reports   import ReportsFrame
from profile   import ProfileFrame

# ── Shared color palette ──────────────────────────────────────────────────────
COLORS = {
    "bg":       "#F0F7FF",
    "panel":    "#FFFFFF",
    "primary":  "#1A6FB5",
    "accent":   "#27AE60",
    "text":     "#2C3E50",
    "subtext":  "#7F8C8D",
    "sidebar":  "#0D4F8C",   # Darker blue sidebar
    "sidebar_hover": "#1565A8",
    "sidebar_active": "#27AE60",
    "border":   "#D5E8F7",
    "danger":   "#E74C3C",
    "warn":     "#F39C12",
}

APP_TITLE   = "DiabeteCare — Patient Management System"
WINDOW_SIZE = "1200x720"


# ════════════════════════════════════════════════════════════
#  MAIN APPLICATION WINDOW
# ════════════════════════════════════════════════════════════

class DiabeteCareApp:
    """Main application shell with sidebar navigation."""

    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS["bg"])

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - 1200) // 2
        y = (self.root.winfo_screenheight() -  720) // 2
        self.root.geometry(f"1200x720+{x}+{y}")

        self.current_tab  = None
        self.frames       = {}
        self.nav_buttons  = {}

        self._build_layout()
        self._build_sidebar()
        self._build_content_area()
        self.switch_tab("dashboard")

        # Start medicine reminder background thread
        self._start_reminder_thread()

    # ── LAYOUT ───────────────────────────────────────────────────────────────

    def _build_layout(self):
        """Top titlebar + horizontal split (sidebar | content)."""
        # Top bar
        topbar = tk.Frame(self.root, bg=COLORS["primary"], height=44)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="🏥  DiabeteCare",
                 font=("Helvetica", 13, "bold"),
                 bg=COLORS["primary"], fg="white").pack(
                     side="left", padx=16, pady=10)

        # User info
        name = self.user.get("full_name", "Patient")
        tk.Label(topbar, text=f"👤  {name}",
                 font=("Helvetica", 10),
                 bg=COLORS["primary"], fg="#A8D4FF").pack(
                     side="right", padx=16)

        # Clock label
        self.clock_lbl = tk.Label(topbar, text="",
                                   font=("Helvetica", 10),
                                   bg=COLORS["primary"], fg="#A8D4FF")
        self.clock_lbl.pack(side="right", padx=8)
        self._update_clock()

        # Horizontal panes
        self.main_pane = tk.Frame(self.root, bg=COLORS["bg"])
        self.main_pane.pack(fill="both", expand=True)

    def _update_clock(self):
        """Update clock every second."""
        now = datetime.now().strftime("%H:%M:%S  %d %b %Y")
        self.clock_lbl.config(text=f"🕐  {now}")
        self.root.after(1000, self._update_clock)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        """Left navigation sidebar."""
        self.sidebar = tk.Frame(self.main_pane,
                                bg=COLORS["sidebar"], width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Patient avatar
        av = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        av.pack(fill="x", pady=(20, 8))

        tk.Label(av, text="👤",
                 font=("Helvetica", 32),
                 bg=COLORS["sidebar"], fg="white").pack()

        name = self.user.get("full_name", "Patient")
        tk.Label(av, text=name.split()[0],
                 font=("Helvetica", 11, "bold"),
                 bg=COLORS["sidebar"], fg="white").pack()

        diab = self.user.get("diabetes_type", "")
        tk.Label(av, text=diab,
                 font=("Helvetica", 9),
                 bg=COLORS["sidebar"], fg="#A8D4FF").pack(pady=(2, 0))

        # Divider
        tk.Frame(self.sidebar, bg="#1E5F9C", height=1).pack(
            fill="x", padx=20, pady=12)

        # Nav items
        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("tracker",   "📝  Health Tracker"),
            ("reminder",  "💊  Medicines"),
            ("bmi",       "⚖️   BMI Calculator"),
            ("reports",   "📊  Reports"),
            ("profile",   "👤  My Profile"),
        ]

        for key, label in nav_items:
            btn = tk.Button(self.sidebar,
                            text=label,
                            command=lambda k=key: self.switch_tab(k),
                            anchor="w",
                            font=("Helvetica", 10, "bold"),
                            bg=COLORS["sidebar"],
                            fg="white",
                            relief="flat",
                            cursor="hand2",
                            bd=0,
                            padx=20,
                            pady=10,
                            activebackground=COLORS["sidebar_hover"],
                            activeforeground="white")
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

            # Hover effects
            btn.bind("<Enter>",
                     lambda e, b=btn: b.config(bg=COLORS["sidebar_hover"]))
            btn.bind("<Leave>",
                     lambda e, b=btn, k=key: b.config(
                         bg=COLORS["sidebar_active"]
                         if self.current_tab == k
                         else COLORS["sidebar"]))

        # Bottom: Emergency + Logout
        tk.Frame(self.sidebar, bg="#1E5F9C", height=1).pack(
            fill="x", padx=20, pady=12)

        tk.Button(self.sidebar,
                  text="🚨  Emergency",
                  command=self._emergency_alert,
                  anchor="w",
                  font=("Helvetica", 10, "bold"),
                  bg=COLORS["danger"],
                  fg="white", relief="flat",
                  cursor="hand2", padx=20, pady=10,
                  activebackground="#C0392B",
                  activeforeground="white").pack(fill="x")

        tk.Button(self.sidebar,
                  text="🚪  Logout",
                  command=self._logout,
                  anchor="w",
                  font=("Helvetica", 10),
                  bg=COLORS["sidebar"],
                  fg="#A8D4FF", relief="flat",
                  cursor="hand2", padx=20, pady=8,
                  activebackground=COLORS["sidebar_hover"],
                  activeforeground="white").pack(
                      fill="x", side="bottom")

        # App version
        tk.Label(self.sidebar, text="v1.0  |  Python + Tkinter",
                 font=("Helvetica", 8),
                 bg=COLORS["sidebar"], fg="#5D8FB5").pack(
                     side="bottom", pady=4)

    # ── CONTENT AREA ─────────────────────────────────────────────────────────

    def _build_content_area(self):
        """Right side where page frames are shown."""
        self.content_area = tk.Frame(self.main_pane, bg=COLORS["bg"])
        self.content_area.pack(side="right", fill="both", expand=True)

    def switch_tab(self, tab_key):
        """Show the requested tab; create frame if first visit."""
        if self.current_tab == tab_key:
            # Refresh current tab
            if tab_key in self.frames:
                self.frames[tab_key].refresh()
            return

        # Hide current
        if self.current_tab and self.current_tab in self.frames:
            self.frames[self.current_tab].pack_forget()

        # Reset previous active button
        if self.current_tab and self.current_tab in self.nav_buttons:
            self.nav_buttons[self.current_tab].config(
                bg=COLORS["sidebar"])

        # Build frame if not yet created
        if tab_key not in self.frames:
            frame_cls = {
                "dashboard": DashboardFrame,
                "tracker":   TrackerFrame,
                "reminder":  ReminderFrame,
                "bmi":       BMIFrame,
                "reports":   ReportsFrame,
                "profile":   ProfileFrame,
            }.get(tab_key)

            if frame_cls:
                frame = frame_cls(self.content_area, self.user, self)
                self.frames[tab_key] = frame
            else:
                return

        # Show and mark active
        self.frames[tab_key].pack(fill="both", expand=True)
        self.current_tab = tab_key

        if tab_key in self.nav_buttons:
            self.nav_buttons[tab_key].config(bg=COLORS["sidebar_active"])

    # ── EMERGENCY ────────────────────────────────────────────────────────────

    def _emergency_alert(self):
        """Emergency popup from sidebar."""
        user    = db.get_user(self.user["id"])
        doctor  = user.get("doctor_name", "Your Doctor")
        doc_ph  = user.get("doctor_phone", "N/A")

        win = tk.Toplevel(self.root)
        win.title("🚨 Emergency Alert")
        win.geometry("420x340")
        win.resizable(False, False)
        win.configure(bg=COLORS["danger"])
        win.grab_set()

        cx = (self.root.winfo_screenwidth()  - 420) // 2
        cy = (self.root.winfo_screenheight() - 340) // 2
        win.geometry(f"420x340+{cx}+{cy}")

        tk.Label(win, text="🚨",
                 font=("Helvetica", 52),
                 bg=COLORS["danger"], fg="white").pack(pady=(28, 5))
        tk.Label(win, text="EMERGENCY ALERT",
                 font=("Helvetica", 20, "bold"),
                 bg=COLORS["danger"], fg="white").pack()
        tk.Label(win, text="Call your doctor or emergency services immediately!",
                 font=("Helvetica", 10),
                 bg=COLORS["danger"], fg="#FFD0D0",
                 wraplength=360).pack(pady=8)

        info = tk.Frame(win, bg="#C0392B", padx=20, pady=12)
        info.pack(fill="x", padx=28)

        tk.Label(info, text=f"👨‍⚕️  {doctor}",
                 font=("Helvetica", 13, "bold"),
                 bg="#C0392B", fg="white").pack(anchor="w")
        tk.Label(info, text=f"📞  {doc_ph}",
                 font=("Helvetica", 12),
                 bg="#C0392B", fg="white").pack(anchor="w", pady=(4, 0))
        tk.Label(info, text="🆘  Ambulance / Emergency: 112",
                 font=("Helvetica", 12, "bold"),
                 bg="#C0392B", fg="white").pack(anchor="w", pady=(4, 0))

        tk.Button(win, text="Close",
                  command=win.destroy,
                  bg="white", fg=COLORS["danger"],
                  font=("Helvetica", 11, "bold"),
                  relief="flat").pack(pady=16, ipadx=24, ipady=6)

    # ── LOGOUT ───────────────────────────────────────────────────────────────

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            # Clear all frames
            for frame in self.frames.values():
                frame.destroy()
            self.frames.clear()
            self.main_pane.destroy()
            # Re-launch login screen
            _show_login(self.root)

    # ── MEDICINE REMINDER THREAD ─────────────────────────────────────────────

    def _start_reminder_thread(self):
        """Background thread that checks medicine reminder times every minute."""
        def check_reminders():
            import json
            notified_today = set()  # Track what was notified to avoid repeats

            while True:
                try:
                    now = datetime.now()
                    current_time = now.strftime("%H:%M")
                    today_key_base = now.strftime("%Y-%m-%d")

                    meds = db.get_medicines(self.user["id"])
                    for med in meds:
                        try:
                            times = json.loads(med.get("reminder_times", "[]"))
                        except Exception:
                            continue

                        if current_time in times:
                            key = f"{today_key_base}_{med['id']}_{current_time}"
                            if key not in notified_today:
                                notified_today.add(key)
                                # Show notification on main thread
                                self.root.after(0, lambda m=med:
                                    self._show_med_reminder(m))

                    # Clean old keys (keep only today's)
                    notified_today = {k for k in notified_today
                                      if k.startswith(today_key_base)}

                except Exception:
                    pass   # Never crash the background thread

                time.sleep(60)  # Check every minute

        t = threading.Thread(target=check_reminders, daemon=True)
        t.start()

    def _show_med_reminder(self, med):
        """Show a medicine reminder popup."""
        win = tk.Toplevel(self.root)
        win.title("💊 Medicine Reminder")
        win.geometry("380x260")
        win.resizable(False, False)
        win.configure(bg=COLORS["warn"])
        win.attributes("-topmost", True)

        cx = (self.root.winfo_screenwidth()  - 380) // 2
        cy = (self.root.winfo_screenheight() - 260) // 2
        win.geometry(f"380x260+{cx}+{cy}")

        tk.Label(win, text="💊",
                 font=("Helvetica", 40),
                 bg=COLORS["warn"], fg="white").pack(pady=(24, 4))
        tk.Label(win, text="Medicine Reminder",
                 font=("Helvetica", 16, "bold"),
                 bg=COLORS["warn"], fg="white").pack()
        tk.Label(win, text=f"Time to take: {med['name']}",
                 font=("Helvetica", 13),
                 bg=COLORS["warn"], fg="white").pack(pady=4)
        tk.Label(win, text=f"Dosage: {med['dosage'] or 'As prescribed'}",
                 font=("Helvetica", 11),
                 bg=COLORS["warn"], fg="#FFF3C4").pack()

        tk.Button(win, text="✓  OK, I've taken it",
                  command=win.destroy,
                  bg="white", fg=COLORS["warn"],
                  font=("Helvetica", 11, "bold"),
                  relief="flat").pack(pady=16, ipadx=20, ipady=6)

        # Auto-close after 30 seconds
        win.after(30000, lambda: win.destroy()
                  if win.winfo_exists() else None)


# ════════════════════════════════════════════════════════════
#  STARTUP
# ════════════════════════════════════════════════════════════

def _show_login(root):
    """Display login window."""
    login_frame = tk.Frame(root)
    login_frame.pack(fill="both", expand=True)

    def on_login_success(user):
        login_frame.destroy()
        root.geometry("1200x720")
        root.resizable(True, True)
        DiabeteCareApp(root, user)

    LoginWindow(login_frame, on_login_success)


def main():
    """Application entry point."""
    print("=" * 60)
    print("  DiabeteCare — Patient Management System")
    print("  Python + Tkinter + SQLite + Matplotlib")
    print("=" * 60)

    # 1. Initialise database
    db.initialize_database()

    # 2. Insert sample data (only once)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()

    if user_count == 0:
        print("[INFO] First run — inserting sample data...")
        db.insert_sample_data()

    # 3. Create root window
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("900x620")
    root.resizable(False, False)

    # App icon (text-based fallback)
    try:
        root.iconbitmap("assets/icon.ico")
    except Exception:
        pass   # No icon file — that's fine

    # 4. Show login
    _show_login(root)

    # 5. Main loop
    print("[INFO] Application started. Login with: demo / demo123")
    root.mainloop()
    print("[INFO] Application closed.")


if __name__ == "__main__":
    main()
