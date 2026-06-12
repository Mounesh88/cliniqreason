import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_NAME = os.getenv("DATABASE_NAME", "cliniqreason.db")

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_code TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_code TEXT NOT NULL,
            name TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            patient_code TEXT,
            doctor_code TEXT,
            symptoms TEXT,
            vitals TEXT,
            medications TEXT,
            history TEXT,
            risk_level TEXT,
            triage TEXT,
            confidence REAL,
            diagnosis TEXT,
            reasoning_chain TEXT,
            recommendations TEXT,
            sources TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            action TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Database tables created successfully! ✅")

if __name__ == "__main__":
    create_tables()