from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Oyuncu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    club = db.Column(db.String(100))
    value = db.Column(db.Float, default=0.0)
    img = db.Column(db.String(500))

# Tabloları oluştur
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    sifre = request.args.get('sifre')
    players = Oyuncu.query.order_by(Oyuncu.value.desc()).all()
    return render_template('index.html', players=players, is_admin=(sifre == "futbol123"), sifre=sifre)

@app.route('/ekle', methods=['POST'])
def ekle():
    s = request.form.get('sifre')
    if s == "futbol123":
        val = request.form.get('value', '0').replace(',', '.')
        yeni = Oyuncu(name=request.form.get('name'), club=request.form.get('club'), value=float(val), img=request.form.get('img'))
        db.session.add(yeni)
        db.session.commit()
    return redirect(url_for('home', sifre=s))

@app.route('/menu')
def menu():
    return render_template('menu.html', sifre=request.args.get('sifre'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
