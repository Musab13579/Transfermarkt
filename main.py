from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy import event, func
from sqlalchemy.dialects.postgresql import NUMERIC

app = Flask(__name__)

# Veritabanı Bağlantısı
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

# MODELLER
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
    rumors = db.Column(db.String(500))
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
    sifre = request.args.get('sifre')
    return render_template('menu.html', sifre=sifre)

@app.route('/haberler')
def haberler():
    sifre = request.args.get('sifre')
    all_haberler = Haber.query.order_by(Haber.tarih.desc()).all()
    return render_template('haberler.html', haberler=all_haberler, sifre=sifre)

@app.route('/kulupler')
def kulupler():
    sifre = request.args.get('sifre')
    all_kulupler = Kulup.query.all()
    return render_template('kulupler.html', kulupler=all_kulupler, sifre=sifre)

@app.route('/kulup/<int:id>')
def kulup_detay(id):
    sifre = request.args.get('sifre')
    k = Kulup.query.get_or_404(id)
    toplam_deger = sum(p.value for p in k.oyuncular)
    return render_template('kulup_detay.html', k=k, toplam_deger=toplam_deger, sifre=sifre)

@app.route('/en-iyiler')
def en_iyiler():
    sifre = request.args.get('sifre')
    # Mevkilere göre en yüksek değerli oyuncular
    best_players = Oyuncu.query.order_by(Oyuncu.position, Oyuncu.value.desc()).all()
    return render_template('en_iyiler.html', players=best_players, sifre=sifre)

@app.route('/oyuncu/<int:id>')
def detay(id):
    sifre = request.args.get('sifre')
    p = Oyuncu.query.get_or_404(id)
    
    # Sıralama Hesaplamaları
    lig_sira = Oyuncu.query.filter(Oyuncu.value > p.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.kulup_id == p.kulup_id, Oyuncu.value > p.value).count() + 1
    mevki_sira = Oyuncu.query.filter(Oyuncu.position == p.position, Oyuncu.value > p.value).count() + 1
    
    return render_template('detay.html', p=p, lig_sira=lig_sira, takim_sira=takim_sira, mevki_sira=mevki_sira, sifre=sifre)

# ADMIN EKLEME ROTALARI
@app.route('/ekle_hersey', methods=['POST'])
def ekle_hersey():
    sifre = request.form.get('sifre')
    if sifre != "futbol123": return "Yetkisiz", 403
    
    tip = request.form.get('tip')
    if tip == "kulup":
        y = Kulup(isim=request.form['isim'], logo=request.form['logo'])
    elif tip == "oyuncu":
        y = Oyuncu(name=request.form['name'], position=request.form['position'], 
                   value=float(request.form['value']), img=request.form['img'],
                   rumors=request.form.get('rumors',''), kulup_id=int(request.form['kulup_id']))
    elif tip == "haber":
        y = Haber(baslik=request.form['baslik'], icerik=request.form['icerik'])
    
    db.session.add(y)
    db.session.commit()
    return redirect(url_for('index', sifre=sifre))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
