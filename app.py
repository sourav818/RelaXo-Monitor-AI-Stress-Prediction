from flask import Flask, render_template, send_file
from flask import request, redirect, session
from flask import make_response
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

import pandas as pd
import os
import pyrebase

app = Flask(__name__)

app.secret_key = "relaxo_monitor_secret_2026"

# PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data.csv")

# FIREBASE AUTH
firebaseConfig = {

    "apiKey": "apikey",

    "authDomain": "relaxo-monitor.firebaseapp.com",

    "databaseURL": "",

    "projectId": "relaxo-monitor",

    "storageBucket": "relaxo-monitor.firebasestorage.app",

    "messagingSenderId": "",

    "appId": ""

}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()

# REQUIRED COLUMNS
COLUMNS = ['Time','BPM','Temp','Humidity',
           'Emotion','Movement','Voice',
           'Stress','Suggestion']


# ---------------- HOME ----------------
@app.route('/')
def home():

    if 'user' not in session:
        return redirect('/login')

    try:
        # If CSV not exists → create fresh
        if not os.path.exists(CSV_PATH):
            pd.DataFrame(columns=COLUMNS).to_csv(CSV_PATH, index=False)

        df = pd.read_csv(CSV_PATH)

        # If empty → return default
        if df.empty:
            return render_template("index.html", data={
                "BPM": "--",
                "Temp": "--",
                "Stress": "--",
                "Movement": "--",
                "Voice": "--",
                "Suggestion": "--"
            })

        # Fix missing columns
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "--"

        # Convert numeric
        df['BPM'] = pd.to_numeric(df['BPM'], errors='coerce')
        df['Temp'] = pd.to_numeric(df['Temp'], errors='coerce')

        # Filter valid
        df = df.dropna(subset=['BPM','Temp'])
        df = df[(df['BPM'] > 0) & (df['Temp'] > 0)]

        # Fill missing values
        df = df.fillna("--")

        if not df.empty:
            latest = df.iloc[-1].to_dict()
        else:
            latest = {}

        # Ensure keys
        for key in ["BPM","Temp","Stress",
                    "Movement","Voice","Suggestion"]:
            latest.setdefault(key, "--")

    except Exception as e:
        print("Flask Error:", e)
        latest = {
            "BPM": "--",
            "Temp": "--",
            "Stress": "--",
            "Movement": "--",
            "Voice": "--",
            "Suggestion": "--"
        }

    return render_template("index.html", data=latest)


# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():

    if 'user' not in session:
        return redirect('/login')

    return render_template("analytics.html")


# ---------------- LIVE DATA ----------------
@app.route('/data')
def data():
    try:
        if not os.path.exists(CSV_PATH):
            return "[]"

        df = pd.read_csv(CSV_PATH)

        if df.empty:
            return "[]"

        # Fix missing columns
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "--"

        df['BPM'] = pd.to_numeric(df['BPM'], errors='coerce')
        df['Temp'] = pd.to_numeric(df['Temp'], errors='coerce')

        df = df.dropna(subset=['BPM','Temp'])
        df = df[(df['BPM'] > 0) & (df['Temp'] > 0)]

        df = df.fillna("--")

        return df.tail(30).to_json(orient="records")

    except Exception as e:
        print("Data API Error:", e)
        return "[]"


# ---------------- DOWNLOAD ----------------
@app.route('/download')
def download():
    try:
        return send_file(CSV_PATH, as_attachment=True)
    except Exception as e:
        print("Download Error:", e)
        return "File not available"


# ---------------- REPORT DOWNLOAD ----------------
@app.route('/report')
def report():

    try:

        df = pd.read_csv(CSV_PATH)

        if df.empty:
            return "No data available"

        latest = df.iloc[-1]

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter
        )

        styles = getSampleStyleSheet()

        elements = []

        title = Paragraph(
            "<b>Relaxo Monitor Stress Report</b>",
            styles['Title']
        )

        elements.append(title)
        elements.append(Spacer(1, 20))

        report_data = [

            f"Time: {latest['Time']}",

            f"BPM: {latest['BPM']}",

            f"Temperature: {latest['Temp']}",

            f"Humidity: {latest['Humidity']}",

            f"Emotion: {latest['Emotion']}",

            f"Movement: {latest['Movement']}",

            f"Voice: {latest['Voice']}",

            f"Stress Level: {latest['Stress']}",

            f"Suggestion: {latest['Suggestion']}"

        ]

        for item in report_data:

            elements.append(
                Paragraph(item, styles['BodyText'])
            )

            elements.append(Spacer(1, 10))

        doc.build(elements)

        pdf = buffer.getvalue()

        buffer.close()

        response = make_response(pdf)

        response.headers['Content-Type'] = 'application/pdf'

        response.headers['Content-Disposition'] = 'attachment; filename=stress_report.pdf'

        return response

    except Exception as e:

        return str(e)


# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        try:

            auth.create_user_with_email_and_password(email, password)

            return redirect('/login')

        except Exception as e:

            return f"Signup Failed: {e}"

    return render_template("signup.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        try:

            user = auth.sign_in_with_email_and_password(email, password)

            session['user'] = email

            return redirect('/')

        except Exception as e:

            return f"Login Failed: {e}"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')


# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🚀 Flask server starting...")
    app.run(debug=True, port=5001, use_reloader=False)