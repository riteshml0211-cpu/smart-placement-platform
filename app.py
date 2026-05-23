from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

bcrypt = Bcrypt(app)

# DATABASE CONNECTION
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# CREATE USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
""")

# CREATE RESULTS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    score INTEGER
)
""")

conn.commit()

# QUIZ QUESTIONS
questions = [
    {
        "question": "What is the time complexity of binary search?",
        "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
        "answer": "O(log n)"
    },

    {
        "question": "Which data structure uses FIFO?",
        "options": ["Stack", "Queue", "Tree", "Graph"],
        "answer": "Queue"
    },

    {
        "question": "Python is?",
        "options": ["Compiled", "Interpreted", "Assembly", "Machine"],
        "answer": "Interpreted"
    }
]

# HOME
@app.route("/")
def home():
    return render_template("index.html")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor.execute(
            "INSERT INTO users (name,email,password) VALUES (?,?,?)",
            (name, email, hashed_password)
        )

        conn.commit()

        return redirect("/login")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            if bcrypt.check_password_hash(user[3], password):

                session["user"] = user[1]

                return redirect("/dashboard")

    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        user=session["user"]
    )

# QUIZ
@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        score = 0

        for i in range(len(questions)):

            selected = request.form.get(str(i))

            if selected == questions[i]["answer"]:
                score += 1

        cursor.execute(
            "INSERT INTO results (user,score) VALUES (?,?)",
            (session["user"], score)
        )

        conn.commit()

        return render_template(
            "result.html",
            score=score
        )

    return render_template(
        "quiz.html",
        questions=questions
    )

# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# RUN APP
if __name__ == "__main__":
    app.run(debug=True)