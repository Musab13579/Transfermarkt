from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- VERİTABANI AYARLARI ---
# Render'daki DATABASE_URL'i düzeltiyoruz (postgres:// -> postgresql://)
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- VERİ MODELLERİ ---
class Oyuncu(db.Model):
    __tablename__ = 'oyuncu'
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
    __tablename__ = 'haber'
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200))
    icerik = db.Column(db.Text)

class Kulup(db.Model):
    __tablename__ = 'kulup'
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100))
    logo = db.Column(db.String(500))

# --- KRİTİK: TABLOLARI OTOMATİK OLUŞTURMA ---
# Bu blok her başlangıçta tabloları kontrol eder ve eksikse oluşturur.
with app.app_context():
    try:
        db.create_all()
        print(">>> Veritabanı tabloları hazır.")
    except Exception as e:
        print(f">>> Tablo hatası: {e}")

# --- ROTALAR ---
@app.route('/')
def home():
    sifre = request.args.get('sifre')
    # Tablo hatası almamak için try-except içine aldık
    try:
        players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
        haberler = Haber.query.order_by(Haber.id.desc()).all()
        kulupler = Kulup.query.all()
    except:
        players, haberler, kulupler = [], [], []
    
    return render_template('index.html', players=players, haberler=haberler, kulupler=kulupler, is_admin=(sifre == "futbol123"), sifre=sifre)

@app.route('/menu')
def menu():
    return render_template('menu.html', sifre=request.args.get('sifre'))

@app.route('/ekle', methods=['POST'])
def ekle():
    sifre = request.form.get('sifre')
    if sifre == "futbol123":
        val = request.form.get('value', '0').replace(',', '.')
        yeni = Oyuncu(
            name=request.form.get('name'), club=request.form.get('club'),
            value=float(val) if val else 0.0, age=request.form.get('age'),
            country=request.form.get('country'), position=request.form.get('position'),
            img=request.form.get('img'), rumors=request.form.get('rumors')
        )
        db.session.add(yeni)
        db.session.commit()
    return redirect(url_for('home', sifre=sifre))

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

@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    p = Oyuncu.query.get_or_404(player_id)
    lig_sira = Oyuncu.query.filter(Oyuncu.value > p.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.club == p.club, Oyuncu.value > p.value).count() + 1
    return render_template('detay.html', player=p, sifre=request.args.get('sifre'), lig_sira=lig_sira, takim_sira=takim_sira)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
