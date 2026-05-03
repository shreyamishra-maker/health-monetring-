"""
profile.py - Patient Profile Management
View and edit personal + medical information
"""

import tkinter as tk
from tkinter import messagebox, ttk
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


class ProfileFrame(tk.Frame):
    """Patient profile view and editor."""

    def __init__(self, parent, user, app_ref):
        super().__init__(parent, bg=COLORS["bg"])
        self.user    = user
        self.app     = app_ref
        self._build()

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self.user = db.get_user(self.user["id"])
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg="#1ABC9C", height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="👤  Patient Profile",
                 font=("Helvetica", 14, "bold"),
                 bg="#1ABC9C", fg="white").pack(
                     side="left", padx=20, pady=12)

        # Scrollable content
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        vsb    = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        content = tk.Frame(canvas, bg=COLORS["bg"])
        cw = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cw, width=e.width))
        content.bind("<Configure>",
                     lambda e: canvas.configure(
                         scrollregion=canvas.bbox("all")))

        self._profile_header(content)
        self._edit_form(content)

    def _profile_header(self, parent):
        """Avatar card at the top."""
        card = tk.Frame(parent, bg=COLORS["panel"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", padx=20, pady=16)

        # Avatar section
        av_frame = tk.Frame(card, bg=COLORS["primary"], width=90, height=90)
        av_frame.pack(side="left", padx=16, pady=16)
        av_frame.pack_propagate(False)
        tk.Label(av_frame, text="👤",
                 font=("Helvetica", 36),
                 bg=COLORS["primary"], fg="white").pack(
                     expand=True)

        # Info
        info = tk.Frame(card, bg=COLORS["panel"])
        info.pack(side="left", padx=12, pady=16)

        name = self.user.get("full_name", "Patient")
        tk.Label(info, text=name,
                 font=("Helvetica", 20, "bold"),
                 bg=COLORS["panel"], fg=COLORS["primary"]).pack(anchor="w")

        uname = self.user.get("username", "")
        tk.Label(info, text=f"@{uname}",
                 font=("Helvetica", 11),
                 bg=COLORS["panel"], fg=COLORS["subtext"]).pack(anchor="w")

        diab_type = self.user.get("diabetes_type", "—")
        tk.Label(info, text=f"🩺  {diab_type}",
                 font=("Helvetica", 11, "bold"),
                 bg=COLORS["panel"], fg=COLORS["accent"]).pack(
                     anchor="w", pady=(6, 0))

        diagnosis = self.user.get("diagnosis_date", "")
        if diagnosis:
            tk.Label(info, text=f"📅  Diagnosed: {diagnosis}",
                     font=("Helvetica", 10),
                     bg=COLORS["panel"], fg=COLORS["subtext"]).pack(anchor="w")

        # Doctor info
        doc = tk.Frame(card, bg="#F0F7FF", padx=14, pady=10)
        doc.pack(side="right", padx=16, pady=16)

        tk.Label(doc, text="👨‍⚕️  Primary Physician",
                 font=("Helvetica", 9, "bold"),
                 bg="#F0F7FF", fg=COLORS["subtext"]).pack(anchor="w")
        tk.Label(doc, text=self.user.get("doctor_name", "Not set"),
                 font=("Helvetica", 11, "bold"),
                 bg="#F0F7FF", fg=COLORS["primary"]).pack(anchor="w")
        tk.Label(doc, text=self.user.get("doctor_phone", "—"),
                 font=("Helvetica", 10),
                 bg="#F0F7FF", fg=COLORS["text"]).pack(anchor="w")

    def _edit_form(self, parent):
        """Editable profile form."""
        form_card = tk.Frame(parent, bg=COLORS["panel"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
        form_card.pack(fill="x", padx=20, pady=(0, 20))

        hdr = tk.Frame(form_card, bg=COLORS["primary"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="✏️  Edit Profile Information",
                 font=("Helvetica", 12, "bold"),
                 bg=COLORS["primary"], fg="white").pack(
                     side="left", padx=16, pady=10)

        # Two-column form
        cols_frame = tk.Frame(form_card, bg=COLORS["panel"])
        cols_frame.pack(fill="x", padx=20, pady=16)

        col1 = tk.Frame(cols_frame, bg=COLORS["panel"])
        col2 = tk.Frame(cols_frame, bg=COLORS["panel"])
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Initialise vars with current values
        self.pv = {
            "full_name":   tk.StringVar(value=self.user.get("full_name", "")),
            "age":         tk.StringVar(value=str(self.user.get("age", ""))),
            "email":       tk.StringVar(value=self.user.get("email", "")),
            "phone":       tk.StringVar(value=self.user.get("phone", "")),
            "doctor_name": tk.StringVar(value=self.user.get("doctor_name", "")),
            "doctor_phone":tk.StringVar(value=self.user.get("doctor_phone", "")),
            "diagnosis":   tk.StringVar(value=self.user.get("diagnosis_date", "")),
        }

        self.gender_var   = tk.StringVar(value=self.user.get("gender", "Male"))
        self.diab_type_var = tk.StringVar(
            value=self.user.get("diabetes_type", "Type 2"))

        # Left column fields
        left_fields = [
            ("📋  Full Name",   "full_name"),
            ("🎂  Age",         "age"),
            ("📧  Email",       "email"),
            ("📱  Phone",       "phone"),
        ]
        for lbl, key in left_fields:
            tk.Label(col1, text=lbl,
                     font=("Helvetica", 10, "bold"),
                     bg=COLORS["panel"], fg=COLORS["text"],
                     anchor="w").pack(fill="x", pady=(8, 2))
            _entry(col1, self.pv[key]).pack(fill="x", ipady=7)

        # Right column fields
        right_fields = [
            ("🩺  Doctor Name",  "doctor_name"),
            ("📞  Doctor Phone", "doctor_phone"),
            ("📅  Diagnosis Date", "diagnosis"),
        ]
        for lbl, key in right_fields:
            tk.Label(col2, text=lbl,
                     font=("Helvetica", 10, "bold"),
                     bg=COLORS["panel"], fg=COLORS["text"],
                     anchor="w").pack(fill="x", pady=(8, 2))
            _entry(col2, self.pv[key]).pack(fill="x", ipady=7)

        # Gender
        tk.Label(col2, text="⚧  Gender",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"],
                 anchor="w").pack(fill="x", pady=(8, 2))
        gf = tk.Frame(col2, bg=COLORS["panel"])
        gf.pack(fill="x")
        for g in ["Male", "Female", "Other"]:
            tk.Radiobutton(gf, text=g, variable=self.gender_var,
                           value=g, bg=COLORS["panel"],
                           fg=COLORS["text"],
                           selectcolor=COLORS["panel"],
                           font=("Helvetica", 10)).pack(
                               side="left", padx=4)

        # Diabetes type
        tk.Label(col1, text="🩺  Diabetes Type",
                 font=("Helvetica", 10, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"],
                 anchor="w").pack(fill="x", pady=(8, 2))
        df = tk.Frame(col1, bg=COLORS["panel"])
        df.pack(fill="x")
        for dt in ["Type 1", "Type 2", "Gestational", "Pre-Diabetes"]:
            tk.Radiobutton(df, text=dt,
                           variable=self.diab_type_var, value=dt,
                           bg=COLORS["panel"], fg=COLORS["text"],
                           selectcolor=COLORS["panel"],
                           font=("Helvetica", 9)).pack(
                               side="left", padx=3)

        # Save button
        tk.Button(form_card, text="💾  Save Profile Changes",
                  command=self._save_profile,
                  bg=COLORS["accent"], fg="white",
                  font=("Helvetica", 12, "bold"),
                  relief="flat", cursor="hand2").pack(
                      fill="x", padx=20, ipady=12, pady=16)

    def _save_profile(self):
        try:
            age = int(self.pv["age"].get().strip())
            if not (1 <= age <= 120):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Please enter a valid age.")
            return

        db.update_user_profile(
            user_id      = self.user["id"],
            full_name    = self.pv["full_name"].get().strip(),
            age          = age,
            gender       = self.gender_var.get(),
            email        = self.pv["email"].get().strip(),
            phone        = self.pv["phone"].get().strip(),
            doctor_name  = self.pv["doctor_name"].get().strip(),
            doctor_phone = self.pv["doctor_phone"].get().strip(),
            diabetes_type = self.diab_type_var.get(),
            diagnosis_date = self.pv["diagnosis"].get().strip(),
        )

        # Update local user dict
        self.user = db.get_user(self.user["id"])
        messagebox.showinfo("✅ Saved",
                            "Profile updated successfully!")
        self.refresh()
