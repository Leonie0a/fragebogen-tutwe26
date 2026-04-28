from flask import Flask, render_template, request, redirect, session, Response
import random
import sqlite3
import datetime
import ast
from openpyxl import Workbook
from openpyxl.styles import PatternFill
import io

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_PASSWORD = "IKLMZ"

# ---------------------------
# FRAGEN
# ---------------------------
fragen = [
    {
        "frage": "Als welches Tier willst du wiedergeboren werden?",
        "multi": True,
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
        "multi": True,
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
        "multi": True,
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
        "multi": True,
        "antworten": [
            {"text": "Du betrittst ein dunkles menschenverlassenes Geisterhaus. Du versuchst die verschlossene Stahlgittertür zu öffnen um in den Keller zu gelangen, damit du endlich deine Karriere als Geisterjäger*in starten kannst. Eine deiner inneren Stimmen singt schaurig: Ghostbusters!", "kategorie": "Hades"},
            {"text": "Die Planke wackelt unter deinen Füßen. Die meterhohen Wellen machen dir nichts aus, als du mit sicheren Schritten die Planke zum anderen Schiff überquerst. Mit einem lauten “Ahoi! Alles im Lot auf dem Boot?” verwirrst du die Person, die dir mit einem Säbel gegenübersteht und…", "kategorie": "Poseidon"},
            {"text": "Du läufst zielstrebig den langen heruntergekommenen Tunnel entlang. Um etwas zu sehen fragst du die Glühwürchen nach Hilfe. Gerade als sie mit Ihrem Tanz beginnen sieht du wie sich hinter dir eine geheime Tür öffnet. Von drinnen hörst du die Gummibärenbande und stimmst freudig in ihr Lied mit ein.", "kategorie": "Demeter"},
            {"text": "Du hörst von Weitem ein lautes Schnaufen und freust dich bereits darauf, dass er gleich in deine Falle tappen wird. Seit Ewigkeiten hat es niemand geschafft ihn zu fangen und du wirst nun die erste Person sein die ihn zu Gesicht bekommt. Du stimmst bereits dein Siegeslied an: Hey Hey yippie, hey, yippie, hey…", "kategorie": "Athene"},
            {"text": "Du merkst den Druck auf deiner Brust und dir schwinden fast die Sinne. Du wirst immer höher und höher getragen. Im Rückspiegel siehst du die Welt immer kleiner und kleiner werden. Du spürst erst jetzt wie bedeutend dein Leben sein wird, während du zu neuen Welten aufbrichst. Durch die Lautsprecher erklingt der Gesang: “oohh yeahh yeah I′m your basic average girl And I’m here to save the world”", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Weche Stadt würdest du zerstören?",
        "multi": True,
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
        "multi": True,
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
        "multi": True,
        "antworten": [
            {"text": "Ich bin nie zu spät, alle anderen sind einfach zu früh.", "kategorie": "Hades"},
            {"text": "Meine Geschwister sind schuld!", "kategorie": "Poseidon"},
            {"text": "Ich habe einer Igel-Oma über die Straße geholfen.", "kategorie": "Demeter"},
            {"text": "Was ist “zu spät kommen”?", "kategorie": "Athene"},
            {"text": "Musste zurück, habe meine Sonnenbrille vergessen.", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Wie verhälst du dich nach Streit?",
        "multi": True,
        "antworten": [
            {"text": "Ich komme zu deiner Beerdigung.", "kategorie": "Hades"},
            {"text": "Lass uns was Trinken gehen.", "kategorie": "Poseidon"},
            {"text": "Wir gehen zusammen Bäume umarmen.", "kategorie": "Demeter"},
            {"text": "Wir wissen, ich habe Recht.", "kategorie": "Athene"},
            {"text": "Karma regelt.", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Welcher Satz klingt nicht nach KI?",
        "multi": True,
        "antworten": [
            {"text": "Der Satz, der übertrieben perfekt, generisch und etwas unpersönlich formuliert ist, klingt am ehesten nach KI.", "kategorie": "Hades"},
            {"text": "In einem flirrenden Netzwerk aus Datenpunkten generiere ich mit algorithmischer Präzision eine Antwort, die zugleich effizient und überraschend elegant ist.", "kategorie": "Poseidon"},
            {"text": "Viele Dinge klingen bedeutungsvoll, aber am Ende zählt meistens, was praktisch funktioniert und im Alltag wirklich Bestand hat.", "kategorie": "Demeter"},
            {"text": "Ein Satz ist eine abgeschlossene sprachliche Einheit, die einen vollständigen Gedanken ausdrückt.", "kategorie": "Athene"},
            {"text": "Zwischen zwei Atemzügen flüstert die Zeit von allem, was noch werden will.", "kategorie": "Apollo"},
        ]
    },
    {
        "frage": "Unter welchen Umständen ist ein Mord okay?",
        "multi": True,
        "antworten": [
            {"text": "Unter allen Umständen", "kategorie": "Hades"},
            {"text": "Wenn es keine Zeugen gibt", "kategorie": "Poseidon"},
            {"text": "Wenn die Mitbewohner*in die Pflanzen nicht gegossen hat", "kategorie": "Demeter"},
            {"text": "Wenn die Person dumm ist", "kategorie": "Athene"},
            {"text": "Wenn die Person schief singt", "kategorie": "Apollo"},
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
