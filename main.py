from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import os
import secrets

load_dotenv()

app = Flask(
    __name__,
    template_folder='ui/templates',
    static_folder='ui/static'
)
app.secret_key = os.getenv("SECRET_KEY")

def generate_csrf():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/login")
def login():
    return render_template('login.html', csrf_token=generate_csrf())

@app.route("/login", methods=["POST"])
def login_post():
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    password = data.get('password')

    # Demo credentials
    if doctor_id == "DR-DEMO-001" and password == "demo123":
        session['doctor_id'] = doctor_id
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/input")
def input_form():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return render_template('input.html', csrf_token=generate_csrf())

@app.route("/reset")
def reset():
    return render_template('login.html',
        csrf_token=generate_csrf()
    )

if __name__ == "__main__":
    app.run(debug=True)