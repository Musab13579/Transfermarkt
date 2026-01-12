from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# --- POSTGRESQL BAĞLANTISI ---
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODEL ---
class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    club = db.Column(db.String(100))
    value = db.Column(db.Float, default=0.0)
    age = db.Column(db.String(10))
    country = db.Column(db.String(50))
    position = db.Column(db.String(50))
    img = db.Column(db.String(500))
    rumors = db.Column(db.Text)
    history = db.Column(db.Text, default="")

# --- KRİTİK NOKTA: OTOMATİK TABLO OLUŞTURUCU ---
# Siteye herhangi bir sayfa için istek geldiğinde tablolar yoksa oluşturur
@app.before_request
def create_tables():
    # Bu fonksiyon sadece bir kez çalışır ve tabloları oluşturur
    db.create_all()

# --- ROTALAR ---
@app.route('/')
def home():
    gelen_sifre = request.args.get('sifre')
    is_admin = (gelen_sifre == "futbol123")
    try:
        players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
    except:
        players = [] # Tablo henüz oluşmadıysa çökmesin
    return render_template('index.html', players=players, is_admin=is_admin, sifre=gelen_sifre)

@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    gelen_sifre = request.args.get('sifre')
    player = Oyuncu.query.get_or_404(player_id)
    lig_sira = Oyuncu.query.filter(Oyuncu.value > player.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.club == player.club, Oyuncu.value > player.value).count() + 1
    return render_template('detay.html', player=player, is_admin=(gelen_sifre == "futbol123"), 
                           sifre=gelen_sifre, lig_sira=lig_sira, takim_sira=takim_sira)

@app.route('/menu')
def menu():
    return render_template('menu.html', sifre=request.args.get('sifre'))

@app.route('/ekle', methods=['POST'])
def ekle():
    gelen_sifre = request.form.get('sifre')
    if gelen_sifre == "futbol123":
        v_raw = request.form.get('value', '0').replace(',', '.')
        yeni_oyuncu = Oyuncu(
            name=request.form.get('name'), club=request.form.get('club'),
            value=float(v_raw), age=request.form.get('age'),
            country=request.form.get('country'), position=request.form.get('position'),
            img=request.form.get('img', '').strip(), rumors=request.form.get('rumors', '')
        )
        db.session.add(yeni_oyuncu)
        db.session.commit()
    return redirect(url_for('home', sifre=gelen_sifre))

@app.route('/sil/<int:player_id>')
def sil(player_id):
    gelen_sifre = request.args.get('sifre')
    if gelen_sifre == "futbol123":
        p = Oyuncu.query.get(player_id)
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('home', sifre=gelen_sifre))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
