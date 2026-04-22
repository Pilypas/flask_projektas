# app.py - pagrindinė Flask aplikacijos logika

from flask import Flask, render_template, request, session, url_for, redirect
import os
import secrets
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = secrets.token_hex(16)

app.secret_key = secret_key


# -----------------------------------
# DB prisijungimas
# -----------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# -----------------------------------
# Pagalbinė funkcija stulpelio patikrinimui
# -----------------------------------
def ar_stulpelis_egzistuoja(cursor, table_name, column_name):
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
    """, (table_name, column_name))
    result = cursor.fetchone()
    return result[0] > 0


# -----------------------------------
# Lentelių ir papildomų laukų sukūrimas
# -----------------------------------
def sukurti_db_lenteles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        komentarai_query = """
        CREATE TABLE IF NOT EXISTS komentarai (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vardas VARCHAR(100) NOT NULL,
            elpastas VARCHAR(150) NOT NULL,
            zinute TEXT NOT NULL,
            sukurta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        vartotojai_query = """
        CREATE TABLE IF NOT EXISTS vartotojai (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vardas VARCHAR(100) NOT NULL,
            elpastas VARCHAR(150) NOT NULL UNIQUE,
            slaptazodis VARCHAR(255) NOT NULL,
            sukurta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        paslaugos_query = """
        CREATE TABLE IF NOT EXISTS paslaugos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pavadinimas VARCHAR(150) NOT NULL,
            kategorija VARCHAR(100) NOT NULL,
            trukme_min INT NOT NULL,
            kaina DECIMAL(10,2) NOT NULL,
            aktyvi TINYINT(1) NOT NULL DEFAULT 1,
            aprasymas TEXT,
            sukurta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        cursor.execute(komentarai_query)
        cursor.execute(vartotojai_query)
        cursor.execute(paslaugos_query)

        # Papildomi profilio laukai lentelėje vartotojai
        papildomi_stulpeliai = [
            ("gimimo_metai", "INT NULL"),
            ("miestas", "VARCHAR(100) NULL"),
            ("biografija", "TEXT NULL"),
            ("avataro_nuoroda", "VARCHAR(255) NULL")
        ]

        for stulpelio_pavadinimas, stulpelio_tipas in papildomi_stulpeliai:
            if not ar_stulpelis_egzistuoja(cursor, "vartotojai", stulpelio_pavadinimas):
                alter_query = f"ALTER TABLE vartotojai ADD COLUMN {stulpelio_pavadinimas} {stulpelio_tipas}"
                cursor.execute(alter_query)

        conn.commit()
        cursor.close()
        conn.close()

        print("Lentelės ir papildomi stulpeliai sėkmingai paruošti.")

    except Error as e:
        print("Klaida kuriant lenteles:", e)


# -----------------------------------
# DB testas
# -----------------------------------
@app.route("/db-testas")
def db_testas():
    try:
        conn = get_db_connection()
        if conn.is_connected():
            conn.close()
            return "Prisijungimas prie MySQL pavyko!"
        return "Prisijungimas nepavyko."
    except Error as e:
        return f"Klaida jungiantis: {e}"


# -----------------------------------
# Pagrindiniai puslapiai
# -----------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/kontaktai")
def kontaktai():
    return render_template("kontaktai.html")


@app.route("/apie")
def apie():
    return render_template("apie.html")


# -----------------------------------
# Registracija
# -----------------------------------
@app.route("/registracija", methods=["GET", "POST"])
def registracija():
    klaida = None
    sekme = False

    if request.method == "POST":
        vardas = request.form.get("vardas")
        elpastas = request.form.get("elpastas")
        slaptazodis = request.form.get("slaptazodis")

        if not vardas or not elpastas or not slaptazodis:
            klaida = "Užpildykite visus laukus."
            return render_template("registracija.html", klaida=klaida, sekme=sekme)

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id FROM vartotojai WHERE elpastas = %s", (elpastas,))
            egzistuojantis = cursor.fetchone()

            if egzistuojantis:
                klaida = "Toks vartotojas jau egzistuoja."
            else:
                uzkoduotas_slaptazodis = generate_password_hash(slaptazodis)
                cursor.execute(
                    "INSERT INTO vartotojai (vardas, elpastas, slaptazodis) VALUES (%s, %s, %s)",
                    (vardas, elpastas, uzkoduotas_slaptazodis)
                )
                conn.commit()
                sekme = True

            cursor.close()
            conn.close()

        except Error as e:
            klaida = f"Nepavyko užregistruoti vartotojo: {e}"

    return render_template("registracija.html", klaida=klaida, sekme=sekme)


# -----------------------------------
# Prisijungimas
# -----------------------------------
@app.route("/prisijungimas", methods=["GET", "POST"])
def prisijungimas():
    klaida = None

    if request.method == "POST":
        elpastas = request.form.get("elpastas")
        slaptazodis = request.form.get("slaptazodis")

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM vartotojai WHERE elpastas = %s", (elpastas,))
            vartotojas = cursor.fetchone()

            cursor.close()
            conn.close()

            if vartotojas and check_password_hash(vartotojas["slaptazodis"], slaptazodis):
                session["vartotojo_id"] = vartotojas["id"]
                session["vartotojo_vardas"] = vartotojas["vardas"]
                session["avataro_nuoroda"] = vartotojas.get("avataro_nuoroda")
                return redirect(url_for("profilis"))
            else:
                klaida = "Neteisingi prisijungimo duomenys."

        except Error as e:
            klaida = f"Klaida: {e}"

    return render_template("prisijungimas.html", klaida=klaida)


# -----------------------------------
# Profilis - peržiūra ir redagavimas
# -----------------------------------
@app.route("/profilis", methods=["GET", "POST"])
def profilis():
    if "vartotojo_id" not in session:
        return redirect(url_for("prisijungimas"))

    klaida = None
    sekme = False
    vartotojas = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == "POST":
            vardas = request.form.get("vardas")
            gimimo_metai = request.form.get("gimimo_metai")
            miestas = request.form.get("miestas")
            biografija = request.form.get("biografija")
            avataro_nuoroda = request.form.get("avataro_nuoroda")

            if gimimo_metai == "":
                gimimo_metai = None

            update_query = """
                UPDATE vartotojai
                SET vardas = %s,
                    gimimo_metai = %s,
                    miestas = %s,
                    biografija = %s,
                    avataro_nuoroda = %s
                WHERE id = %s
            """
            cursor.execute(
                update_query,
                (vardas, gimimo_metai, miestas, biografija, avataro_nuoroda, session["vartotojo_id"])
            )
            conn.commit()

            session["vartotojo_vardas"] = vardas
            session["avataro_nuoroda"] = avataro_nuoroda
            sekme = True

        cursor.execute("SELECT * FROM vartotojai WHERE id = %s", (session["vartotojo_id"],))
        vartotojas = cursor.fetchone()

        cursor.close()
        conn.close()

    except Error as e:
        klaida = f"Nepavyko nuskaityti arba atnaujinti profilio: {e}"

    return render_template("profilis.html", vartotojas=vartotojas, sekme=sekme, klaida=klaida)


# -----------------------------------
# Atsijungimas
# -----------------------------------
@app.route("/atsijungti")
def atsijungti():
    session.clear()
    return redirect(url_for("index"))


# -----------------------------------
# Komentarai
# -----------------------------------
@app.route("/komentarai", methods=["GET", "POST"])
def komentarai():
    sekme = False
    klaida = None
    visi_komentarai = []

    if request.method == "POST":
        vardas = request.form.get("vardas")
        elpastas = request.form.get("elpastas")
        zinute = request.form.get("zinute")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO komentarai (vardas, elpastas, zinute) VALUES (%s, %s, %s)",
                (vardas, elpastas, zinute)
            )
            conn.commit()
            cursor.close()
            conn.close()
            sekme = True

        except Error as e:
            klaida = f"Nepavyko išsaugoti komentaro: {e}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT vardas, elpastas, zinute, sukurta FROM komentarai ORDER BY sukurta DESC")
        visi_komentarai = cursor.fetchall()
        cursor.close()
        conn.close()

    except Error as e:
        klaida = f"Nepavyko nuskaityti komentarų: {e}"

    return render_template(
        "komentarai.html",
        klaida=klaida,
        sekme=sekme,
        komentarai=visi_komentarai
    )


# -----------------------------------
# PASLAUGOS - sąrašas
# -----------------------------------
@app.route("/paslaugos")
def paslaugos():
    klaida = None
    visos_paslaugos = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM paslaugos ORDER BY sukurta DESC")
        visos_paslaugos = cursor.fetchall()
        cursor.close()
        conn.close()

    except Error as e:
        klaida = f"Nepavyko nuskaityti paslaugų: {e}"

    return render_template("paslaugos.html", paslaugos=visos_paslaugos, klaida=klaida)


# -----------------------------------
# PASLAUGOS - įvedimas
# -----------------------------------
@app.route("/ivesti-paslauga", methods=["GET", "POST"])
def ivesti_paslauga():
    sekme = False
    klaida = None

    if request.method == "POST":
        pavadinimas = request.form.get("pavadinimas")
        kategorija = request.form.get("kategorija")
        trukme_min = request.form.get("trukme_min")
        kaina = request.form.get("kaina")
        aktyvi = 1 if request.form.get("aktyvi") == "on" else 0
        aprasymas = request.form.get("aprasymas")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO paslaugos (pavadinimas, kategorija, trukme_min, kaina, aktyvi, aprasymas)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pavadinimas, kategorija, trukme_min, kaina, aktyvi, aprasymas))
            conn.commit()
            cursor.close()
            conn.close()
            sekme = True

        except Error as e:
            klaida = f"Nepavyko išsaugoti paslaugos: {e}"

    return render_template("ivesti_paslauga.html", sekme=sekme, klaida=klaida)


# -----------------------------------
# Paleidimas
# -----------------------------------
if __name__ == "__main__":
    sukurti_db_lenteles()
    app.run(debug=True)