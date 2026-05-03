"""
database.py - SQLite Database Manager for Diabetes Patient Management App
Handles all database operations: create, read, update, delete
"""

import sqlite3
import hashlib
import os
from datetime import datetime, date

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "diabetes_app.db")


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn


def hash_password(password):
    """Hash password using SHA-256 for security."""
    return hashlib.sha256(password.encode()).hexdigest()


def initialize_database():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users / Patient Profiles ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            full_name   TEXT,
            age         INTEGER,
            gender      TEXT,
            email       TEXT,
            phone       TEXT,
            doctor_name TEXT,
            doctor_phone TEXT,
            diabetes_type TEXT DEFAULT 'Type 2',
            diagnosis_date TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Blood Sugar Readings ────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blood_sugar (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            reading     REAL NOT NULL,
            reading_type TEXT DEFAULT 'Random',  -- Fasting / Post-Meal / Random
            notes       TEXT,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Medicine Reminders ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT NOT NULL,
            dosage      TEXT,
            frequency   TEXT,
            reminder_times TEXT,   -- JSON list of times e.g. '["08:00","20:00"]'
            is_active   INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Meal / Diet Log ─────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            meal_type   TEXT,      -- Breakfast / Lunch / Dinner / Snack
            food_items  TEXT,
            calories    INTEGER,
            carbs       REAL,
            notes       TEXT,
            logged_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Water Intake ────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_intake (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount_ml   INTEGER NOT NULL,
            logged_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Exercise / Walking Log ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            activity    TEXT,
            duration_min INTEGER,
            distance_km REAL,
            calories_burned INTEGER,
            notes       TEXT,
            logged_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── BMI History ─────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bmi_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            weight_kg   REAL NOT NULL,
            height_cm   REAL NOT NULL,
            bmi         REAL NOT NULL,
            category    TEXT,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


# ════════════════════════════════════════════════════════════
#  USER FUNCTIONS
# ════════════════════════════════════════════════════════════

def register_user(username, password, full_name, age, gender, email="", phone="",
                  doctor_name="", doctor_phone="", diabetes_type="Type 2", diagnosis_date=""):
    """Register a new user. Returns True on success, error string on failure."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password, full_name, age, gender,
                               email, phone, doctor_name, doctor_phone,
                               diabetes_type, diagnosis_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, hash_password(password), full_name, age, gender,
              email, phone, doctor_name, doctor_phone, diabetes_type, diagnosis_date))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return "Username already exists. Please choose another."
    finally:
        conn.close()


def login_user(username, password):
    """Validate login credentials. Returns user row dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_user(user_id):
    """Fetch full profile of a user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_profile(user_id, full_name, age, gender, email, phone,
                        doctor_name, doctor_phone, diabetes_type, diagnosis_date):
    """Update user profile information."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET full_name=?, age=?, gender=?, email=?, phone=?,
        doctor_name=?, doctor_phone=?, diabetes_type=?, diagnosis_date=?
        WHERE id=?
    """, (full_name, age, gender, email, phone, doctor_name, doctor_phone,
          diabetes_type, diagnosis_date, user_id))
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════
#  BLOOD SUGAR FUNCTIONS
# ════════════════════════════════════════════════════════════

def add_blood_sugar(user_id, reading, reading_type="Random", notes=""):
    """Add a new blood sugar reading."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO blood_sugar (user_id, reading, reading_type, notes)
        VALUES (?, ?, ?, ?)
    """, (user_id, reading, reading_type, notes))
    conn.commit()
    conn.close()


def get_blood_sugar_records(user_id, limit=50):
    """Get recent blood sugar records for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM blood_sugar WHERE user_id=?
        ORDER BY recorded_at DESC LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_blood_sugar_last7days(user_id):
    """Get blood sugar readings from the last 7 days."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reading, reading_type, recorded_at FROM blood_sugar
        WHERE user_id=? AND recorded_at >= datetime('now', '-7 days')
        ORDER BY recorded_at ASC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_blood_sugar_last30days(user_id):
    """Get blood sugar readings from the last 30 days."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reading, reading_type, recorded_at FROM blood_sugar
        WHERE user_id=? AND recorded_at >= datetime('now', '-30 days')
        ORDER BY recorded_at ASC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_latest_sugar_reading(user_id):
    """Get the most recent blood sugar reading."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reading, reading_type, recorded_at FROM blood_sugar
        WHERE user_id=? ORDER BY recorded_at DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ════════════════════════════════════════════════════════════
#  MEDICINE FUNCTIONS
# ════════════════════════════════════════════════════════════

def add_medicine(user_id, name, dosage, frequency, reminder_times):
    """Add a new medicine reminder."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medicines (user_id, name, dosage, frequency, reminder_times)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, dosage, frequency, reminder_times))
    conn.commit()
    conn.close()


def get_medicines(user_id):
    """Get all active medicines for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM medicines WHERE user_id=? AND is_active=1
        ORDER BY created_at DESC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def delete_medicine(medicine_id):
    """Soft-delete a medicine by setting is_active=0."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE medicines SET is_active=0 WHERE id=?", (medicine_id,))
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════
#  MEAL FUNCTIONS
# ════════════════════════════════════════════════════════════

def add_meal(user_id, meal_type, food_items, calories, carbs, notes=""):
    """Log a meal entry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meals (user_id, meal_type, food_items, calories, carbs, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, meal_type, food_items, calories, carbs, notes))
    conn.commit()
    conn.close()


def get_meals_today(user_id):
    """Get all meals logged today."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM meals WHERE user_id=?
        AND date(logged_at) = date('now')
        ORDER BY logged_at ASC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_meals_recent(user_id, limit=20):
    """Get recent meals."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM meals WHERE user_id=?
        ORDER BY logged_at DESC LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ════════════════════════════════════════════════════════════
#  WATER INTAKE FUNCTIONS
# ════════════════════════════════════════════════════════════

def add_water(user_id, amount_ml):
    """Log water intake."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO water_intake (user_id, amount_ml) VALUES (?, ?)",
        (user_id, amount_ml)
    )
    conn.commit()
    conn.close()


def get_water_today(user_id):
    """Get total water intake for today in ml."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(amount_ml), 0) as total
        FROM water_intake WHERE user_id=?
        AND date(logged_at) = date('now')
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["total"] if row else 0


def get_water_week(user_id):
    """Get daily water totals for last 7 days."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date(logged_at) as day, SUM(amount_ml) as total
        FROM water_intake WHERE user_id=?
        AND logged_at >= datetime('now', '-7 days')
        GROUP BY date(logged_at) ORDER BY day ASC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ════════════════════════════════════════════════════════════
#  EXERCISE FUNCTIONS
# ════════════════════════════════════════════════════════════

def add_exercise(user_id, activity, duration_min, distance_km=0, calories_burned=0, notes=""):
    """Log an exercise session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO exercise (user_id, activity, duration_min, distance_km, calories_burned, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, activity, duration_min, distance_km, calories_burned, notes))
    conn.commit()
    conn.close()


def get_exercise_today(user_id):
    """Get exercise logged today."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM exercise WHERE user_id=?
        AND date(logged_at) = date('now')
        ORDER BY logged_at ASC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_exercise_recent(user_id, limit=20):
    """Get recent exercise sessions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM exercise WHERE user_id=?
        ORDER BY logged_at DESC LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ════════════════════════════════════════════════════════════
#  BMI FUNCTIONS
# ════════════════════════════════════════════════════════════

def add_bmi_record(user_id, weight_kg, height_cm, bmi, category):
    """Save a BMI calculation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bmi_records (user_id, weight_kg, height_cm, bmi, category)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, weight_kg, height_cm, bmi, category))
    conn.commit()
    conn.close()


def get_bmi_history(user_id, limit=10):
    """Get BMI history for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM bmi_records WHERE user_id=?
        ORDER BY recorded_at DESC LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_latest_bmi(user_id):
    """Get the most recent BMI record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM bmi_records WHERE user_id=?
        ORDER BY recorded_at DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ════════════════════════════════════════════════════════════
#  SAMPLE DATA
# ════════════════════════════════════════════════════════════

def insert_sample_data():
    """Insert sample data for demo/testing purposes."""
    import json
    from datetime import datetime, timedelta
    import random

    # Register a sample user
    result = register_user(
        username="demo",
        password="demo123",
        full_name="Rajesh Kumar",
        age=45,
        gender="Male",
        email="rajesh@email.com",
        phone="9876543210",
        doctor_name="Dr. Priya Sharma",
        doctor_phone="9811112222",
        diabetes_type="Type 2",
        diagnosis_date="2020-03-15"
    )

    if result is True:
        # Get the created user
        user = login_user("demo", "demo123")
        uid = user["id"]

        # Sample blood sugar readings over past 30 days
        conn = get_connection()
        cursor = conn.cursor()
        base_date = datetime.now()
        sugar_types = ["Fasting", "Post-Meal", "Random"]

        for i in range(30):
            day = base_date - timedelta(days=i)
            for _ in range(random.randint(1, 3)):
                reading = random.uniform(90, 280)
                r_type = random.choice(sugar_types)
                ts = day.strftime("%Y-%m-%d") + f" {random.randint(6,22):02d}:00:00"
                cursor.execute("""
                    INSERT INTO blood_sugar (user_id, reading, reading_type, recorded_at)
                    VALUES (?, ?, ?, ?)
                """, (uid, round(reading, 1), r_type, ts))

        # Sample water intake
        for i in range(7):
            day = base_date - timedelta(days=i)
            for _ in range(random.randint(4, 8)):
                ml = random.choice([200, 250, 300])
                ts = day.strftime("%Y-%m-%d") + f" {random.randint(7,21):02d}:00:00"
                cursor.execute(
                    "INSERT INTO water_intake (user_id, amount_ml, logged_at) VALUES (?, ?, ?)",
                    (uid, ml, ts)
                )

        # Sample exercises
        activities = ["Walking", "Yoga", "Cycling", "Swimming"]
        for i in range(10):
            day = base_date - timedelta(days=i * 2)
            act = random.choice(activities)
            cursor.execute("""
                INSERT INTO exercise (user_id, activity, duration_min, distance_km,
                                      calories_burned, logged_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (uid, act, random.randint(20, 60),
                  round(random.uniform(1, 5), 1),
                  random.randint(100, 300),
                  day.strftime("%Y-%m-%d %H:%M:%S")))

        # Sample medicines
        meds = [
            ("Metformin", "500mg", "Twice daily", '["08:00", "20:00"]'),
            ("Glipizide", "5mg", "Once daily", '["07:30"]'),
            ("Lisinopril", "10mg", "Once daily", '["09:00"]'),
        ]
        for name, dosage, freq, times in meds:
            cursor.execute("""
                INSERT INTO medicines (user_id, name, dosage, frequency, reminder_times)
                VALUES (?, ?, ?, ?, ?)
            """, (uid, name, dosage, freq, times))

        # Sample meals
        meal_data = [
            ("Breakfast", "Oats with milk, Banana", 320, 55),
            ("Lunch", "Brown rice, Dal, Sabzi, Salad", 480, 70),
            ("Dinner", "Roti, Paneer curry, Salad", 410, 60),
            ("Snack", "Apple, Nuts", 180, 25),
        ]
        for i in range(5):
            day = base_date - timedelta(days=i)
            for mtype, food, cal, carb in meal_data:
                ts = day.strftime("%Y-%m-%d") + " 12:00:00"
                cursor.execute("""
                    INSERT INTO meals (user_id, meal_type, food_items, calories, carbs, logged_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (uid, mtype, food, cal, carb, ts))

        # Sample BMI records
        for i in range(5):
            day = base_date - timedelta(days=i * 30)
            w = round(random.uniform(78, 85), 1)
            h = 172
            bmi = round(w / ((h / 100) ** 2), 1)
            cat = "Overweight" if bmi >= 25 else "Normal"
            cursor.execute("""
                INSERT INTO bmi_records (user_id, weight_kg, height_cm, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (uid, w, h, bmi, cat, day.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        print("[DB] Sample data inserted. Login: demo / demo123")
