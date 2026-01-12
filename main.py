from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey, Numeric
from datetime import datetime
import os

# Yeni nesil SQLAlchemy 2.0 başlatma (3.13 uyumlu)
class Base(DeclarativeBase):
    pass

app = Flask(__name__)

# Veritabanı Ayarı
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# MODELLER
class Kulup(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    isim: Mapped[str] = mapped_column(String(100))
    logo: Mapped[str] = mapped_column(String(500), nullable=True)
    oyuncular = relationship("Oyuncu", back_populates="kulup")

class Oyuncu(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(50))
    # Burası kritik: Numeric hatasını engellemek için Float kullanıyoruz
    value: Mapped[float] = mapped_column(Float, default=0.0)
    img: Mapped[str] = mapped_column(String(500), nullable=True)
    rumors: Mapped[str] = mapped_column(String(500), nullable=True)
    kulup_id: Mapped[int] = mapped_column(ForeignKey("kulup.id"))
    kulup = relationship("Kulup", back_populates="oyuncular")

class Haber(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    baslik: Mapped[str] = mapped_column(String(200))
    icerik: Mapped[str] = mapped_column(Text)
    tarih: Mapped[datetime] = mapped_column(default=datetime.utcnow)

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
    sifre = request.args.get('sifre')
    p = Oyuncu.query.get_or_404(id)
    # Sıralamalar
    lig_sira = Oyuncu.query.filter(Oyuncu.value > p.value).count() + 1
    takim_sira = Oyuncu.query.filter(Oyuncu.kulup_id == p.kulup_id, Oyuncu.value > p.value).count() + 1
    mevki_sira = Oyuncu.query.filter(Oyuncu.position == p.position, Oyuncu.value > p.value).count() + 1
    return render_template('detay.html', p=p, lig_sira=lig_sira, takim_sira=takim_sira, mevki_sira=mevki_sira, sifre=sifre)

@app.route('/haberler')
def haberler():
    h_list = Haber.query.order_by(Haber.tarih.desc()).all()
    return render_template('haberler.html', haberler=h_list, sifre=request.args.get('sifre'))

@app.route('/kulupler')
def kulupler():
    k_list = Kulup.query.all()
    return render_template('kulupler.html', kulupler=k_list, sifre=request.args.get('sifre'))

@app.route('/en-iyiler')
def en_iyiler():
    best = Oyuncu.query.order_by(Oyuncu.position, Oyuncu.value.desc()).all()
    return render_template('en_iyiler.html', players=best, sifre=request.args.get('sifre'))

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
    app.run(debug=True)
