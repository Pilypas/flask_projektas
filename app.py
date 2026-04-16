# app.py - pagrindinė Flask aplikacijos logika
#Šiame faile aprašyti maršrutai (routes)

#Reikalingos bibliotekos (importai)

from flask import Flask, render_template, request, session, url_for, redirect # naudoja Jinja2 viduje automatiskai pacio flask

import os
import secrets
from dotenv import load_dotenv # .env failo nuskaitymui
import mysql.connector
from mysql.connector import Error

#Darbui su hash passwordais
from werkzeug.security import generate_password_hash, check_password_hash


#Užkrauname aplinkos kintamuosius iš .env failo
load_dotenv()


#Sukuriame Flask aplikacijos objektą
app = Flask(__name__)

#Secret_KEY (automatinis genravimas, jei nėra rakto .env faile)
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = secrets.token_hex(16)

app.secret_key = secret_key

#Duomenų bazės prijungimas
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT",3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

#Automatinis lentelės sukūrimas (paleidimo metu)
#Ši funkcija kviečiama vieną katą startuojant aplikacijai

def sukurti_db_lenteles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        lenteliu_sukurimo_db_uzklausa = """
        CREATE TABLE IF NOT EXISTS komentarai (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vardas VARCHAR(100) NOT NULL,
            elpastas VARCHAR(150) NOT NULL,
            zinute TEXT NOT NULL,
            sukurta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        vartotoju_sukurimo_db_uzklausa = """
        CREATE TABLE IF NOT EXISTS vartotojai (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vardas VARCHAR(100) NOT NULL,
            elpastas VARCHAR(150) NOT NULL UNIQUE,
            slaptazodis VARCHAR(255) NOT NULL,
            sukurta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        cursor.execute(lenteliu_sukurimo_db_uzklausa)
        cursor.execute(vartotoju_sukurimo_db_uzklausa)
        conn.commit()

        cursor.close()
        conn.close()

        print("Lentelės sėkmingai sukurtos")
    except Error as e:
        print("Klaida kuriant lentelę", e)

# Maršrutas: DB prisijungimo testas
@app.route("/db-testas")
def db_testas():
    try:
        conn = get_db_connection()
        if conn.is_connected():
            return "Prisijungimas prie mysql pavyko !"
        else:
            return "Prisijungimas nepavyko"
    except Error as e:
        return f"Klaida jungiantis: {e}"    
        
#Maršrutas: pagrindinis puslapis
# URL: /
# Metodas: GET
# Atvaizduoja index.html šabloną
@app.route("/") #Dekoratorius
def index():
    return render_template("index.html")

#Maršrutas: kontaktų puslapis (forma)
#Metodai: GET ir POST
@app.route("/kontaktai") #Dekoratorius
def kontaktai():
    return render_template("kontaktai.html")


#Maršrutas: Apie mus puslapis (forma)
#Metodai: GET ir POST
@app.route("/apie") #Dekoratorius
def apie():
    return render_template("apie.html")

#Maršrutas: registracija
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

            # Patikriname, ar vartotojas jau egzistuoja
            cursor.execute("SELECT id FROM vartotojai WHERE elpastas = %s", (elpastas,))
            egzistuojantis_vartotojas = cursor.fetchone()

            if egzistuojantis_vartotojas:
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


#Prisijungimo maršrutas
@app.route("/prisijungimas", methods=["GET", "POST"])
def prisijungimas():
    klaida = None

    if request.method == "POST":
        elpastas = request.form.get("elpastas")
        slaptazodis = request.form.get("slaptazodis")

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM vartotojai WHERE elpastas=%s",(elpastas,))
            vartotojas = cursor.fetchone()

            cursor.close()
            conn.close()

            if vartotojas and check_password_hash(vartotojas["slaptazodis"], slaptazodis):
                session["vartotojo_id"] = vartotojas["id"]
                session["vartotojo_vardas"] = vartotojas["vardas"]
                return redirect(url_for("profilis"))
            else:
                klaida = "Neteisingi duomenys"
        except Error as e:
            klaida = f"Klaida: {e}"        
    return render_template("prisijungimas.html", klaida=klaida)

#Profilio maršrutas (apsaugotas)
@app.route("/profilis")
def profilis():
    if "vartotojo_id" not in session:
        return redirect(url_for("prisijungimas"))
    
    return render_template("profilis.html", vardas=session["vartotojo_vardas"])

#Atsijungimas
@app.route("/atsijungti")
def atsijungti():
    session.clear()
    return redirect(url_for("index"))




#Maršrutas: komentarų puslapis
@app.route("/komentarai", methods=["GET", "POST"]) #Dekoratorius
def komentarai():
    sekme = False
    klaida = None
    visi_komentarai = [] # Sąrašas komentarų, kuriuos rodysime puslapyje

    if request.method == "POST":
        vardas = request.form.get("vardas")
        elpastas = request.form.get("elpastas")
        zinute = request.form.get("zinute")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            #Įrašome naują komentarą naudodami parametrizuotą užklausą
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

    #Nuskaitome visus komentarus iš DB
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #Rikiuojame visus komentarus nuo naujausio komentaro
        cursor.execute("SELECT vardas, elpastas, zinute, sukurta FROM komentarai ORDER BY sukurta DESC") 
        visi_komentarai = cursor.fetchall()
        cursor.close()
        conn.close()
    except Error as e:
        klaida = f"Nepavyko nuskaityti komentarų {e}"

    return render_template(
        "komentarai.html",
        klaida = klaida,
        sekme = sekme,
        komentarai = visi_komentarai
    )

#Aplikacijos paleidimas
#Paleidimo metu kai debug = True - automatinis aplikacijos perkrovimas pakeitus kodą + klaidų rodymas
if __name__ == "__main__":
    sukurti_db_lenteles()
    app.run(debug=True)