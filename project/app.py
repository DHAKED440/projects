from flask import Flask, render_template, request, redirect, session
import pandas as pd
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- MYSQL CONNECTION ----------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",   # change if needed
        database="quizapp"
    )

# ---------------- LOAD CSV ----------------
df = pd.read_csv(r"D:\quiz app\project\clean_general_aptitude_dataset.csv", sep=';', engine='python')
df.columns = df.columns.str.strip().str.lower()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():

    if "user" in session:
        return redirect("/home")     

    if request.method == "POST":
        email = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = email
            return redirect("/home")
        else:
            return "Invalid Login"

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        phone = request.form["phone"]
        email = request.form["email"]
        age = request.form["age"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (first_name, last_name, phone, email, age, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (first, last, phone, email, age, password))
            conn.commit()
        except:
            return "User already exists"

        conn.close()
        return redirect("/")

    return render_template("signup.html")


# ---------------- HOME ----------------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT first_name FROM users WHERE email=%s", (session["user"],))
    user = cursor.fetchone()

    conn.close()

    return render_template("home.html", name=user[0])


# ---------------- START QUIZ ----------------
@app.route("/start_quiz")
def start_quiz():
    session["q_index"] = 0
    session["score"] = 0
    session["lifeline_5050_used"] = False
    session["lifeline_5050_active"] = False

    session["lifeline_audience_used"] = False
    session["lifeline_phone_used"] = False

    import time
    session["start_time"] = time.time()
    session["correct"] = 0
    session["wrong"] = 0
    return redirect("/quiz")


# ---------------- QUIZ ----------------
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "user" not in session:
        return redirect("/")
    
    lifeline_active = session.get("lifeline_5050_active", False)
    lifeline_used = session.get("lifeline_5050_used", False)

    audience_used = session.get("lifeline_audience_used", False)
    phone_used = session.get("lifeline_phone_used", False)

    q_index = session.get("q_index", 0)

    if q_index >= 10:
      return redirect("/result")

    question = df.iloc[q_index]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT first_name FROM users WHERE email=%s", (session["user"],))
    user = cursor.fetchone()
    conn.close()

    player_name = user[0]

    result = None
    selected = None
    correct_option = str(question["answer"]).strip().lower()

    options_map = {
    "a": question["option a"],
    "b": question["option b"],
    "c": question["option c"],
    "d": question["option d"]
}

    correct = options_map.get(correct_option)

    if request.method == "POST":
        selected = request.form["option"].strip()

        if selected.strip().lower() == str(correct).strip().lower():
         session["score"] += 1
         session["correct"] += 1
         result = "correct"
        else:
         session["wrong"] += 1
         result = "wrong"

        # ✅ show same question with result (no index increase here)
        return render_template(
            "quiz.html",
            question=question,
            selected=selected,
            correct=correct,
            result=result,
            name=player_name,
            lifeline_active=lifeline_active,
            lifeline_used=lifeline_used,

            poll=session.get("poll"),
            phone=session.get("phone_suggestion"),
            audience_used=audience_used,
            phone_used=phone_used
        )

    # GET request
    return render_template(
        "quiz.html",
        question=question,
        result=None,
        name=player_name,
        lifeline_active=lifeline_active,
        lifeline_used=lifeline_used,

        poll=session.get("poll"),
        phone=session.get("phone_suggestion"),
        audience_used=audience_used,
        phone_used=phone_used

    )

# ---------------- RESULT ----------------
@app.route("/result")
def result():
    import time
    
    total_time = int(time.time() - session.get("start_time", time.time()))

    score = session.get("score", 0)
    progress = int((score / 10) * 100)

    return render_template(
        "result.html",
        score=score,
        correct=session.get("correct", 0),
        wrong=session.get("wrong", 0),
        time_spent=total_time,
        progress=progress   # 🔥 MUST
    )
#-----------------NEXT BUTTON-------------

@app.route("/next")
def next_question():
    session["q_index"] += 1
    session["lifeline_5050_active"] = False   # ❗ reset for next question
    return redirect("/quiz")

#-----------------LIFELINE 50:50-------------
@app.route("/lifeline_5050")
def lifeline():
    session["lifeline_5050_active"] = True   # current question
    session["lifeline_5050_used"] = True     # permanently used
    return redirect("/quiz")

#-----------------AUDIENCE POLL--------------

import random

@app.route("/audience_poll")
def audience_poll():
    if not session.get("lifeline_audience_used", False):
        session["lifeline_audience_used"] = True

        # random % generate
        poll = {
            "A": random.randint(10, 40),
            "B": random.randint(10, 40),
            "C": random.randint(10, 40),
            "D": random.randint(10, 40)
        }

        session["poll"] = poll

    return redirect("/quiz")
#-----------------PHONE FRIEND------------

@app.route("/phone_friend")
def phone_friend():
    if not session.get("lifeline_phone_used", False):
        session["lifeline_phone_used"] = True

        # friend suggestion (random)
        import random
        suggestion = random.choice(["A", "B", "C", "D"])
        session["phone_suggestion"] = suggestion

    return redirect("/quiz")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)