from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# DATABASE_URL Ayarı
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modeller
class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    club = db.Column(db.String(100))
    value = db.Column(db.Float, default=0.0)
    img = db.Column(db.String(500))

class Haber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200))
    icerik = db.Column(db.Text)

class Kulup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100))
    logo = db.Column(db.String(500))

# TABLOLARI OLUŞTURAN ÖZEL BLOK
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    sifre = request.args.get('sifre')
    try:
        players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
        haberler = Haber.query.all()
        kulupler = Kulup.query.all()
    except:
        players, haberler, kulupler = [], [], []
    return render_template('index.html', players=players, haberler=haberler, kulupler=kulupler, is_admin=(sifre == "futbol123"), sifre=sifre)

# Diğer rotalar (ekle, haber_ekle vb.) aynı kalabilir...

if __name__ == '__main__':
    # PORT 10000 AYARI BURADA
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
