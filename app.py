# app.py - pagrindinė Flask aplikacijos logika
#Šiame faile aprašyti maršrutai (routes)

#Reikalingos bibliotekos (importai)
from flask import Flask, render_template

#Sukuriame Flask aplikacijos objektą
app = Flask(__name__)

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

#Aplikacijos paleidimas
#Paleidimo metu kai debug = True - automatinis aplikacijos perkrovimas pakeitus kodą + klaidų rodymas
if __name__ == "__main__":
    app.run(debug=True)