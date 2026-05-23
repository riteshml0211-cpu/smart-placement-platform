from flask import Flask, render_template, request, redirect, session
from openai import OpenAI
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "secret123"

# =========================================
# DATABASE CONNECTION (NEON)
# =========================================

try:

    conn = psycopg2.connect(
        os.getenv("DATABASE_URL")
    )

    cursor = conn.cursor()

    print("✅ Database Connected")

except Exception as e:

    print("❌ Database Error:", e)

# =========================================
# AI CLIENT (GROQ)
# =========================================

try:

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )

    print("✅ Groq AI Connected")

except Exception as e:

    print("❌ AI Error:", e)

# =========================================
# CREATE USERS TABLE
# =========================================

try:

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE,
        password VARCHAR(100)
    )
    """)

    conn.commit()

    print("✅ Users Table Ready")

except Exception as e:

    conn.rollback()

    print("❌ Table Error:", e)

# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():

    return render_template("index.html")

# =========================================
# REGISTER PAGE
# =========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        try:

            name = request.form["name"]
            password = request.form["password"]

            cursor.execute(
                "SELECT * FROM users WHERE name=%s",
                (name,)
            )

            existing_user = cursor.fetchone()

            if existing_user:

                return "⚠️ Username already exists"

            cursor.execute(
                "INSERT INTO users(name,password) VALUES(%s,%s)",
                (name, password)
            )

            conn.commit()

            return redirect("/login")

        except Exception as e:

            conn.rollback()

            return f"Register Error: {str(e)}"

    return render_template("register.html")

# =========================================
# LOGIN PAGE
# =========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        try:

            name = request.form["name"]
            password = request.form["password"]

            cursor.execute(
                "SELECT * FROM users WHERE name=%s AND password=%s",
                (name, password)
            )

            user = cursor.fetchone()

            if user:

                session["user"] = user[1]

                return redirect("/dashboard")

            else:

                return "❌ Invalid Username or Password"

        except Exception as e:

            conn.rollback()

            return f"Login Error: {str(e)}"

    return render_template("login.html")

# =========================================
# DASHBOARD
# =========================================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:

        return redirect("/login")

    return render_template(
        "dashboard.html",
        user=session["user"]
    )

# =========================================
# AI APTITUDE
# =========================================

@app.route("/aptitude")
def aptitude():

    if "user" not in session:

        return redirect("/login")

    result = ""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": """
                    Generate one aptitude MCQ question.

                    Include:
                    1. Question
                    2. Four options
                    3. Correct answer
                    4. Explanation

                    Keep it beginner friendly.
                    """
                }
            ]
        )

        result = response.choices[0].message.content

    except Exception as e:

        result = f"AI Error: {str(e)}"

    return render_template(
        "aptitude.html",
        result=result
    )

# =========================================
# AI CODING
# =========================================

@app.route("/coding")
def coding():

    if "user" not in session:

        return redirect("/login")

    result = ""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": """
                    Generate one Python coding interview question.

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

    except Exception as e:

        result = f"AI Error: {str(e)}"

    return render_template(
        "coding.html",
        result=result
    )

# =========================================
# AI CODE CHECKER
# =========================================

@app.route("/check-code", methods=["POST"])
def check_code():

    if "user" not in session:

        return redirect("/login")

    feedback = ""

    try:

        code = request.form["code"]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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

    except Exception as e:

        feedback = f"AI Error: {str(e)}"

    return render_template(
        "coding_result.html",
        feedback=feedback
    )

# =========================================
# MOCK INTERVIEW
# =========================================

@app.route("/mock-interview", methods=["GET", "POST"])
def mock_interview():

    if "user" not in session:

        return redirect("/login")

    result = ""

    if request.method == "POST":

        role = request.form["role"]

        try:

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Conduct a mock interview for:

                        {role}

                        Ask:
                        1. HR Questions
                        2. Technical Questions
                        3. Behavioral Questions
                        """
                    }
                ]
            )

            result = response.choices[0].message.content

        except Exception as e:

            result = f"AI Error: {str(e)}"

    return render_template(
        "mock_interview.html",
        result=result
    )

# =========================================
# SKILL TRACKER
# =========================================

@app.route("/skills")
def skills():

    if "user" not in session:

        return redirect("/login")

    return render_template("skills.html")

# =========================================
# AI ASSISTANT
# =========================================

@app.route("/assistant", methods=["GET", "POST"])
def assistant():

    if "user" not in session:

        return redirect("/login")

    result = ""

    if request.method == "POST":

        question = request.form["question"]

        try:

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        You are an AI placement mentor.

                        Help student with:
                        - placements
                        - coding
                        - aptitude
                        - interviews
                        - resume

                        Question:
                        {question}
                        """
                    }
                ]
            )

            result = response.choices[0].message.content

        except Exception as e:

            result = f"AI Error: {str(e)}"

    return render_template(
        "assistant.html",
        result=result
    )

# =========================================
# RESUME PAGE
# =========================================

@app.route("/resume")
def resume():

    if "user" not in session:

        return redirect("/login")

    return render_template("resume.html")

# =========================================
# AI RESUME ANALYZER
# =========================================

@app.route("/resume-ai", methods=["GET", "POST"])
def resume_ai():

    if "user" not in session:

        return redirect("/login")

    result = ""

    if request.method == "POST":

        try:

            resume_text = request.form["resume_text"]

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Analyze this resume.

                        Give:
                        1. ATS Score
                        2. Missing Skills
                        3. Suggestions
                        4. Placement Readiness

                        Resume:
                        {resume_text}
                        """
                    }
                ]
            )

            result = response.choices[0].message.content

        except Exception as e:

            result = f"AI Error: {str(e)}"

    return render_template(
        "resume_ai.html",
        result=result
    )

# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

# =========================================
# RUN APP
# =========================================

if __name__ == "__main__":

    app.run(debug=True)
