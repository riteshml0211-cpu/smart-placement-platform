from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE CONNECTION
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# CREATE USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
""")

conn.commit()

# HOME PAGE -> INDEX.HTML
@app.route("/")
def home():
    return render_template("index.html")

# REGISTER PAGE
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

# LOGIN PAGE
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

# DASHBOARD PAGE
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        user=session["user"]
    )

# QUIZ PAGE
@app.route("/quiz")
def quiz():

    if "user" not in session:
        return redirect("/login")

    return render_template("quiz.html")

# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

# RUN APP
if __name__ == "__main__":
    app.run(debug=True)
