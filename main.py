from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# --- POSTGRESQL BAĞLANTISI ---
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELLER ---
class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    club = db.Column(db.String(100))
    value = db.Column(db.Float)
    age = db.Column(db.String(10))
    country = db.Column(db.String(50))
    position = db.Column(db.String(50))
    img = db.Column(db.String(500))
    rumors = db.Column(db.Text)
    history = db.Column(db.Text)
    value_history = db.Column(db.JSON, default=list)
    date_history = db.Column(db.JSON, default=list)

class Haber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200))
    icerik = db.Column(db.Text)

class Kulup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100))
    logo = db.Column(db.String(500))

# --- VERİTABANI OLUŞTURMA ---
with app.app_context():
    try:
        db.create_all()
        print("Veritabanı tabloları başarıyla oluşturuldu.")
    except Exception as e:
        print(f"Tablo oluşturma hatası: {e}")

# --- ROTALAR ---

@app.route('/tablo-kur')
def tablo_kur():
    try:
        # ÖNEMLİ: Tabloları birbirine bağlayan kilitleri zorla açıyoruz
        db.session.execute(db.text('DROP TABLE IF EXISTS oyuncu CASCADE;'))
        db.session.execute(db.text('DROP TABLE IF EXISTS haber CASCADE;'))
        db.session.execute(db.text('DROP TABLE IF EXISTS kulup CASCADE;'))
        db.session.commit()
        
        # Şimdi tertemiz ve yeni sütunlarla (club dahil) kuruyoruz
        db.create_all()
        return "Veritabanı zorla SIFIRLANDI ve club sütunu eklendi! Ana sayfaya dönebilirsin."
    except Exception as e:
        db.session.rollback()
        return f"Hata: {str(e)}"
        
        

@app.route('/')
def home():
    try:
        sifre = request.args.get('sifre')
        players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
        news = Haber.query.order_by(Haber.id.desc()).all()
        clubs = Kulup.query.all()
        return render_template('index.html', players=players, news=news, clubs=clubs, is_admin=(sifre == "futbol123"), sifre=sifre)
    except Exception as e:
        return f"Veritabanı hatası! Lütfen önce /tablo-kur adresine gidin. Detay: {str(e)}"

@app.route('/ekle', methods=['POST'])
def ekle():
    s = request.form.get('sifre')
    tip = request.form.get('tip', 'player')
    if s == "futbol123":
        if tip == 'player':
            v_raw = request.form.get('value', '0').replace(',', '.')
            try:
                v = float(v_raw)
            except:
                v = 0.0
            bugun = datetime.now().strftime("%d/%m")
            yeni = Oyuncu(
                name=request.form.get('name'), club=request.form.get('club'),
                value=v, age=request.form.get('age'), country=request.form.get('country'),
                position=request.form.get('position'), img=request.form.get('img'),
                rumors=request.form.get('rumors'), value_history=[v], date_history=[bugun]
            )
            db.session.add(yeni)
        elif tip == 'club':
            db.session.add(Kulup(ad=request.form.get('ad'), logo=request.form.get('logo')))
        elif tip == 'news':
            db.session.add(Haber(baslik=request.form.get('baslik'), icerik=request.form.get('icerik')))
        db.session.commit()
    return redirect(url_for('home', sifre=s))

@app.route('/ping')
def ping():
    return "Sistem Aktif", 200
    

@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    p = Oyuncu.query.get_or_404(player_id)
    s = request.args.get('sifre')
    lig_sira = Oyuncu.query.filter(Oyuncu.value > p.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.club == p.club, Oyuncu.value > p.value).count() + 1
    mevki_sira = Oyuncu.query.filter(Oyuncu.position == p.position, Oyuncu.value > p.value).count() + 1
    return render_template('detay.html', player=p, is_admin=(s == "futbol123"), sifre=s, lig_sira=lig_sira, Nightmare=takim_sira, mevki_sira=mevki_sira)

@app.route('/kulup/<string:kulup_adi>')
def kulup_sayfasi(kulup_adi):
    kadro = Oyuncu.query.filter_by(club=kulup_adi).all()
    toplam_deger = round(sum(p.value for p in kadro), 2)
    return render_template('kulup.html', kadro=kadro, kulup_adi=kulup_adi, toplam_deger=toplam_deger, sifre=request.args.get('sifre'))

@app.route('/sil/<int:player_id>')
def sil(player_id):
    s = request.args.get('sifre')
    if s == "futbol123":
        p = Oyuncu.query.get(player_id)
        if p:
            db.session.delete(p)
            db.session.commit()
    return redirect(url_for('home', sifre=s))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
