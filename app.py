# ============================================================
# app.py – pagrindinė Flask aplikacijos logika
# ============================================================
# Šiame faile aprašyti visi maršrutai (routes), duomenų bazės
# prisijungimas ir lentelės kūrimas. Komentarų funkcionalumas
# naudoja MySQL duomenų bazę – komentarai įrašomi ir skaitomi
# iš lentelės "komentarai".
# ============================================================

# --- Importai ---
import os
from flask import Flask, render_template, request
from dotenv import load_dotenv          # .env failui skaityti
import mysql.connector
from mysql.connector import Error

# Užkrauname aplinkos kintamuosius iš .env failo
# (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
load_dotenv()

# Sukuriame Flask aplikacijos objektą
app = Flask(__name__)


# ============================================================
# Duomenų bazės prisijungimo funkcija
# ============================================================
# Grąžina naują MySQL ryšio objektą. Kiekvieną kartą kviečiama
# iš naujo, kad nebūtų problemų su pasibaigusiais ryšiais.
# ============================================================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# ============================================================
# Automatinis lentelės sukūrimas (paleidimo metu)
# ============================================================
# Ši funkcija kviečiama vieną kartą startuojant aplikaciją.
# Jei lentelė "komentarai" dar neegzistuoja – ji sukuriama.
# Lentelės stulpeliai:
#   id       – automatinis numeris (PRIMARY KEY)
#   vardas   – komentaro autoriaus vardas
#   elpastas – autoriaus el. paštas
#   zinute   – komentaro tekstas
#   sukurta  – įrašymo data ir laikas (automatinis)
# ============================================================
def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS komentarai (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vardas VARCHAR(100) NOT NULL,
            elpastas VARCHAR(150) NOT NULL,
            zinute TEXT NOT NULL,
            sukurta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        cursor.execute(create_table_query)
        conn.commit()

        cursor.close()
        conn.close()

        print("Lentelė 'komentarai' paruošta.")

    except Error as e:
        print("Klaida kuriant lentelę:", e)


# ============================================================
# Maršrutas: pagrindinis puslapis
# ============================================================
# URL: /
# Metodas: GET
# Tiesiog atvaizduoja index.html šabloną.
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# Maršrutas: kontaktų puslapis (forma)
# ============================================================
# URL: /kontaktai
# Metodai: GET ir POST
# GET  – rodoma tuščia kontaktų forma
# POST – paimami formos laukai ir parodomas patvirtinimas
#         (duomenys kol kas nėra saugomi į DB)
# ============================================================
@app.route("/kontaktai", methods=["GET", "POST"])
def kontaktai():
    if request.method == "POST":
        # Nuskaitome formos laukų reikšmes
        vardas = request.form.get("vardas")
        elpastas = request.form.get("elpastas")
        zinute = request.form.get("zinute")

        # Perduodame duomenis atgal į šabloną – rodome patvirtinimą
        return render_template(
            "kontaktai.html",
            sekme=True,
            vardas=vardas,
            elpastas=elpastas,
            zinute=zinute
        )

    return render_template("kontaktai.html", sekme=False)


# ============================================================
# Maršrutas: komentarų puslapis
# ============================================================
# URL: /komentarai
# Metodai: GET ir POST
#
# GET  – nuskaitomi visi komentarai iš DB lentelės "komentarai"
#         ir perduodami į šabloną komentarai.html. Komentarai
#         rūšiuojami nuo naujausio (DESC pagal sukurta).
#
# POST – iš formos paimami vardas, elpastas ir zinute, įrašomi
#         į DB. Po sėkmingo įrašymo nustatomas sekme=True, kad
#         šablonas parodytų patvirtinimo žinutę. Tada vėl
#         nuskaitomi visi komentarai ir perduodami šablonui.
#
# Jei DB operacija nepavyksta – klaidos pranešimas perduodamas
# šablonui per kintamąjį "klaida".
# ============================================================
@app.route("/komentarai", methods=["GET", "POST"])
def komentarai():
    sekme = False       # Ar komentaras ką tik sėkmingai išsaugotas
    klaida = None       # Klaidos pranešimas (jei kas nors nepavyko)
    visi_komentarai = []  # Sąrašas komentarų, kuriuos rodysime puslapyje

    # --- POST: vartotojas pateikė naują komentarą ---
    if request.method == "POST":
        vardas = request.form.get("vardas")
        elpastas = request.form.get("elpastas")
        zinute = request.form.get("zinute")

        try:
            # Prisijungiame prie DB
            conn = get_db_connection()
            cursor = conn.cursor()

            # Įrašome naują komentarą naudodami parametrizuotą užklausą
            # (%s apsaugo nuo SQL injekcijų)
            cursor.execute(
                "INSERT INTO komentarai (vardas, elpastas, zinute) VALUES (%s, %s, %s)",
                (vardas, elpastas, zinute)
            )
            conn.commit()

            cursor.close()
            conn.close()

            # Pažymime, kad įrašymas pavyko
            sekme = True

        except Error as e:
            # Jei DB operacija nepavyko – išsaugome klaidos pranešimą
            klaida = f"Nepavyko išsaugoti komentaro: {e}"

    # --- Nuskaitome visus komentarus iš DB (ir GET, ir POST atvejais) ---
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # dictionary=True grąžina dict, ne tuple

        # Rūšiuojame nuo naujausio komentaro
        cursor.execute("SELECT vardas, elpastas, zinute, sukurta FROM komentarai ORDER BY sukurta DESC")
        visi_komentarai = cursor.fetchall()

        cursor.close()
        conn.close()

    except Error as e:
        klaida = f"Nepavyko nuskaityti komentarų: {e}"

    # Perduodame viską į šabloną
    return render_template(
        "komentarai.html",
        sekme=sekme,
        klaida=klaida,
        komentarai=visi_komentarai
    )


# ============================================================
# Maršrutas: DB prisijungimo testas
# ============================================================
# URL: /db-test
# Patikrina ar pavyksta prisijungti prie MySQL serverio.
# Naudinga derinimo (debugging) metu.
# ============================================================
@app.route("/db-test")
def db_test():
    try:
        conn = get_db_connection()

        if conn.is_connected():
            conn.close()
            return "✅ Prisijungimas prie MySQL pavyko!"

        return "❌ Prisijungimas nepavyko."

    except Error as e:
        return f"❌ Klaida jungiantis: {e}"


# ============================================================
# Aplikacijos paleidimas
# ============================================================
# create_tables() kviečiama tik paleidus tiesiogiai (python app.py).
# debug=True – automatinis perkrovimas pakeitus kodą + klaidų rodymas.
# ============================================================
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
