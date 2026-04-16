from flask import Flask, render_template, request, redirect, session
import random
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_PASSWORD = "IKLMZ"

# ---------------------------
# FRAGEN
# ---------------------------
fragen = [
    {
        "frage": "Was beschreibt dich am besten?",
        "multi": False,
        "antworten": [
            {"text": "Analytisch", "kategorie": "A"},
            {"text": "Kreativ", "kategorie": "B"},
            {"text": "Strukturiert", "kategorie": "C"},
            {"text": "Spontan", "kategorie": "D"},
            {"text": "Sozial", "kategorie": "E"},
        ]
    },
    {
        "frage": "Was machst du gerne?",
        "multi": True,
        "antworten": [
            {"text": "Lesen", "kategorie": "A"},
            {"text": "Sport", "kategorie": "B"},
            {"text": "Musik", "kategorie": "C"},
            {"text": "Reisen", "kategorie": "D"},
            {"text": "Gaming", "kategorie": "E"},
        ]
    }
]

# ---------------------------
# DB
# ---------------------------
def init_db():
    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            time TEXT,
            answers TEXT,
            result TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# START
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        session["name"] = request.form["name"]
        session["index"] = 0
        session["answers"] = []
        return redirect("/frage")
    return render_template("start.html")

# ---------------------------
# FRAGEN LOGIK
# ---------------------------
@app.route("/frage", methods=["GET", "POST"])
def frage():
    i = session.get("index", 0)

    if i >= len(fragen):
        return redirect("/ende")

    frage = fragen[i]
    antworten = frage["antworten"].copy()
    random.shuffle(antworten)

    if request.method == "POST":
        selected = request.form.getlist("antwort")
        session["answers"].append(selected)
        session["index"] = i + 1
        return redirect("/frage")

    return render_template("frage.html", frage=frage, antworten=antworten)

# ---------------------------
# AUSWERTUNG
# ---------------------------
def berechne_result(answers):
    counter = {"A":0, "B":0, "C":0, "D":0, "E":0}

    for antwort_liste in answers:
        for k in antwort_liste:
            counter[k] += 1

    total = sum(counter.values())
    if total == 0:
        return counter

    return {
        k: round(v / total * 100, 1)
        for k, v in counter.items()
    }

# ---------------------------
# ENDE
# ---------------------------
@app.route("/ende")
def ende():
    name = session.get("name")
    answers = session.get("answers")

    result = berechne_result(answers)

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO results (name, time, answers, result) VALUES (?, ?, ?, ?)",
        (name, str(datetime.datetime.now()), str(answers), str(result))
    )
    conn.commit()
    conn.close()

    return render_template("ende.html")

# ---------------------------
# ADMIN LOGIN
# ---------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        return "Falsches Passwort"

    return render_template("admin_login.html")

# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
@app.route("/admin/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute("SELECT * FROM results")
    data = c.fetchall()
    conn.close()

    return render_template("admin.html", data=data)

# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)