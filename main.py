from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import NUMERIC
from datetime import datetime
import os

app = Flask(__name__)

# VERİTABANI BAĞLANTISI
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# PostgreSQL Numeric Hatası Tamiri
def fix_numeric(value, dialect):
    return float(value) if value is not None else None
NUMERIC.result_processor = fix_numeric

# MODELLER (Tamamen eski usul db.Column, 3.13'te en garantisi budur)
class Kulup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(500))
    oyuncular = db.relationship('Oyuncu', backref='kulup', lazy=True)

class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50))
    value = db.Column(db.Float, default=0.0)
    img = db.Column(db.String(500))
    kulup_id = db.Column(db.Integer, db.ForeignKey('kulup.id'), nullable=False)

class Haber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200))
    icerik = db.Column(db.Text)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)

# ROTALAR
@app.route('/')
def index():
    sifre = request.args.get('sifre')
    is_admin = (sifre == "futbol123")
    players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
    return render_template('index.html', players=players, is_admin=is_admin, sifre=sifre)

@app.route('/menu')
def menu():
    return render_template('menu.html', sifre=request.args.get('sifre'))

@app.route('/oyuncu/<int:id>')
def detay(id):
    p = Oyuncu.query.get_or_404(id)
    # Sıralama mantığı
    lig_sira = Oyuncu.query.filter(Oyuncu.value > p.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.kulup_id == p.kulup_id, Oyuncu.value > p.value).count() + 1
    mevki_sira = Oyuncu.query.filter(Oyuncu.position == p.position, Oyuncu.value > p.value).count() + 1
    return render_template('detay.html', p=p, lig_sira=lig_sira, takim_sira=takim_sira, mevki_sira=mevki_sira, sifre=request.args.get('sifre'))

@app.route('/ekle_hersey', methods=['POST'])
def ekle_hersey():
    sifre = request.form.get('sifre')
    if sifre != "futbol123": return "Yetkisiz", 403
    tip = request.form.get('tip')
    if tip == "kulup":
        n = Kulup(isim=request.form['name'], logo=request.form['img'])
    elif tip == "oyuncu":
        n = Oyuncu(name=request.form['name'], position=request.form['position'], 
                   value=float(request.form['value']), img=request.form['img'],
                   kulup_id=int(request.form['kulup_id']))
    elif tip == "haber":
        n = Haber(baslik=request.form['name'], icerik=request.form['icerik'])
    db.session.add(n)
    db.session.commit()
    return redirect(url_for('index', sifre=sifre))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
