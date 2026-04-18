from flask import Flask, render_template, request, redirect, session
import random
import sqlite3
import datetime
import ast

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_PASSWORD = "IKLMZ"

# ---------------------------
# FRAGEN (UNVERÄNDERT)
# ---------------------------
fragen = [
    {
        "frage": "Als welches Tier willst du wiedergeboren werden?",
        "multi": False,
        "antworten": [
            {"text": "Hund", "kategorie": "Hades"},
            {"text": "Pferd", "kategorie": "Poseidon"},
            {"text": "Delfin", "kategorie": "Demeter"},
            {"text": "Eule", "kategorie": "Athene"},
            {"text": "Rabe", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Was siehst du in diesem Bild?",
        "bild": "/static/gerald.jpg",
        "multi": False,
        "antworten": [
            {"text": "Skorpion", "kategorie": "Hades"},
            {"text": "Fisch", "kategorie": "Poseidon"},
            {"text": "Jungfrau", "kategorie": "Demeter"},
            {"text": "Widder", "kategorie": "Athene"},
            {"text": "Zwilling", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Was hättest du am liebsten als useless talent?",
        "multi": False,
        "antworten": [
            {"text": "Galgenmännchen", "kategorie": "Hades"},
            {"text": "Luft anhalten", "kategorie": "Poseidon"},
            {"text": "Loch buddeln", "kategorie": "Demeter"},
            {"text": "Schiffe versenken", "kategorie": "Athene"},
            {"text": "Tarotkarten legen", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Such dir ein Abenteuer aus:",
        "multi": False,
        "antworten": [
            {"text": "Du betrittst ein dunkles menschenverlassenes Geisterhaus...", "kategorie": "Hades"},
            {"text": "Die Planke wackelt unter deinen Füßen...", "kategorie": "Poseidon"},
            {"text": "Du läufst zielstrebig den langen Tunnel entlang...", "kategorie": "Demeter"},
            {"text": "Den hörst von Weitem ein lautes Schnaufen...", "kategorie": "Athene"},
            {"text": "Du merkst den Druck auf deiner Brust...", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Weche Stadt würdest du zerstören?",
        "multi": False,
        "antworten": [
            {"text": "Welche nicht?", "kategorie": "Hades"},
            {"text": "Dubai und Athen", "kategorie": "Poseidon"},
            {"text": "Alles, was größer ist als Bielefeld", "kategorie": "Demeter"},
            {"text": "Ganz USA", "kategorie": "Athene"},
            {"text": "Hamburg", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Was ist dein Lieblingsschulfach?",
        "multi": False,
        "antworten": [
            {"text": "Batman Geschichte", "kategorie": "Hades"},
            {"text": "Schwimmunterricht", "kategorie": "Poseidon"},
            {"text": "Werkunterricht", "kategorie": "Demeter"},
            {"text": "Philosophie", "kategorie": "Athene"},
            {"text": "Eurythmie", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Was wäre dein Grund fürs zu spät kommen?",
        "multi": False,
        "antworten": [
            {"text": "Ich bin nie zu spät...", "kategorie": "Hades"},
            {"text": "Meine Geschwister sind schuld!", "kategorie": "Poseidon"},
            {"text": "Ich habe einer Igel-oma geholfen.", "kategorie": "Demeter"},
            {"text": "Was ist zu spät kommen?", "kategorie": "Athene"},
            {"text": "Sonnenbrille vergessen.", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Wie verhälst du dich nach Streit?",
        "multi": False,
        "antworten": [
            {"text": "Ich komme zu deiner Beerdigung.", "kategorie": "Hades"},
            {"text": "Lass uns was trinken gehen.", "kategorie": "Poseidon"},
            {"text": "Bäume umarmen.", "kategorie": "Demeter"},
            {"text": "Ich habe Recht.", "kategorie": "Athene"},
            {"text": "Karma regelt.", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Welcher Satz klingt nach KI?",
        "multi": False,
        "antworten": [
            {"text": "Der Satz klingt generisch...", "kategorie": "Hades"},
            {"text": "Ein Netzwerk aus Datenpunkten...", "kategorie": "Poseidon"},
            {"text": "Praktisch funktioniert...", "kategorie": "Demeter"},
            {"text": "Ein Satz ist eine Einheit...", "kategorie": "Athene"},
            {"text": "Zwischen zwei Atemzügen...", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Unter welchen Umständen ist ein Mord okay?",
        "multi": False,
        "antworten": [
            {"text": "Unter allen Umständen", "kategorie": "Hades"},
            {"text": "Wenn keine Zeugen da sind", "kategorie": "Poseidon"},
            {"text": "Wenn Pflanzen nicht gegossen wurden", "kategorie": "Demeter"},
            {"text": "Wenn die Person dumm ist", "kategorie": "Athene"},
            {"text": "Wenn jemand schief singt", "kategorie": "Apollo"},
        ]
    },
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
            buddy TEXT,
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
        session["buddy"] = request.form.get("buddy")
        session["index"] = 0
        session["answers"] = []
        return redirect("/frage")
    return render_template("start.html")

# ---------------------------
# FRAGEN
# ---------------------------
@app.route("/frage", methods=["GET", "POST"])
def frage():
    if "answers" not in session:
        return redirect("/")

    i = session.get("index", 0)

    if i >= len(fragen):
        return redirect("/ende")

    frage = fragen[i]
    antworten = frage["antworten"].copy()
    random.shuffle(antworten)

    if request.method == "POST":
        selected = request.form.getlist("antwort")

        if not selected:
            return render_template("frage.html", frage=frage, antworten=antworten, error="Bitte wähle eine Antwort")

        session["answers"].append(selected)
        session["index"] = i + 1
        return redirect("/frage")

    return render_template("frage.html", frage=frage, antworten=antworten)

# ---------------------------
# AUSWERTUNG
# ---------------------------
def berechne_result(answers):
    counter = {
        "Hades": 0,
        "Poseidon": 0,
        "Demeter": 0,
        "Athene": 0,
        "Apollo": 0
    }

    for antwort_liste in answers:
        for k in antwort_liste:
            counter[k] = counter.get(k, 0) + 1

    return {k: v * 10 for k, v in counter.items()}

# ---------------------------
# ENDE
# ---------------------------
@app.route("/ende")
def ende():
    name = session.get("name")
    buddy = session.get("buddy")
    answers = session.get("answers")

    result = berechne_result(answers)

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO results (name, buddy, time, answers, result) VALUES (?, ?, ?, ?, ?)",
        (name, buddy, datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), str(answers), str(result))
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

    c.execute("SELECT name, buddy, time, result FROM results")
    rows = c.fetchall()
    conn.close()

    data = []
    for r in rows:
        try:
            result = ast.literal_eval(r[3])
        except:
            result = {}

        data.append((r[0], r[1], r[2], result))

    return render_template("admin.html", data=data)

# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
