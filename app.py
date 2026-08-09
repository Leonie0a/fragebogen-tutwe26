from flask import Flask, render_template, request, redirect, session, Response
import random
import sqlite3
import datetime
import ast
from openpyxl import Workbook
from openpyxl.styles import PatternFill
import io
from fragen import fragen

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_PASSWORD = "IKLMZ"


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
        session["saved"] = False
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
            return render_template(
                "frage.html",
                frage=frage,
                antworten=antworten,
                error="Bitte wähle eine Antwort"
            )

        # 🔥 WICHTIG: wir speichern TEXT + KATEGORIE sauber getrennt
        chosen = []

        for a in frage["antworten"]:
            if a["kategorie"] in selected:
                chosen.append({
                    "god": a["kategorie"],
                    "text": a["text"]
                })

        session["answers"].append({
            "frage": frage["frage"],
            "selected": chosen
        })

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

    for eintrag in answers:
        antworten = eintrag.get("selected", [])

        for a in antworten:
            god = a.get("god")
            if god:
                counter[god] += 1

    return {k: v * 10 for k, v in counter.items()}

# ---------------------------
# ENDE
# ---------------------------
@app.route("/ende")
def ende():
    # 🔥 Schon gespeichert?
    if session.get("saved"):
        return render_template("ende.html")

    name = session.get("name")
    buddy = session.get("buddy")
    answers = session.get("answers")

    result = berechne_result(answers)

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO results (name, buddy, time, answers, result) VALUES (?, ?, ?, ?, ?)",
        (
            name,
            buddy,
            (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%d.%m.%Y %H:%M"),
            str(answers),
            str(result)
        )
    )

    conn.commit()
    conn.close()

    # 🔥 markieren als gespeichert
    session["saved"] = True

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
# ADMIN RESET
# ---------------------------
@app.route("/admin/reset", methods=["POST"])
def reset():
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute("DELETE FROM results")
    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")

# ---------------------------
# ADMIN CARDS
# ---------------------------
@app.route("/admin/cards")
def cards():
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute("SELECT name, buddy, time, result, answers FROM results")
    rows = c.fetchall()
    conn.close()

    import ast

    data = []
    for r in rows:
        name = r[0]
        buddy = r[1]
        time = r[2]
        result = ast.literal_eval(r[3])
        answers = ast.literal_eval(r[4])

        data.append((name, buddy, time, result, answers))

    return render_template("admin_cards.html", data=data)


# ---------------------------
# EXCEL
# ---------------------------

@app.route("/admin/export")
def export_excel():
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute("SELECT name, buddy, result FROM results")
    rows = c.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Ergebnisse"

    gods = ["Athene", "Poseidon", "Demeter", "Hades", "Apollo"]

    # Header
    ws.append(["Name"] + gods + ["Buddy"])

    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")

    for r in rows:
        name = r[0]
        buddy = r[1]

        result = ast.literal_eval(r[2])

        row_values = [name]
        max_value = max(result.values()) if result else 0

        # Gott-Werte
        for g in gods:
            row_values.append(result.get(g, 0))

        row_values.append(buddy)

        ws.append(row_values)

        # 🔥 Grün markieren (höchster Wert)
        row_index = ws.max_row

        for col_index, g in enumerate(gods, start=2):
            cell = ws.cell(row=row_index, column=col_index)

            if cell.value == max_value and max_value > 0:
                cell.fill = green_fill

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=ergebnisse.xlsx"}
    )


# ---------------------------
# ADMIN FRAGEN AUSWERTUNG
# ---------------------------
@app.route("/admin/fragen")
def admin_fragen():
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("daten.db")
    c = conn.cursor()
    c.execute("SELECT answers FROM results")
    rows = c.fetchall()
    conn.close()

    # 🔢 Zähler vorbereiten
    stats = {}

    for f in fragen:
        stats[f["frage"]] = {}
        for a in f["antworten"]:
            stats[f["frage"]][a["text"]] = {
                "god": a["kategorie"],
                "count": 0
            }

    total_people = len(rows)

    # 🔢 Antworten zählen
    for r in rows:
        try:
            answers = ast.literal_eval(r[0])
        except:
            continue

        for entry in answers:
            frage_text = entry["frage"]

            for s in entry["selected"]:
                answer_text = s["text"]

                if frage_text in stats and answer_text in stats[frage_text]:
                    stats[frage_text][answer_text]["count"] += 1

    # 📊 Prozent berechnen
    for frage_text in stats:
        for answer_text in stats[frage_text]:
            count = stats[frage_text][answer_text]["count"]

            if total_people > 0:
                percent = round(count / total_people * 100, 1)
            else:
                percent = 0

            stats[frage_text][answer_text]["percent"] = percent

    return render_template("admin_fragen.html", stats=stats)

# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
