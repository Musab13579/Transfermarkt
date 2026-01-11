from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
ADMIN_PASSWORD = "futbol123"

# --- RENDER POSTGRESQL BAĞLANTISI ---
# Senin verdiğin dahili URL buraya eklendi
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:3in2iaasDVhdIwkPl0fvbtEd21NfO9SS@dpg-d5hop175r7bs73bj9rdg-a/veritabani_zonx_97zd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- VERİTABANI MODELLERİ ---
class Kulup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(500))
    oyuncular = db.relationship('Oyuncu', backref='kulup_bilgisi', lazy=True)

class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    kulup_id = db.Column(db.Integer, db.ForeignKey('kulup.id'))
    value = db.Column(db.String(50))
    age = db.Column(db.String(10))
    country = db.Column(db.String(50))
    position = db.Column(db.String(50))
    img = db.Column(db.String(500))
    rumors = db.Column(db.Text)
    history = db.Column(db.Text)
    value_history = db.Column(db.JSON) # Grafik için liste tutar
    date_history = db.Column(db.JSON)  # Tarihleri tutar

# Tabloları oluştur
with app.app_context():
    db.create_all()

# --- YOLLAR (ROUTES) ---

@app.route('/')
def home():
    players = Oyuncu.query.all()
    kulupler = Kulup.query.all()
    gelen_sifre = request.args.get('sifre')
    is_admin = (gelen_sifre == ADMIN_PASSWORD)
    return render_template('index.html', players=players, kulupler=kulupler, is_admin=is_admin, sifre=gelen_sifre)

@app.route('/kulup_ekle', methods=['POST'])
def kulup_ekle():
    gelen_sifre = request.form.get('sifre')
    if gelen_sifre == ADMIN_PASSWORD:
        yeni = Kulup(isim=request.form.get('isim'), logo=request.form.get('logo'))
        db.session.add(yeni)
        db.session.commit()
    return redirect(url_for('home', sifre=gelen_sifre))

@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    player = Oyuncu.query.get(player_id)
    kulupler = Kulup.query.all()
    gelen_sifre = request.args.get('sifre')
    if player:
        return render_template('detay.html', player=player, kulupler=kulupler, is_admin=(gelen_sifre == ADMIN_PASSWORD), sifre=gelen_sifre)
    return "Oyuncu bulunamadı", 404

@app.route('/ekle', methods=['POST'])
def ekle():
    gelen_sifre = request.form.get('sifre')
    if gelen_sifre == ADMIN_PASSWORD:
        v_raw = request.form.get('value', '0').replace(',', '.')
        bugun = datetime.now().strftime("%d/%m")
        yeni_oyuncu = Oyuncu(
            name=request.form.get('name'),
            kulup_id=request.form.get('kulup_id'),
            value=v_raw, age=request.form.get('age'), country=request.form.get('country'),
            position=request.form.get('position'), img=request.form.get('img', '').strip(),
            rumors=request.form.get('rumors', ''), history="",
            value_history=[float(v_raw)], date_history=[bugun]
        )
        db.session.add(yeni_oyuncu)
        db.session.commit()
    return redirect(url_for('home', sifre=gelen_sifre))

@app.route('/guncelle/<int:player_id>', methods=['POST'])
def guncelle(player_id):
    player = Oyuncu.query.get(player_id)
    gelen_sifre = request.form.get('sifre')
    if player and gelen_sifre == ADMIN_PASSWORD:
        yeni_kulup_id = int(request.form.get('kulup_id'))
        if player.kulup_id != yeni_kulup_id:
            eski_k = player.kulup_bilgisi.isim if player.kulup_bilgisi else "Kulüpsüz"
            yeni_k = Kulup.query.get(yeni_kulup_id).isim
            tarih = datetime.now().strftime("%d/%m/%Y")
            player.history = f"{tarih}: {eski_k} ➔ {yeni_k}\n" + (player.history or "")
            player.kulup_id = yeni_kulup_id
        
        player.name = request.form.get('name')
        player.age = request.form.get('age')
        player.country = request.form.get('country')
        player.position = request.form.get('position')
        player.rumors = request.form.get('rumors')
        player.img = request.form.get('img').strip()
        
        yeni_val = request.form.get('value').replace(',', '.')
        try:
            v_float = float(yeni_val)
            if v_float != float(player.value):
                vh = list(player.value_history)
                dh = list(player.date_history)
                vh.append(v_float)
                dh.append(datetime.now().strftime("%d/%m"))
                player.value_history = vh
                player.date_history = dh
            player.value = yeni_val
        except: pass
        db.session.commit()
    return redirect(f'/oyuncu/{player_id}?sifre={gelen_sifre}')

@app.route('/sil/<int:player_id>')
def sil(player_id):
    gelen_sifre = request.args.get('sifre')
    if gelen_sifre == ADMIN_PASSWORD:
        p = Oyuncu.query.get(player_id)
        if p:
            db.session.delete(p)
            db.session.commit()
    return redirect(url_for('home', sifre=gelen_sifre))

@app.route('/ping')
def ping():
    return "Sistem Aktif", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
