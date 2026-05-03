"""
login.py - Login & Registration Window
Healthcare-themed UI with soft blue/green/white palette
"""

import tkinter as tk
from tkinter import ttk, messagebox
import database as db


# ── Color palette ────────────────────────────────────────────────────────────
COLORS = {
    "bg":       "#F0F7FF",      # soft sky background
    "panel":    "#FFFFFF",      # white card
    "primary":  "#1A6FB5",      # medical blue
    "accent":   "#27AE60",      # health green
    "text":     "#2C3E50",      # dark text
    "subtext":  "#7F8C8D",      # grey helper text
    "border":   "#D5E8F7",      # soft border
    "entry_bg": "#F8FCFF",      # entry background
    "danger":   "#E74C3C",      # alert red
    "warn":     "#F39C12",      # warning orange
}


def _style_entry(entry):
    """Apply common styling to Entry widgets."""
    entry.configure(
        bg=COLORS["entry_bg"],
        fg=COLORS["text"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["primary"],
        font=("Helvetica", 11),
        bd=0,
        insertbackground=COLORS["primary"],
    )


class LoginWindow:
    """Main login/register window that launches on startup."""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success   # callback(user_dict)
        self.root.title("DiabeteCare — Patient Management System")
        self.root.geometry("900x620")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])

        # Centre the window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 900) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"900x620+{x}+{y}")

        self._build_ui()

    # ── UI CONSTRUCTION ──────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the two-panel login layout."""
        # Left decorative panel
        left = tk.Frame(self.root, bg=COLORS["primary"], width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self._left_panel(left)

        # Right panel (form area)
        right = tk.Frame(self.root, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True)

        self._right_panel(right)

    def _left_panel(self, parent):
        """Decorative left panel with branding."""
        tk.Label(parent, text="🏥", font=("Helvetica", 48),
                 bg=COLORS["primary"], fg="white").pack(pady=(80, 10))

        tk.Label(parent, text="DiabeteCare",
                 font=("Helvetica", 26, "bold"),
                 bg=COLORS["primary"], fg="white").pack()

        tk.Label(parent, text="Patient Management System",
                 font=("Helvetica", 12),
                 bg=COLORS["primary"], fg="#A8D4FF").pack(pady=(4, 30))

        # Feature pills
        features = [
            "🩸  Blood Sugar Tracking",
            "💊  Medicine Reminders",
            "🥗  Diet & Meal Tracker",
            "💧  Water Intake Monitor",
            "🏃  Exercise Tracker",
            "📊  Health Reports & Charts",
            "⚖️  BMI Calculator",
            "🚨  Emergency Alerts",
        ]
        for feat in features:
            row = tk.Frame(parent, bg=COLORS["primary"])
            row.pack(fill="x", padx=30, pady=3)
            tk.Label(row, text=feat, font=("Helvetica", 10),
                     bg=COLORS["primary"], fg="#D0EAFF",
                     anchor="w").pack(fill="x")

        tk.Label(parent, text="© 2024 DiabeteCare v1.0",
                 font=("Helvetica", 9),
                 bg=COLORS["primary"], fg="#7EB8E8").pack(side="bottom", pady=20)

    def _right_panel(self, parent):
        """Right panel hosts login / register tabs."""
        # Notebook (tabs)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.TNotebook", background=COLORS["bg"],
                        borderwidth=0)
        style.configure("Custom.TNotebook.Tab",
                        background=COLORS["border"],
                        foreground=COLORS["text"],
                        padding=[20, 8],
                        font=("Helvetica", 11, "bold"))
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", COLORS["panel"])],
                  foreground=[("selected", COLORS["primary"])])

        nb = ttk.Notebook(parent, style="Custom.TNotebook")
        nb.pack(fill="both", expand=True, padx=30, pady=40)

        # Login tab
        login_frame = tk.Frame(nb, bg=COLORS["panel"])
        nb.add(login_frame, text="  Sign In  ")
        self._login_form(login_frame)

        # Register tab
        reg_frame = tk.Frame(nb, bg=COLORS["panel"])
        nb.add(reg_frame, text="  Register  ")
        self._register_form(reg_frame)

    # ── LOGIN FORM ───────────────────────────────────────────────────────────

    def _login_form(self, parent):
        """Username + password sign-in form."""
        tk.Label(parent, text="Welcome Back!",
                 font=("Helvetica", 20, "bold"),
                 bg=COLORS["panel"], fg=COLORS["primary"]).pack(pady=(40, 6))

        tk.Label(parent, text="Sign in to continue your health journey",
                 font=("Helvetica", 10),
                 bg=COLORS["panel"], fg=COLORS["subtext"]).pack(pady=(0, 30))

        # Fields
        self.login_user_var = tk.StringVar()
        self.login_pass_var = tk.StringVar()

        for label, var, show in [
            ("👤  Username", self.login_user_var, ""),
            ("🔒  Password", self.login_pass_var, "*"),
        ]:
            tk.Label(parent, text=label, font=("Helvetica", 10, "bold"),
                     bg=COLORS["panel"], fg=COLORS["text"],
                     anchor="w").pack(fill="x", padx=50)

            e = tk.Entry(parent, textvariable=var, show=show, width=30)
            _style_entry(e)
            e.pack(fill="x", padx=50, ipady=8, pady=(2, 14))

        # Sign In button
        btn = tk.Button(parent, text="Sign In  →",
                        command=self._do_login,
                        bg=COLORS["primary"], fg="white",
                        font=("Helvetica", 12, "bold"),
                        relief="flat", cursor="hand2",
                        activebackground="#15599A",
                        activeforeground="white")
        btn.pack(fill="x", padx=50, ipady=10, pady=(6, 0))

        # Demo hint
        tk.Label(parent, text="Demo: username=demo  password=demo123",
                 font=("Helvetica", 9),
                 bg=COLORS["panel"], fg=COLORS["subtext"]).pack(pady=(12, 0))

        # Bind Enter key
        self.root.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        """Validate credentials and trigger callback."""
        username = self.login_user_var.get().strip()
        password = self.login_pass_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Missing Fields",
                                   "Please enter both username and password.")
            return

        user = db.login_user(username, password)
        if user:
            self.on_login_success(user)
        else:
            messagebox.showerror("Login Failed",
                                 "Invalid username or password.\nPlease try again.")

    # ── REGISTER FORM ────────────────────────────────────────────────────────

    def _register_form(self, parent):
        """New patient registration form."""
        # Scrollable canvas for long form
        canvas = tk.Canvas(parent, bg=COLORS["panel"],
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLORS["panel"])
        window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(event):
            canvas.itemconfig(window, width=event.width)

        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))

        # Mouse wheel scroll
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            -1 * (e.delta // 120), "units"))

        self._build_register_fields(inner)

    def _build_register_fields(self, parent):
        """All fields for registration."""
        tk.Label(parent, text="Create Account",
                 font=("Helvetica", 18, "bold"),
                 bg=COLORS["panel"], fg=COLORS["primary"]).pack(pady=(30, 4))

        tk.Label(parent, text="Fill in your details to get started",
                 font=("Helvetica", 10),
                 bg=COLORS["panel"], fg=COLORS["subtext"]).pack(pady=(0, 20))

        # Variables
        self.reg_vars = {
            "username":    tk.StringVar(),
            "password":    tk.StringVar(),
            "confirm":     tk.StringVar(),
            "full_name":   tk.StringVar(),
            "age":         tk.StringVar(),
            "email":       tk.StringVar(),
            "phone":       tk.StringVar(),
            "doctor_name": tk.StringVar(),
            "doctor_phone":tk.StringVar(),
            "diagnosis":   tk.StringVar(),
        }

        # Field definitions: (label, key, show)
        fields = [
            ("👤  Username *",         "username",    ""),
            ("🔒  Password *",         "password",    "*"),
            ("🔒  Confirm Password *", "confirm",     "*"),
            ("📋  Full Name *",        "full_name",   ""),
            ("🎂  Age *",              "age",         ""),
            ("📧  Email",              "email",       ""),
            ("📱  Phone",              "phone",       ""),
            ("🩺  Doctor Name",        "doctor_name", ""),
            ("📞  Doctor Phone",       "doctor_phone",""),
            ("📅  Diagnosis Date",     "diagnosis",   ""),
        ]

        for label, key, show in fields:
            tk.Label(parent, text=label,
                     font=("Helvetica", 10, "bold"),
                     bg=COLORS["panel"], fg=COLORS["text"],
                     anchor="w").pack(fill="x", padx=40)
            e = tk.Entry(parent,
                         textvariable=self.reg_vars[key],
                         show=show)
            _style_entry(e)
            e.pack(fill="x", padx=40, ipady=7, pady=(2, 10))

        # Gender selector
        tk.Label(parent, text="⚧  Gender *",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"],
                 anchor="w").pack(fill="x", padx=40)

        self.gender_var = tk.StringVar(value="Male")
        gf = tk.Frame(parent, bg=COLORS["panel"])
        gf.pack(fill="x", padx=40, pady=(2, 10))
        for g in ["Male", "Female", "Other"]:
            tk.Radiobutton(gf, text=g, variable=self.gender_var,
                           value=g, bg=COLORS["panel"],
                           fg=COLORS["text"],
                           selectcolor=COLORS["panel"],
                           activebackground=COLORS["panel"],
                           font=("Helvetica", 10)).pack(side="left", padx=8)

        # Diabetes type
        tk.Label(parent, text="🩺  Diabetes Type *",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"],
                 anchor="w").pack(fill="x", padx=40)

        self.diab_type_var = tk.StringVar(value="Type 2")
        df = tk.Frame(parent, bg=COLORS["panel"])
        df.pack(fill="x", padx=40, pady=(2, 14))
        for dt in ["Type 1", "Type 2", "Gestational", "Pre-Diabetes"]:
            tk.Radiobutton(df, text=dt, variable=self.diab_type_var,
                           value=dt, bg=COLORS["panel"],
                           fg=COLORS["text"],
                           selectcolor=COLORS["panel"],
                           activebackground=COLORS["panel"],
                           font=("Helvetica", 10)).pack(side="left", padx=6)

        # Register button
        btn = tk.Button(parent, text="Create Account  →",
                        command=self._do_register,
                        bg=COLORS["accent"], fg="white",
                        font=("Helvetica", 12, "bold"),
                        relief="flat", cursor="hand2",
                        activebackground="#1E8449",
                        activeforeground="white")
        btn.pack(fill="x", padx=40, ipady=10, pady=(4, 30))

    def _do_register(self):
        """Validate and submit registration form."""
        v = self.reg_vars

        # Required field validation
        required = ["username", "password", "confirm", "full_name", "age"]
        for key in required:
            if not v[key].get().strip():
                messagebox.showwarning("Missing Fields",
                                       "Please fill all required (*) fields.")
                return

        if v["password"].get() != v["confirm"].get():
            messagebox.showerror("Password Mismatch",
                                 "Passwords do not match!")
            return

        try:
            age = int(v["age"].get().strip())
            if not (1 <= age <= 120):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Age", "Please enter a valid age.")
            return

        result = db.register_user(
            username=v["username"].get().strip(),
            password=v["password"].get().strip(),
            full_name=v["full_name"].get().strip(),
            age=age,
            gender=self.gender_var.get(),
            email=v["email"].get().strip(),
            phone=v["phone"].get().strip(),
            doctor_name=v["doctor_name"].get().strip(),
            doctor_phone=v["doctor_phone"].get().strip(),
            diabetes_type=self.diab_type_var.get(),
            diagnosis_date=v["diagnosis"].get().strip(),
        )

        if result is True:
            messagebox.showinfo("Success! 🎉",
                                "Account created successfully!\n"
                                "Please sign in with your credentials.")
            # Clear register fields
            for var in self.reg_vars.values():
                var.set("")
        else:
            messagebox.showerror("Registration Failed", result)
