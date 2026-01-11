from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy.dialects import postgresql
# Eğer hata devam ederse, koda şunu ekle:
import sqlalchemy
import sqlalchemy.dialects.postgresql

app = Flask(__name__)

# Veritabanı bağlantısı
# Eski 13. satırın yerine gelecek kısım:
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELLER ---
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
    yorumlar = db.relationship('Yorum', backref='oyuncu', lazy=True)

class Haber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200))
    icerik = db.Column(db.Text)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)

class Yorum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kullanici = db.Column(db.String(50))
    metin = db.Column(db.Text)
    oyuncu_id = db.Column(db.Integer, db.ForeignKey('oyuncu.id'))

# --- ROTARLAR ---
@app.route('/')
def index():
    sifre = request.args.get('sifre')
    is_admin = (sifre == "futbol123")
    players = Oyuncu.query.all()
    kulupler = Kulup.query.all()
    haberler = Haber.query.order_by(Haber.tarih.desc()).all()
    return render_template('index.html', players=players, kulupler=kulupler, haberler=haberler, is_admin=is_admin, sifre=sifre)

@app.route('/kulup_ekle', methods=['POST'])
def kulup_ekle():
    if request.form.get('sifre') == "futbol123":
        y_k = Kulup(isim=request.form['isim'], logo=request.form['logo'])
        db.session.add(y_k)
        db.session.commit()
    return redirect(url_for('index', sifre=request.form.get('sifre')))

@app.route('/haber_ekle', methods=['POST'])
def haber_ekle():
    if request.form.get('sifre') == "futbol123":
        y_h = Haber(baslik=request.form['baslik'], icerik=request.form['icerik'])
        db.session.add(y_h)
        db.session.commit()
    return redirect(url_for('index', sifre=request.form.get('sifre')))

@app.route('/ekle', methods=['POST'])
def ekle():
    if request.form.get('sifre') == "futbol123":
        try:
            val = float(request.form.get('value', 0).replace(',', '.'))
        except:
            val = 0.0
        y_o = Oyuncu(
            name=request.form['name'], 
            position=request.form['position'],
            value=val, 
            img=request.form['img'],
            rumors=request.form.get('rumors', ''),
            kulup_id=int(request.form['kulup_id'])
        )
        db.session.add(y_o)
        db.session.commit()
    return redirect(url_for('index', sifre=request.form.get('sifre')))

@app.route('/oyuncu/<int:id>')
def detay(id):
    sifre = request.args.get('sifre')
    p = Oyuncu.query.get_or_404(id)
    return render_template('detay.html', p=p, sifre=sifre)

@app.route('/yorum_yap/<int:id>', methods=['POST'])
def yorum_yap(id):
    y = Yorum(kullanici=request.form['kullanici'], metin=request.form['metin'], oyuncu_id=id)
    db.session.add(y)
    db.session.commit()
    return redirect(url_for('detay', id=id, sifre=request.form.get('sifre')))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
