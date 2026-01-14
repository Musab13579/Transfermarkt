from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# --- DATABASE BAĞLANTISI ---
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///futbol.db'
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
    yan_mevki = db.Column(db.String(50))
    img = db.Column(db.String(500))
    rumors = db.Column(db.Text)
    history = db.Column(db.Text)
    value_history = db.Column(db.JSON, default=list)
    date_history = db.Column(db.JSON, default=list)
    mac = db.Column(db.Integer, default=0)
    gol = db.Column(db.Integer, default=0)
    asist = db.Column(db.Integer, default=0)
    sure = db.Column(db.Integer, default=0)
    mevki_x = db.Column(db.Integer, default=50)
    mevki_y = db.Column(db.Integer, default=50)
    yan_mevki_x = db.Column(db.Integer, default=60)
    yan_mevki_y = db.Column(db.Integer, default=60)

class Haber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200))
    icerik = db.Column(db.Text)

class Kulup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100))
    logo = db.Column(db.String(500))

# --- TEMEL ROTALAR ---

@app.route('/')
def home():
    sifre = request.args.get('sifre')
    players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
    news = Haber.query.order_by(Haber.id.desc()).all()
    clubs = Kulup.query.all()
    return render_template('index.html', players=players, news=news, clubs=clubs, is_admin=(sifre == "futbol123"), sifre=sifre)

@app.route('/tablo-kur')
def tablo_kur():
    db.drop_all()
    db.create_all()
    return "Veritabanı ve tüm fonksiyonlar (Ekle/Sil/Güncelle) sıfırdan kuruldu!"

# --- EKLEME SİSTEMİ (Oyuncu, Kulüp, Haber) ---
@app.route('/ekle', methods=['POST'])
def ekle():
    s = request.form.get('sifre')
    if s != "futbol123": return redirect(url_for('home'))
    
    tip = request.form.get('tip')
    if tip == 'player':
        v = float(request.form.get('value', '0').replace(',', '.'))
        bugun = datetime.now().strftime("%d/%m")
        yeni = Oyuncu(
            name=request.form.get('name'), club=request.form.get('club'),
            value=v, country=request.form.get('nation'),
            position=request.form.get('position'), yan_mevki=request.form.get('sub_position'),
            img=request.form.get('img'), value_history=[v], date_history=[bugun]
        )
        db.session.add(yeni)
    elif tip == 'club':
        db.session.add(Kulup(ad=request.form.get('ad'), logo=request.form.get('logo')))
    elif tip == 'news':
        db.session.add(Haber(baslik=request.form.get('baslik'), icerik=request.form.get('icerik')))
    
    db.session.commit()
    return redirect(url_for('home', sifre=s))

# --- OYUNCU DETAY VE GÜNCELLEME ---
@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    p = Oyuncu.query.get_or_404(player_id)
    s = request.args.get('sifre')
    lig_sira = Oyuncu.query.filter(Oyuncu.value > p.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.club == p.club, Oyuncu.value > p.value).count() + 1
    mevki_sira = Oyuncu.query.filter(Oyuncu.position == p.position, Oyuncu.value > p.value).count() + 1
    return render_template('detay.html', player=p, is_admin=(s == "futbol123"), sifre=s, lig_sira=lig_sira, takim_sira=takim_sira, mevki_sira=mevki_sira)

@app.route('/oyuncu-guncelle/<int:id>', methods=['POST'])
def oyuncu_guncelle(id):
    s = request.form.get('sifre')
    if s == "futbol123":
        p = Oyuncu.query.get_or_404(id)
        # Transfer Log
        yeni_k = request.form.get('club')
        if p.club != yeni_k:
            log = f"{datetime.now().strftime('%d/%m/%y')}: {p.club} -> {yeni_k}"
            p.history = (log + "\n" + (p.history or ""))
            p.club = yeni_k
        # Veri Güncelleme
        p.name, p.country = request.form.get('name'), request.form.get('country')
        p.position, p.yan_mevki = request.form.get('position'), request.form.get('yan_mevki')
        # Değer & Grafik
        v = float(request.form.get('value').replace(',', '.'))
        if v != p.value:
            p.value = v
            vh, dh = list(p.value_history or []), list(p.date_history or [])
            vh.append(v); dh.append(datetime.now().strftime("%d/%m"))
            p.value_history, p.date_history = vh, dh
        # İstatistik & Koordinat
        p.mac, p.gol = int(request.form.get('mac') or 0), int(request.form.get('gol') or 0)
        p.asist, p.sure = int(request.form.get('asist') or 0), int(request.form.get('sure') or 0)
        p.mevki_x, p.mevki_y = int(request.form.get('mevki_x') or 50), int(request.form.get('mevki_y') or 50)
        p.yan_mevki_x, p.yan_mevki_y = int(request.form.get('yan_mevki_x') or 60), int(request.form.get('yan_mevki_y') or 60)
        p.rumors = request.form.get('rumors')
        db.session.commit()
    return redirect(url_for('oyuncu_detay', player_id=id, sifre=s))

# --- SİLME İŞLEMLERİ ---
@app.route('/oyuncu-sil/<int:id>')
def oyuncu_sil(id):
    s = request.args.get('sifre')
    if s == "futbol123":
        p = Oyuncu.query.get(id)
        if p: db.session.delete(p); db.session.commit()
    return redirect(url_for('home', sifre=s))

@app.route('/haber-sil/<int:id>')
def haber_sil(id):
    s = request.args.get('sifre')
    if s == "futbol123":
        h = Haber.query.get(id)
        if h: db.session.delete(h); db.session.commit()
    return redirect(url_for('home', sifre=s))

@app.route('/kulup-sil/<int:id>')
def kulup_sil(id):
    s = request.args.get('sifre')
    if s == "futbol123":
        k = Kulup.query.get(id)
        if k: db.session.delete(k); db.session.commit()
    return redirect(url_for('home', sifre=s))

# --- DÜZENLEME İŞLEMLERİ ---
@app.route('/haber-duzenle/<int:id>', methods=['POST'])
def haber_duzenle(id):
    s = request.form.get('sifre')
    if s == "futbol123":
        h = Haber.query.get_or_404(id)
        h.baslik, h.icerik = request.form.get('baslik'), request.form.get('icerik')
        db.session.commit()
    return redirect(url_for('home', sifre=s))

@app.route('/kulup/<string:kulup_adi>')
def kulup_sayfasi(kulup_adi):
    kadro = Oyuncu.query.filter_by(club=kulup_adi).order_by(Oyuncu.value.desc()).all()
    return render_template('kulup.html', players=kadro, club_name=kulup_adi, sifre=request.args.get('sifre'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
