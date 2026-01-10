from flask import Flask, render_template, request, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)
ADMIN_PASSWORD = "futbol123"
DATA_FILE = "oyuncular.json"

def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def veri_kaydet(p_list):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(p_list, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    players = veri_yukle()
    gelen_sifre = request.args.get('sifre')
    is_admin = (gelen_sifre == ADMIN_PASSWORD)
    return render_template('index.html', players=players, is_admin=is_admin, sifre=gelen_sifre)

@app.route('/oyuncu/<int:player_id>')
def oyuncu_detay(player_id):
    players = veri_yukle()
    gelen_sifre = request.args.get('sifre')
    player = next((p for p in players if p['id'] == player_id), None)
    if player:
        return render_template('detay.html', player=player, is_admin=(gelen_sifre == ADMIN_PASSWORD), sifre=gelen_sifre)
    return "Oyuncu bulunamadı", 404

@app.route('/ekle', methods=['POST'])
def ekle():
    players = veri_yukle()
    gelen_sifre = request.form.get('sifre')
    if gelen_sifre == ADMIN_PASSWORD:
        yeni_id = max([p['id'] for p in players], default=0) + 1
        v_raw = request.form.get('value', '0').replace(',', '.')
        bugun = datetime.now().strftime("%d/%m")
        yeni_oyuncu = {
            "id": yeni_id, "name": request.form.get('name'), "club": request.form.get('club'),
            "value": v_raw, "age": request.form.get('age'), "country": request.form.get('country'),
            "position": request.form.get('position'), "img": request.form.get('img', '').strip(),
            "rumors": request.form.get('rumors', ''), "history": "", "value_history": [float(v_raw)], "date_history": [bugun]
        }
        players.append(yeni_oyuncu)
        veri_kaydet(players)
    return redirect(f'/?sifre={gelen_sifre}')

@app.route('/guncelle/<int:player_id>', methods=['POST'])
def guncelle(player_id):
    players = veri_yukle()
    gelen_sifre = request.form.get('sifre')
    if gelen_sifre == ADMIN_PASSWORD:
        for p in players:
            if p['id'] == player_id:
                yeni_kulup = request.form.get('club')
                if yeni_kulup != p['club']:
                    tarih = datetime.now().strftime("%d/%m/%Y")
                    p['history'] = f"{tarih}: {p['club']} ➔ {yeni_kulup}\n" + p.get('history', '')
                p.update({
                    "name": request.form.get('name'), "club": yeni_kulup, "age": request.form.get('age'),
                    "country": request.form.get('country'), "position": request.form.get('position'),
                    "rumors": request.form.get('rumors'), "img": request.form.get('img').strip()
                })
                yeni_val = request.form.get('value').replace(',', '.')
                bugun = datetime.now().strftime("%d/%m")
                try:
                    v_float = float(yeni_val)
                    if v_float != float(p['value']):
                        p['value_history'].append(v_float)
                        p['date_history'].append(bugun)
                    p['value'] = yeni_val
                except: pass
                break
        veri_kaydet(players)
    return redirect(f'/oyuncu/{player_id}?sifre={gelen_sifre}')

@app.route('/sil/<int:player_id>')
def sil(player_id):
    players = veri_yukle()
    gelen_sifre = request.args.get('sifre')
    if gelen_sifre == ADMIN_PASSWORD:
        players = [p for p in players if p['id'] != player_id]
        veri_kaydet(players)
    return redirect(f'/?sifre={gelen_sifre}')

@app.route('/ping')
def ping():
    return "Sistem Aktif", 200

if __name__ == '__main__':
    # app.run satırı if'in tam altında bir TAB içerde olmalı
    app.run(host='0.0.0.0', port=8080)
    
