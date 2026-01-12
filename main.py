from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- VERİTABANI ---
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
    value = db.Column(db.Float, default=0.0)
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

with app.app_context():
    db.create_all()

# --- ROTALAR ---
@app.route('/')
def home():
    sifre = request.args.get('sifre')
    players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
    haberler = Haber.query.order_by(Haber.id.desc()).all()
    kulupler = Kulup.query.all()
    
    # Mevkilere göre en pahalı oyuncuları bulma (En İyi 11 Mantığı)
    mevkiler = ["Kaleci", "Stoper", "Sol Bek", "Sağ Bek", "Defansif Orta Saha", "Merkez Orta Saha", "On Numara", "Sol Kanat", "Sağ Kanat", "Santrafor"]
    en_iyiler = {}
    for m in mevkiler:
        en_iyiler[m] = Oyuncu.query.filter_by(position=m).order_by(Oyuncu.value.desc()).first()

    return render_template('index.html', players=players, haberler=haberler, kulupler=kulupler, en_iyiler=en_iyiler, is_admin=(sifre == "futbol123"), sifre=sifre)

@app.route('/ekle', methods=['POST'])
def ekle():
    s = request.form.get('sifre')
    if s == "futbol123":
        v = request.form.get('value', '0').replace(',', '.')
        yeni = Oyuncu(
            name=request.form.get('name'), club=request.form.get('club'),
            value=float(v) if v else 0.0, age=request.form.get('age'),
            country=request.form.get('country'), position=request.form.get('position'),
            img=request.form.get('img'), rumors=request.form.get('rumors')
        )
        db.session.add(yeni)
        db.session.commit()
    return redirect(url_for('home', sifre=s))

@app.route('/kulup/<string:kulup_adi>')
def kulup_detay(kulup_adi):
    s = request.args.get('sifre')
    kadro = Oyuncu.query.filter_by(club=kulup_adi).all()
    toplam_deger = sum(p.value for p in kadro)
    return render_template('kulup.html', kadro=kadro, kulup_adi=kulup_adi, toplam_deger=toplam_deger, sifre=s)

@app.route('/yonetim', methods=['POST'])
def yonetim():
    s = request.form.get('sifre')
    tip = request.form.get('tip')
    if s == "futbol123":
        if tip == "haber":
            db.session.add(Haber(baslik=request.form.get('baslik'), icerik=request.form.get('icerik')))
        elif tip == "kulup":
            db.session.add(Kulup(ad=request.form.get('ad'), logo=request.form.get('logo')))
        db.session.commit()
    return redirect(url_for('home', sifre=s))

@app.route('/oyuncu/<int:player_id>')
def detay(player_id):
    p = Oyuncu.query.get_or_404(player_id)
    return render_template('detay.html', player=p, sifre=request.args.get('sifre'))

@app.route('/menu')
def menu():
    return render_template('menu.html', sifre=request.args.get('sifre'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
