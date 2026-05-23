from flask import Flask, render_template, request, redirect, session
from openai import OpenAI
import psycopg2
import os
from PyPDF2 import PdfReader

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
# PERFORMANCE TABLE
# =========================================

try:

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance(
        id SERIAL PRIMARY KEY,
        username VARCHAR(100),
        aptitude_score INTEGER DEFAULT 0,
        coding_score INTEGER DEFAULT 0,
        interview_score INTEGER DEFAULT 0
    )
    """)

    conn.commit()

    print("✅ Performance Table Ready")

except Exception as e:

    conn.rollback()

    print("❌ Performance Table Error:", e)

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

            # INSERT USER

            cursor.execute(
                "INSERT INTO users(name,password) VALUES(%s,%s)",
                (name, password)
            )

            # CREATE PERFORMANCE ROW

            cursor.execute(
                """
                INSERT INTO performance(
                username,
                aptitude_score,
                coding_score,
                interview_score
                )

                VALUES(%s,%s,%s,%s)
                """,
                (name, 0, 0, 0)
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
# PROFILE PAGE
# =========================================

@app.route("/profile")
def profile():

    if "user" not in session:

        return redirect("/login")

    return render_template(
        "profile.html",
        user=session["user"]
    )

# =========================================
# AI APTITUDE
# =========================================

@app.route("/aptitude", methods=["GET", "POST"])
def aptitude():

    if "user" not in session:

        return redirect("/login")

    question = ""
    answer = ""
    explanation = ""
    correct_answer = ""

    # GENERATE QUESTION

    if request.method == "GET":

        try:

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": """
                        Generate one aptitude MCQ question.

                        Format EXACTLY like this:

                        Question:
                        ...

                        A. ...
                        B. ...
                        C. ...
                        D. ...

                        Correct Answer: A

                        Explanation: ...

                        """
                    }
                ]
            )

            data = response.choices[0].message.content

            lines = data.splitlines()

            for line in lines:

                if "Correct Answer:" in line:

                    correct_answer = line.split(":")[1].strip()

                if "Explanation:" in line:

                    explanation = line.replace(
                        "Explanation:",
                        ""
                    ).strip()

            clean_question = ""

            for line in lines:

                if "Correct Answer:" not in line and \
                   "Explanation:" not in line:

                    clean_question += line + "\n"

            return render_template(
                "aptitude.html",
                question=clean_question,
                correct_answer=correct_answer,
                explanation=explanation
            )

        except Exception as e:

            return render_template(
                "aptitude.html",
                question=f"AI Error: {str(e)}"
            )

    # CHECK ANSWER

    selected = request.form["selected"]
    correct = request.form["correct"]
    explanation = request.form["explanation"]
    question = request.form["question"]

    if selected == correct:

        answer = "✅ Correct Answer"

        # UPDATE SCORE

       # CHECK PERFORMANCE ROW

cursor.execute(
    """
    SELECT * FROM performance
    WHERE username=%s
    """,
    (session["user"],)
)

existing = cursor.fetchone()

# CREATE ROW IF NOT EXISTS

if existing is None:

    cursor.execute(
        """
        INSERT INTO performance(
        username,
        aptitude_score,
        coding_score,
        interview_score
        )

        VALUES(%s,%s,%s,%s)
        """,
        (session["user"], 10, 0, 0)
    )

else:

    cursor.execute(
        """
        UPDATE performance
        SET aptitude_score = aptitude_score + 10
        WHERE username=%s
        """,
        (session["user"],)
    )

conn.commit()

    else:

        answer = f"❌ Wrong Answer. Correct Answer is {correct}"

    return render_template(
        "aptitude.html",
        question=question,
        answer=answer,
        explanation=explanation
    )

# =========================================
# AI CODING PAGE
# =========================================

@app.route("/coding")
def coding():

    if "user" not in session:

        return redirect("/login")

    question = ""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": """
                    Generate ONE beginner Python coding question.

                    Include ONLY:
                    1. Problem Statement
                    2. Example Input
                    3. Example Output

                    Do NOT provide answer.
                    """
                }
            ]
        )

        question = response.choices[0].message.content

    except Exception as e:

        question = f"AI Error: {str(e)}"

    return render_template(
        "coding.html",
        question=question
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

        question = request.form["question"]
        code = request.form["code"]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    You are a strict coding interviewer.

                    QUESTION:
                    {question}

                    USER CODE:
                    {code}

                    Evaluate carefully.

                    Return:
                    1. Correct or Wrong
                    2. Logic mistakes
                    3. Syntax errors
                    4. Improvements
                    5. Score out of 10

                    If code does NOT solve the question,
                    clearly say WRONG ANSWER.
                    """
                }
            ]
        )

        feedback_text = response.choices[0].message.content

        feedback = feedback_text

        # UPDATE CODING SCORE

        if "Correct" in feedback_text:

            cursor.execute(
                """
                UPDATE performance
                SET coding_score = coding_score + 10
                WHERE username=%s
                """,
                (session["user"],)
            )

            conn.commit()

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

            # UPDATE INTERVIEW SCORE

            cursor.execute(
                """
                UPDATE performance
                SET interview_score = interview_score + 10
                WHERE username=%s
                """,
                (session["user"],)
            )

            conn.commit()

        except Exception as e:

            result = f"AI Error: {str(e)}"

    return render_template(
        "mock_interview.html",
        result=result
    )

# =========================================
# SKILL TRACKER
# =========================================
# =========================================
# SKILL TRACKER
# =========================================

@app.route("/skills")
def skills():

    if "user" not in session:

        return redirect("/login")

    cursor.execute(
        """
        SELECT aptitude_score,
               coding_score,
               interview_score

        FROM performance

        WHERE username=%s
        """,
        (session["user"],)
    )

    data = cursor.fetchone()

    # IF USER NOT FOUND

    if data is None:

        cursor.execute(
            """
            INSERT INTO performance(
            username,
            aptitude_score,
            coding_score,
            interview_score
            )

            VALUES(%s,%s,%s,%s)
            """,
            (session["user"], 0, 0, 0)
        )

        conn.commit()

        aptitude = 0
        coding = 0
        interview = 0

    else:

        aptitude = data[0]
        coding = data[1]
        interview = data[2]

    return render_template(
        "skills.html",
        aptitude=aptitude,
        coding=coding,
        interview=interview
    )

# =========================================
# PROGRESS ANALYTICS
# =========================================

@app.route("/analytics")
def analytics():

    if "user" not in session:

        return redirect("/login")

    cursor.execute(
        """
        SELECT aptitude_score,
               coding_score,
               interview_score

        FROM performance

        WHERE username=%s
        """,
        (session["user"],)
    )

    data = cursor.fetchone()

    # IF USER NOT FOUND

    if data is None:

        cursor.execute(
            """
            INSERT INTO performance(
            username,
            aptitude_score,
            coding_score,
            interview_score
            )

            VALUES(%s,%s,%s,%s)
            """,
            (session["user"], 0, 0, 0)
        )

        conn.commit()

        aptitude = 0
        coding = 0
        interview = 0

    else:

        aptitude = data[0]
        coding = data[1]
        interview = data[2]

    return render_template(
        "analytics.html",
        aptitude=aptitude,
        coding=coding,
        interview=interview
    )
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

            pdf_file = request.files["resume"]

            reader = PdfReader(pdf_file)

            resume_text = ""

            for page in reader.pages:

                text = page.extract_text()

                if text:

                    resume_text += text

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
                        5. Strengths
                        6. Weaknesses

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
# AI RESUME BUILDER
# =========================================

@app.route("/resume-builder", methods=["GET", "POST"])
def resume_builder():

    if "user" not in session:

        return redirect("/login")

    result = ""

    if request.method == "POST":

        name = request.form["name"]
        skills = request.form["skills"]
        education = request.form["education"]
        projects = request.form["projects"]

        try:

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Create a professional resume.

                        Name:
                        {name}

                        Skills:
                        {skills}

                        Education:
                        {education}

                        Projects:
                        {projects}

                        Format it professionally.
                        """
                    }
                ]
            )

            result = response.choices[0].message.content

        except Exception as e:

            result = f"AI Error: {str(e)}"

    return render_template(
        "resume_builder.html",
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
