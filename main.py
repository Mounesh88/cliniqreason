from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from flask_session import Session
import os
import secrets
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Initialize database tables on startup
from database.db import create_tables
create_tables()

app = Flask(
    __name__,
    template_folder='ui/templates',
    static_folder='ui/static'
)
app.secret_key = os.getenv("SECRET_KEY", "cliniqreason-secret-key-2026")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

try:
    os.makedirs('flask_session', exist_ok=True)
    Session(app)
    print('Flask-Session initialized OK', flush=True)
except Exception as e:
    print(f'Flask-Session failed: {e}', flush=True)
# ─────────────────────────────────────────
# SCREEN 1 — LOGIN
# ─────────────────────────────────────────
@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/login", methods=["POST"])
def login_post():
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    password = data.get('password')

    # Demo credentials
    DEMO_DOCTORS = {
        "DR-DEMO-001": "demo123"
    }

    # Check demo credentials
    if doctor_id in DEMO_DOCTORS and DEMO_DOCTORS[doctor_id] == password:
        session.permanent = True
        session['doctor_id'] = doctor_id
        return jsonify({"success": True})

    # Check database for real doctors
    try:
        from database.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT doctor_id FROM doctors WHERE doctor_id=? AND password=?',
            (doctor_id, password)
        )
        doctor = cursor.fetchone()
        conn.close()
        if doctor:
            session['doctor_id'] = doctor_id
            return jsonify({"success": True})
    except Exception as e:
        print('DB login error:', e)

    return jsonify({"success": False})

# ─────────────────────────────────────────
# SCREEN 2 — INPUT FORM
# ─────────────────────────────────────────
@app.route("/input")
def input_form():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return render_template(
        'input.html',
        doctor_id=session['doctor_id']
    )

# ─────────────────────────────────────────
# PDF / WORD FILE UPLOAD
# ─────────────────────────────────────────
@app.route("/upload_patient_file", methods=["POST"])
def upload_patient_file():
    if 'doctor_id' not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files['file']
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename"})

    filename = file.filename.lower()
    extracted = {}

    try:
        if filename.endswith('.pdf'):
            try:
                import pdfplumber
                with pdfplumber.open(file) as pdf:
                    text = ''
                    for page in pdf.pages:
                        text += page.extract_text() or ''
                extracted = parse_patient_text(text)
            except ImportError:
                return jsonify({"success": False, "error": "pdfplumber not installed. Run: pip install pdfplumber"})

        elif filename.endswith('.docx'):
            try:
                import docx
                import io
                doc = docx.Document(io.BytesIO(file.read()))
                text = '\n'.join([para.text for para in doc.paragraphs])
                extracted = parse_patient_text(text)
            except ImportError:
                return jsonify({"success": False, "error": "python-docx not installed. Run: pip install python-docx"})

        elif filename.endswith('.txt'):
            text = file.read().decode('utf-8', errors='ignore')
            extracted = parse_patient_text(text)

        else:
            return jsonify({"success": False, "error": "Unsupported file type"})

        return jsonify({"success": True, "extracted": extracted})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def parse_patient_text(text):
    """Extract patient fields from document text"""
    import re
    extracted = {}

    patterns = {
        'patient_code': r'(?:patient\s*(?:code|id|number)\s*[:=]\s*)([A-Z0-9\-]+)',
        'age': r'(?:age\s*[:=]\s*)(\d+)',
        'gender': r'(?:gender|sex)\s*[:=]\s*(male|female|other)',
        'chief_complaint': r'(?:chief\s*complaint|presenting\s*complaint|main\s*symptom|complaint)\s*[:=]\s*(.+)',
        'onset': r'(?:onset|started|began)\s*[:=]\s*(.+)',
        'duration': r'(?:duration|lasting)\s*[:=]\s*(.+)',
        'character': r'(?:character|nature|quality|description)\s*[:=]\s*(.+)',
        'radiation': r'(?:radiation|radiates|radiating)\s*[:=]\s*(.+)',
        'associated_symptoms': r'(?:associated\s*symptoms?|other\s*symptoms?)\s*[:=]\s*(.+)',
        'bp': r'(?:blood\s*pressure|bp)\s*[:=]\s*([\d/]+\s*(?:mmhg)?)',
        'hr': r'(?:heart\s*rate|hr|pulse)\s*[:=]\s*([\d]+\s*(?:bpm)?)',
        'o2': r'(?:o2\s*sat(?:uration)?|oxygen|spo2|o2)\s*[:=]\s*([\d]+\s*%?)',
        'rr': r'(?:respiratory\s*rate|rr|resp\s*rate)\s*[:=]\s*([\d]+\s*(?:breaths?)?(?:/min)?)',
        'temp': r'(?:temperature|temp)\s*[:=]\s*([\d.]+\s*°?[CF]?)',
        'history': r'(?:past\s*(?:medical\s*)?(?:history|conditions?)|medical\s*history|pmh|history)\s*[:=]\s*(.+)',
        'surgeries': r'(?:(?:previous|prior|past)\s*surger(?:y|ies)|surgical\s*history)\s*[:=]\s*(.+)',
        'family_history': r'(?:family\s*history)\s*[:=]\s*(.+)',
        'smoking': r'(?:smoking\s*(?:status)?|smoker)\s*[:=]\s*(.+)',
        'medications': r'(?:medications?|drugs?|current\s*meds?|medicines?)\s*[:=]\s*(.+)',
        'allergies': r'(?:allergies|allergy|allergic)\s*[:=]\s*(.+)',
        'ecg': r'(?:ecg|ekg|electrocardiogram)\s*(?:findings?)?\s*[:=]\s*(.+)',
        'troponin': r'(?:troponin)\s*[:=]\s*(.+)',
        'risk_factors': r'(?:risk\s*factors?)\s*[:=]\s*(.+)',
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if field == 'age':
                try:
                    extracted[field] = int(re.search(r'\d+', value).group())
                except:
                    pass
            elif field == 'gender':
                v = value.lower()
                if 'female' in v:
                    extracted[field] = 'Female'
                elif 'male' in v:
                    extracted[field] = 'Male'
                else:
                    extracted[field] = 'Other'
            elif field == 'smoking':
                v = value.lower()
                if 'ex' in v or 'former' in v:
                    extracted[field] = 'Ex-smoker'
                elif 'current' in v or 'yes' in v:
                    extracted[field] = 'Current smoker'
                else:
                    extracted[field] = 'Never'
            else:
                extracted[field] = value[:300]

    return extracted

# ─────────────────────────────────────────
# SCREEN 3 — LOADING
# ─────────────────────────────────────────
@app.route("/loading")
def loading():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return render_template('loading.html')

# ─────────────────────────────────────────
# ANALYZE — RUN ORCHESTRATOR
# ─────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    if 'doctor_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    try:
        from agents.orchestrator import run_clinical_assessment
        data = request.get_json()
        data['doctor_code'] = session['doctor_id']
        result = run_clinical_assessment(data)
        session['assessment_result'] = result
        session['patient_data'] = data
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────
# SCREEN 4 — OUTPUT DASHBOARD
# ─────────────────────────────────────────
@app.route("/output")
def output():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    result = {}
    patient = {}
    try:
        from database.db import get_connection
        import json
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, patient_code, doctor_code,
                   symptoms, vitals, medications, history,
                   reasoning_chain, final_output, created_at
            FROM sessions
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        if row:
            result = {
                'session_id': row[0],
                'final_report': row[8],
                'reasoning_chain': json.loads(row[7]) if row[7] else {},
                'total_time': None
            }
            vitals_str = row[4] or ''
            import re
            age_match = re.search(r'Age:(\d+)', vitals_str)
            gender_match = re.search(r'Gender:(\w+)', vitals_str)
            bp_match = re.search(r'BP:([\d/]+\s*\w+)', vitals_str)
            hr_match = re.search(r'HR:([\d]+\s*\w+)', vitals_str)
            patient = {
                'patient_code': row[1],
                'doctor_code': row[2],
                'chief_complaint': row[3],
                'vitals': vitals_str,
                'medications': row[5],
                'history': row[6],
                'created_at': row[9],
                'age': age_match.group(1) if age_match else '',
                'gender': gender_match.group(1) if gender_match else '',
                'bp': bp_match.group(1) if bp_match else '',
                'hr': hr_match.group(1) if hr_match else ''
            }
    except Exception as e:
        print('Output error:', e)
    return render_template(
        'output.html',
        doctor_id=session['doctor_id'],
        result=result,
        patient=patient
    )

# ─────────────────────────────────────────
# SCREEN 5 — AUDIT LOG
# ─────────────────────────────────────────
@app.route("/audit")
def audit():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    try:
        from database.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, patient_code, doctor_code,
                   symptoms, created_at, final_output
            FROM sessions
            ORDER BY created_at DESC
            LIMIT 50
        ''')
        rows = cursor.fetchall()
        conn.close()
        sessions_data = [list(r) for r in rows]
        return render_template(
            'audit.html',
            doctor_id=session['doctor_id'],
            sessions=sessions_data
        )
    except Exception as e:
        return render_template(
            'audit.html',
            doctor_id=session['doctor_id'],
            sessions=[]
        )

# ─────────────────────────────────────────
# PATIENTS PAGE
# ─────────────────────────────────────────
@app.route("/patients")
def patients():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    try:
        from database.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        # Get unique patients with session count and last seen
        cursor.execute('''
            SELECT patient_code,
                   COUNT(*) as session_count,
                   MAX(created_at) as last_seen,
                   final_output
            FROM sessions
            GROUP BY patient_code
            ORDER BY last_seen DESC
        ''')
        patients_data = [list(r) for r in cursor.fetchall()]

        # Get all sessions for history modal
        cursor.execute('''
            SELECT session_id, patient_code, doctor_code,
                   symptoms, created_at, final_output
            FROM sessions
            ORDER BY created_at DESC
        ''')
        all_sessions = [list(r) for r in cursor.fetchall()]
        conn.close()

        return render_template(
            'patients.html',
            doctor_id=session['doctor_id'],
            patients=patients_data,
            sessions=all_sessions
        )
    except Exception as e:
        return render_template(
            'patients.html',
            doctor_id=session['doctor_id'],
            patients=[],
            sessions=[]
        )

# ─────────────────────────────────────────
# REPORTS PAGE
# ─────────────────────────────────────────
@app.route("/reports")
def reports():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    try:
        from database.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, patient_code, doctor_code,
                   created_at, final_output
            FROM sessions
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        sessions_data = [list(r) for r in rows]
        return render_template(
            'reports.html',
            doctor_id=session['doctor_id'],
            sessions=sessions_data
        )
    except Exception as e:
        return render_template(
            'reports.html',
            doctor_id=session['doctor_id'],
            sessions=[]
        )

# ─────────────────────────────────────────
# PROTOCOLS PAGE
# ─────────────────────────────────────────
@app.route("/protocols")
def protocols():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return render_template(
        'protocols.html',
        doctor_id=session['doctor_id']
    )

# ─────────────────────────────────────────
# GUIDELINES PAGE
# ─────────────────────────────────────────
@app.route("/guidelines")
def guidelines():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return render_template(
        'guidelines.html',
        doctor_id=session['doctor_id']
    )

# ─────────────────────────────────────────
# RESET PASSWORD
# ─────────────────────────────────────────
@app.route("/reset_password", methods=["POST"])
def reset_password():
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    email = data.get('email')
    try:
        from database.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id TEXT,
                email TEXT,
                requested_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        cursor.execute('''
            INSERT INTO password_resets (doctor_id, email)
            VALUES (?, ?)
        ''', (doctor_id, email))
        conn.commit()
        conn.close()
    except Exception as e:
        print('Reset password error:', e)
    return jsonify({"success": True})

# ─────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)