import os
import sqlite3
import datetime
import requests
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, g, jsonify, url_for, request, redirect, session

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'tv_panel.db'

# --- Config clima ---
OPENWEATHERMAP_API_KEY = "c605b1307153e4b5d3668abba5612025"
CIDADE = "Aparecida do Taboado"
ESTADO_CODIGO = "MS"
PAIS_CODIGO = "BR"
UNITS = "metric"
LANGUAGE = "pt_br"

# --- Upload ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ---------------------- API CLIMA ----------------------
@app.route('/api/weather')
def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CIDADE},{ESTADO_CODIGO},{PAIS_CODIGO}&appid={OPENWEATHERMAP_API_KEY}&units={UNITS}&lang={LANGUAGE}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        clima_info = {
            "temperatura": round(data['main']['temp']),
            "condicao": data['weather'][0]['description'].capitalize()
        }
        return jsonify(clima_info)
    except Exception as e:
        return jsonify({"temperatura": "N/A", "condicao": "Erro ao buscar clima"}), 500

# --------------------- DISPLAY PÁTIO -------------------------
@app.route('/display/patio')
def display_patio():
    db = get_db()
    patio_notices = db.execute("SELECT * FROM patio_notices ORDER BY id DESC").fetchall()
    feriados = db.execute("SELECT * FROM feriados WHERE data >= date('now') ORDER BY data LIMIT 3").fetchall()
    cardapio = db.execute("SELECT text_content, image_url FROM patio_menu WHERE id = 1").fetchone()
    cardapio_img = cardapio['image_url'] if cardapio and cardapio['image_url'] else ""
    return render_template(
        "display_patio.html",
        patio_notices=patio_notices,
        feriados=feriados,
        cardapio_texto=cardapio['text_content'] if cardapio else "",
        cardapio_img=cardapio_img
    )

# ---------------------- EDITAR CARDÁPIO (ATUALIZADO) --------------------------
@app.route('/admin/patio/menu', methods=['GET', 'POST'])
def admin_edit_patio_menu():
    db = get_db()
    error = None
    if request.method == 'POST':
        text_content = request.form.get('text_content', '')
        image_url = None

        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = f"{int(datetime.datetime.now().timestamp())}_{secure_filename(file.filename)}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    image_url = f"uploads/{filename}"
                else:
                    error = "Formato de imagem não suportado."
                    menu = db.execute("SELECT * FROM patio_menu WHERE id = 1").fetchone()
                    return render_template('admin_edit_patio_menu.html', menu=menu, error=error)
            else:
                menu = db.execute("SELECT image_url FROM patio_menu WHERE id = 1").fetchone()
                image_url = menu['image_url'] if menu else ''
        else:
            menu = db.execute("SELECT image_url FROM patio_menu WHERE id = 1").fetchone()
            image_url = menu['image_url'] if menu else ''

        db.execute("UPDATE patio_menu SET text_content = ?, image_url = ? WHERE id = 1", (text_content, image_url))
        db.commit()
        return redirect(url_for('admin_edit_patio_menu'))

    menu = db.execute("SELECT * FROM patio_menu WHERE id = 1").fetchone()
    if not menu:
        db.execute("INSERT INTO patio_menu (id, text_content, image_url) VALUES (1, '', '')")
        db.commit()
        menu = db.execute("SELECT * FROM patio_menu WHERE id = 1").fetchone()
    return render_template('admin_edit_patio_menu.html', menu=menu, error=error)

# --------------------- INTERVALO / FERIADOS / AVISOS PÁTIO -------------------
@app.route('/admin/interval_schedules', methods=['GET', 'POST'])
def admin_interval_schedules():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        is_enabled = 1 if request.form.get('is_enabled') == 'on' else 0
        db.execute("INSERT INTO interval_schedules (name, start_time, end_time, is_enabled) VALUES (?, ?, ?, ?)",
                   (name, start_time, end_time, is_enabled))
        db.commit()
    schedules = db.execute("SELECT * FROM interval_schedules ORDER BY start_time").fetchall()
    return render_template('admin_interval_schedules.html', schedules=schedules)

@app.route('/api/interval/status')
def interval_status():
    db = get_db()
    now = datetime.datetime.now()
    now_time = now.strftime("%H:%M")
    row = db.execute("""
        SELECT * FROM interval_schedules 
        WHERE is_enabled = 1
          AND start_time <= ?
          AND end_time   >= ?
        ORDER BY start_time
        LIMIT 1
    """, (now_time, now_time)).fetchone()

    if row:
        start = datetime.datetime.strptime(row['start_time'], "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        end = datetime.datetime.strptime(row['end_time'], "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        duration = int((end - start).total_seconds())
        remaining = int((end - now).total_seconds())
        return jsonify({
            "active": True,
            "duration": duration,
            "remaining": max(0, remaining),
            "end_time": row['end_time']
        })
    return jsonify({"active": False})

@app.route('/admin/interval_schedules/delete/<int:schedule_id>', methods=['POST'])
def admin_delete_interval(schedule_id):
    db = get_db()
    db.execute("DELETE FROM interval_schedules WHERE id=?", (schedule_id,))
    db.commit()
    return redirect(url_for('admin_interval_schedules'))

@app.route('/admin/patio/notices', methods=['GET', 'POST'])
def admin_edit_patio_notices():
    db = get_db()
    if request.method == 'POST':
        delete_id = request.form.get('delete_id')
        if delete_id:
            db.execute("DELETE FROM patio_notices WHERE id = ?", (delete_id,))
            db.commit()
        else:
            text_content = request.form.get('text_content')
            if text_content:
                db.execute("INSERT INTO patio_notices (content) VALUES (?)", (text_content,))
                db.commit()
        return redirect(url_for('admin_edit_patio_notices'))
    avisos = db.execute("SELECT * FROM patio_notices ORDER BY id DESC").fetchall()
    return render_template('admin_edit_patio_notices.html', avisos=avisos)

@app.route('/admin/patio/notices/delete/<int:notice_id>', methods=['POST'])
def admin_delete_patio_notice(notice_id):
    db = get_db()
    db.execute("DELETE FROM patio_notices WHERE id = ?", (notice_id,))
    db.commit()
    return redirect(url_for('admin_edit_patio_notices'))

# ------------------- USUÁRIOS ------------------------------
@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    success_message = error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error_message = "Preencha usuário e senha."
        elif db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            error_message = "Usuário já existe."
        else:
            db.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), 0)
            )
            db.commit()
            success_message = "Usuário cadastrado com sucesso!"
    users = db.execute("SELECT * FROM users ORDER BY username").fetchall()
    return render_template(
        'admin_users.html',
        users=users,
        success_message=success_message,
        error_message=error_message
    )

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return redirect(url_for('admin_users'))

# ------------------- LOGIN / DASHBOARD ------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = user['username']
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Usuário ou senha inválidos")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# ------------------- MODELOS ------------------------------
@app.route('/admin/models', methods=['GET', 'POST'])
def admin_models():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == "POST":
        name = request.form.get('name')
        if name:
            db.execute("INSERT INTO models (name) VALUES (?)", (name,))
            db.commit()
        return redirect(url_for('admin_models')) 
    models = db.execute("SELECT * FROM models ORDER BY name").fetchall()
    return render_template('admin_models.html', models=models)

@app.route('/admin/models/<int:model_id>/delete', methods=['POST'])
def admin_delete_model(model_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute("DELETE FROM models WHERE id = ?", (model_id,))
    db.execute("DELETE FROM model_images WHERE model_id = ?", (model_id,))
    db.execute("DELETE FROM model_notices WHERE model_id = ?", (model_id,))
    db.commit()
    return redirect(url_for('admin_models'))

# ------------------- MODELOS: NOTICES ------------------------------
@app.route('/admin/models/<int:model_id>/notices', methods=['GET', 'POST'])
def admin_model_notices(model_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    model = db.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
    if not model:
        return redirect(url_for('admin_models'))

    error = None
    if request.method == "POST":
        content = request.form.get('content')
        if content:
            db.execute("INSERT INTO model_notices (model_id, content) VALUES (?, ?)", (model_id, content))
            db.commit()
        else:
            error = "Conteúdo não pode ser vazio."
    notices = db.execute("SELECT * FROM model_notices WHERE model_id = ?", (model_id,)).fetchall()
    return render_template('admin_model_notices.html', model=model, notices=notices, error=error)

@app.route('/admin/models/<int:model_id>/notices/<int:notice_id>/delete', methods=['POST'])
def admin_delete_model_notice(model_id, notice_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute("DELETE FROM model_notices WHERE id = ? AND model_id = ?", (notice_id, model_id))
    db.commit()
    return redirect(url_for('admin_model_notices', model_id=model_id))

# ------------------- MODELOS: IMAGES ------------------------------
@app.route('/admin/models/<int:model_id>/images', methods=['GET', 'POST'])
def admin_model_images(model_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    model = db.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
    if not model:
        return redirect(url_for('admin_models'))

    error = None
    if request.method == "POST":
        if 'image_file' not in request.files or not request.files['image_file'].filename:
            error = "Selecione um arquivo de imagem."
        else:
            file = request.files['image_file']
            if allowed_file(file.filename):
                filename = f"{int(datetime.datetime.now().timestamp())}_{secure_filename(file.filename)}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                image_url = f"uploads/{filename}"
                start_date = request.form.get('start_date')
                end_date = request.form.get('end_date')
                db.execute("INSERT INTO model_images (model_id, image_url, start_date, end_date) VALUES (?, ?, ?, ?)",
                           (model_id, image_url, start_date, end_date))
                db.commit()
            else:
                error = "Formato de imagem não suportado."
    images = db.execute("SELECT * FROM model_images WHERE model_id = ?", (model_id,)).fetchall()
    return render_template('admin_model_images.html', model=model, images=images, error=error)

@app.route('/admin/models/<int:model_id>/images/<int:image_id>/delete', methods=['POST'])
def admin_delete_model_image(model_id, image_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute("DELETE FROM model_images WHERE id = ? AND model_id = ?", (image_id, model_id))
    db.commit()
    return redirect(url_for('admin_model_images', model_id=model_id))

# ------------------- DEVICES ------------------------------
@app.route('/admin/devices', methods=['GET', 'POST'])
def admin_devices():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    error = None

    if request.method == 'POST':
        name = request.form.get('name')
        screen_type = request.form.get('screen_type')
        location_notes = request.form.get('location_notes')
        model_id = request.form.get('model_id') if screen_type == 'modelo' else None

        if not name or not screen_type:
            error = "Preencha todos os campos obrigatórios."
        elif screen_type == 'modelo' and not model_id:
            error = "Selecione um modelo para telas personalizadas."
        else:
            if screen_type == 'patio':
                model_id = 0
            db.execute(
                "INSERT INTO devices (name, model_id, screen_type, location_notes) VALUES (?, ?, ?, ?)",
                (name, model_id, screen_type, location_notes)
            )
            db.commit()
            return redirect(url_for('admin_devices'))

    models = db.execute("SELECT * FROM models").fetchall()
    devices = db.execute("""
        SELECT d.*, m.name as model_name FROM devices d
        LEFT JOIN models m ON d.model_id = m.id
        ORDER BY d.name
    """).fetchall()
    return render_template('admin_devices.html', devices=devices, models=models, error=error)

@app.route('/admin/devices/delete/<int:device_id>', methods=['POST'])
def admin_delete_device(device_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    db.commit()
    return redirect(url_for('admin_devices'))

@app.route('/display/<int:device_id>')
def display(device_id):
    db = get_db()
    device = db.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    if not device:
        return "Dispositivo não encontrado", 404

    # Exemplo: se for personalizado, pega o modelo e mostra na tela certa
    if device['screen_type'] == 'modelo' and device['model_id']:
        model = db.execute("SELECT * FROM models WHERE id = ?", (device['model_id'],)).fetchone()
        notices = db.execute("SELECT * FROM model_notices WHERE model_id = ?", (device['model_id'],)).fetchall()
        images = db.execute("SELECT * FROM model_images WHERE model_id = ?", (device['model_id'],)).fetchall()
        global_announcement = db.execute("SELECT * FROM global_announcements WHERE id = 1").fetchone()
        return render_template(
            "display_model.html",
            model=model,
            notices=notices,
            images=images,
            global_announcement=global_announcement
        )
    elif device['screen_type'] == 'patio':
        return redirect(url_for('display_patio'))
    else:
        return "Tipo de tela não suportado.", 400


# ------------------- GLOBAL ANNOUNCEMENT ------------------------------
@app.route('/admin/global_announcement', methods=['GET', 'POST'])
def admin_global_announcement():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == 'POST':
        message = request.form.get('message')
        is_active = int(bool(request.form.get('is_active')))
        db.execute("UPDATE global_announcements SET message = ?, is_active = ? WHERE id = 1", (message, is_active))
        db.commit()
        return redirect(url_for('admin_global_announcement'))
    row = db.execute("SELECT message, is_active FROM global_announcements WHERE id = 1").fetchone()
    return render_template('admin_global_announcement.html', announcement=row)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
