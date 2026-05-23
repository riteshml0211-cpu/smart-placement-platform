from flask import Flask, render_template, request, redirect, session
import sqlite3
from openai import OpenAI

import os
app = Flask(__name__)
app.secret_key = "secret123"

# =========================
# DATABASE CONNECTION
# =========================

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# GROK AI CLIENT
# =========================


client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# =========================
# CREATE USERS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
""")

conn.commit()

# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")

# =========================
# REGISTER PAGE
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password)
        )

        conn.commit()

        return redirect("/login")

    return render_template("register.html")

# =========================
# LOGIN PAGE
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        if user:

            session["user"] = user[1]

            return redirect("/dashboard")

    return render_template("login.html")

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        user=session["user"]
    )

# =========================
# QUIZ PAGE
# =========================

@app.route("/quiz")
def quiz():

    if "user" not in session:
        return redirect("/login")

    return render_template("quiz.html")

# =========================
# APTITUDE PAGE
# =========================

@app.route("/aptitude")
def aptitude():

    if "user" not in session:
        return redirect("/login")

    response = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {
                "role": "user",
                "content": """
                Generate one aptitude MCQ question.

                Format:
                Question:
                Options:
                A)
                B)
                C)
                D)

                Correct Answer:
                Explanation:

                Difficulty: Medium

                Keep it short.
                """
            }
        ]
    )

    result = response.choices[0].message.content

    return render_template(
        "aptitude.html",
        result=result
    )
# =========================
# CODING PAGE
# =========================

@app.route("/coding")
def coding():

    if "user" not in session:
        return redirect("/login")

    response = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {
                "role": "user",
                "content": """
                Generate one coding interview question.

                Include:
                1. Problem Statement
                2. Example Input
                3. Example Output
                4. Difficulty Level

                Keep it beginner friendly.
                """
            }
        ]
    )

    result = response.choices[0].message.content

    return render_template(
        "coding.html",
        result=result
    )

# =========================
# CODING AI
# =========================

@app.route("/coding-ai", methods=["GET", "POST"])
def coding_ai():

    if "user" not in session:
        return redirect("/login")

    result = ""

    if request.method == "POST":

        question = request.form["question"]

        response = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Solve this coding question in Python.

                    Give explanation also.

                    Question:
                    {question}
                    """
                }
            ]
        )

        result = response.choices[0].message.content

    return render_template(
        "coding_ai.html",
        result=result
    )

@app.route("/check-code", methods=["POST"])
def check_code():

    if "user" not in session:
        return redirect("/login")

    code = request.form["code"]

    response = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {
                "role": "user",
                "content": f"""
                Check this Python code.

                Give:
                1. Is code correct?
                2. Errors
                3. Improvements
                4. Optimized approach
                5. Score out of 10

                Code:
                {code}
                """
            }
        ]
    )

    feedback = response.choices[0].message.content

    return render_template(
        "coding_result.html",
        feedback=feedback
    )
# =========================
# RESUME ANALYZER PAGE
# =========================

@app.route("/resume")
def resume():

    if "user" not in session:
        return redirect("/login")

    return render_template("resume.html")

# =========================
# RESUME AI ANALYZER
# =========================

@app.route("/resume-ai", methods=["GET", "POST"])
def resume_ai():

    if "user" not in session:
        return redirect("/login")

    result = ""

    if request.method == "POST":

        resume_text = request.form["resume_text"]

        response = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Analyze this resume.

                    Give:
                    1. ATS Score
                    2. Missing Skills
                    3. Improvement Suggestions
                    4. Placement Readiness

                    Resume:
                    {resume_text}
                    """
                }
            ]
        )

        result = response.choices[0].message.content

    return render_template(
        "resume_ai.html",
        result=result
    )

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=True)
