# app.py - pagrindinė Flask aplikacijos logika
#Šiame faile aprašyti maršrutai (routes)

#Reikalingos bibliotekos (importai)
<<<<<<< HEAD
=======
<<<<<<< HEAD
from flask import Flask, render_template
=======
>>>>>>> 4c9aafd
import os
from flask import Flask, render_template
from dotenv import load_dotenv # .env failo nuskaitymui
import mysql.connector
from mysql.connector import Error

#Užkrauname aplinkos kintamuosius iš .env failo
load_dotenv()
<<<<<<< HEAD
=======
>>>>>>> 957c885 (Atnaujintas projektas)
>>>>>>> 4c9aafd

#Sukuriame Flask aplikacijos objektą
app = Flask(__name__)

<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> 4c9aafd
#Duomenų bazės prijungimas
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT",3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

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
        



<<<<<<< HEAD
=======
>>>>>>> 957c885 (Atnaujintas projektas)
>>>>>>> 4c9aafd
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

<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> 4c9aafd
#Maršrutas: komentarų puslapis
@app.route("/komentarai", methods=["GET", "POST"]) #Dekoratorius
def komentarai():
    return render_template(
        "komentarai.html"
    )

<<<<<<< HEAD
=======
>>>>>>> 957c885 (Atnaujintas projektas)
>>>>>>> 4c9aafd
#Aplikacijos paleidimas
#Paleidimo metu kai debug = True - automatinis aplikacijos perkrovimas pakeitus kodą + klaidų rodymas
if __name__ == "__main__":
    app.run(debug=True)