from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

ADMIN_PASSWORD = "futbol123"

# --- BURAYI GÜNCELLE ---
# Render'daki 'Internal Database URL' bilgisini aşağıdaki tırnakların içine yapıştır.
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:Isg8m2Vxg9XOUtFUBAJZTzwFGjWUc6ak@dpg-d5hlatp5pdvs73bhojn0-a/veritabani_zonx'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- VERİTABANI TABLOSU (ESKİ JSON YAPISIYLA AYNI) ---
class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    club = db.Column(db.String(100))
    value = db.Column(db.String(50))
    age = db.Column(db.String(10))
    country = db.Column(db.String(50))
    position = db.Column(db.String(50))
    img = db.Column(db.String(300))
    rumors = db.Column(db.Text)
    history = db.Column(db.Text)
    value_history = db.Column(db.JSON) # Liste olarak saklar
    date_history = db.Column(db.JSON)  # Liste olarak saklar

# Veritabanını oluştur
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    players = Oyuncu.query.all()
    gelen_sifre = request.args.get('sifre')
    is_admin = (gelen_sifre == ADMIN_PASSWORD)
    return render_template('index.html', players=players, is_admin=is_admin, sifre=gelen_sifre)

@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    player = Oyuncu.query.get(player_id)
    gelen_sifre = request.args.get('sifre')
    if player:
        return render_template('detay.html', player=player, is_admin=(gelen_sifre == ADMIN_PASSWORD), sifre=gelen_sifre)
    return "Oyuncu bulunamadı", 404

@app.route('/ekle', methods=['POST'])
def ekle():
    gelen_sifre = request.form.get('sifre')
    if gelen_sifre == ADMIN_PASSWORD:
        v_raw = request.form.get('value', '0').replace(',', '.')
        bugun = datetime.now().strftime("%d/%m")
        
        yeni_oyuncu = Oyuncu(
            name=request.form.get('name'),
            club=request.form.get('club'),
            value=v_raw,
            age=request.form.get('age'),
            country=request.form.get('country'),
            position=request.form.get('position'),
            img=request.form.get('img', '').strip(),
            rumors=request.form.get('rumors', ''),
            history="",
            value_history=[float(v_raw)],
            date_history=[bugun]
        )
        db.session.add(yeni_oyuncu)
        db.session.commit()
    return redirect(url_for('home', sifre=gelen_sifre))

@app.route('/guncelle/<int:player_id>', methods=['POST'])
def guncelle(player_id):
    player = Oyuncu.query.get(player_id)
    gelen_sifre = request.form.get('sifre')
    if player and gelen_sifre == ADMIN_PASSWORD:
        yeni_kulup = request.form.get('club')
        if yeni_kulup != player.club:
            tarih = datetime.now().strftime("%d/%m/%Y")
            player.history = f"{tarih}: {player.club} ➔ {yeni_kulup}\n" + (player.history or "")
        
        player.name = request.form.get('name')
        player.club = yeni_kulup
        player.age = request.form.get('age')
        player.country = request.form.get('country')
        player.position = request.form.get('position')
        player.rumors = request.form.get('rumors')
        player.img = request.form.get('img').strip()
        
        yeni_val = request.form.get('value').replace(',', '.')
        bugun = datetime.now().strftime("%d/%m")
        try:
            v_float = float(yeni_val)
            if v_float != float(player.value):
                # JSON listelerini güncellemek için kopyalayıp tekrar atıyoruz
                vh = list(player.value_history)
                dh = list(player.date_history)
                vh.append(v_float)
                dh.append(bugun)
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
        player = Oyuncu.query.get(player_id)
        if player:
            db.session.delete(player)
            db.session.commit()
    return redirect(url_for('home', sifre=gelen_sifre))

@app.route('/ping')
def ping():
    return "Sistem Aktif", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
        
