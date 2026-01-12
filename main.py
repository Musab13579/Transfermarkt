from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- VERİTABANI BAĞLANTISI ---
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELLER ---
class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    club = db.Column(db.String(100))
    value = db.Column(db.Float, default=0.0) # En sorunsuz tip
    age = db.Column(db.String(10))
    country = db.Column(db.String(50))
    position = db.Column(db.String(50))
    img = db.Column(db.String(500))
    rumors = db.Column(db.Text)

class Haber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200))
    icerik = db.Column(db.Text)

class Kulup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100))
    logo = db.Column(db.String(500))

# --- TABLOLARI OLUŞTUR ---
with app.app_context():
    db.create_all()

# --- ANA SAYFA ---
@app.route('/')
def home():
    sifre = request.args.get('sifre')
    players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
    haberler = Haber.query.order_by(Haber.id.desc()).all()
    kulupler = Kulup.query.all()
    return render_template('index.html', players=players, haberler=haberler, kulupler=kulupler, is_admin=(sifre == "futbol123"), sifre=sifre)

# --- OYUNCU EKLE ---
@app.route('/ekle', methods=['POST'])
def ekle():
    sifre = request.form.get('sifre')
    if sifre == "futbol123":
        try:
            val = request.form.get('value', '0').replace(',', '.')
            yeni = Oyuncu(
                name=request.form.get('name'),
                club=request.form.get('club'),
                value=float(val) if val else 0.0,
                age=request.form.get('age'),
                country=request.form.get('country'),
                position=request.form.get('position'),
                img=request.form.get('img'),
                rumors=request.form.get('rumors')
            )
            db.session.add(yeni)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"Hata: {e}"
    return redirect(url_for('home', sifre=sifre))

# --- HABER & KULÜP EKLE ---
@app.route('/haber_ekle', methods=['POST'])
def haber_ekle():
    sifre = request.form.get('sifre')
    if sifre == "futbol123":
        yeni = Haber(baslik=request.form.get('baslik'), icerik=request.form.get('icerik'))
        db.session.add(yeni)
        db.session.commit()
    return redirect(url_for('menu', sifre=sifre))

@app.route('/kulup_ekle', methods=['POST'])
def kulup_ekle():
    sifre = request.form.get('sifre')
    if sifre == "futbol123":
        yeni = Kulup(ad=request.form.get('ad'), logo=request.form.get('logo'))
        db.session.add(yeni)
        db.session.commit()
    return redirect(url_for('menu', sifre=sifre))

# --- DİĞER ROTALAR ---
@app.route('/menu')
def menu():
    return render_template('menu.html', sifre=request.args.get('sifre'))

@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    p = Oyuncu.query.get_or_404(player_id)
    lig_sira = Oyuncu.query.filter(Oyuncu.value > p.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.club == p.club, Oyuncu.value > p.value).count() + 1
    return render_template('detay.html', player=p, sifre=request.args.get('sifre'), lig_sira=lig_sira, takim_sira=takim_sira)

@app.route('/sil/<int:player_id>')
def sil(player_id):
    s = request.args.get('sifre')
    if s == "futbol123":
        p = Oyuncu.query.get(player_id)
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('home', sifre=s))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
