import flask
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, g
from flask_cors import CORS
import requests 
import os
from werkzeug.utils import secure_filename 
import datetime
import time
import sqlite3 
import json

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)

DATABASE = 'tv_panel.db'
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads') 

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER) 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

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

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('CREATE TABLE IF NOT EXISTS patio_notices (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS patio_menu (id INTEGER PRIMARY KEY CHECK (id = 1), text_content TEXT, image_url TEXT)')
        cursor.execute("INSERT OR IGNORE INTO patio_menu (id, text_content, image_url) VALUES (1, ?, ?)", ("Cardápio padrão.", "uploads/placeholder_prato.jpg"))
        cursor.execute('CREATE TABLE IF NOT EXISTS global_announcements (id INTEGER PRIMARY KEY CHECK (id = 1), message TEXT, is_active BOOLEAN DEFAULT 0)')
        cursor.execute("INSERT OR IGNORE INTO global_announcements (id, message, is_active) VALUES (1, '', 0)")
        cursor.execute('CREATE TABLE IF NOT EXISTS devices (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, screen_type TEXT NOT NULL, location_notes TEXT)')
        cursor.execute("CREATE TABLE IF NOT EXISTS interval_schedule (id INTEGER PRIMARY KEY CHECK (id = 1), start_time TEXT DEFAULT '10:00', end_time TEXT DEFAULT '10:15', is_enabled BOOLEAN DEFAULT 1)")
        cursor.execute("INSERT OR IGNORE INTO interval_schedule (id, start_time, end_time, is_enabled) VALUES (1, '10:00', '10:15', 1)")
        cursor.execute('CREATE TABLE IF NOT EXISTS secretaria_notices (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, display_order INTEGER DEFAULT 0)')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT, image_url TEXT NOT NULL, target_screen_type TEXT NOT NULL,
                start_date TEXT NOT NULL, end_date TEXT NOT NULL, display_order INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_screens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                layout_config_json TEXT
            )
        ''')
        
        db.commit()

with app.app_context():
    init_db()

OPENWEATHERMAP_API_KEY = "c605b1307153e4b5d3668abba5612025" 
CIDADE = "Aparecida do Taboado"
ESTADO_CODIGO = "MS"
PAIS_CODIGO = "BR"
UNITS = "metric" 
LANGUAGE = "pt_br"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_combined_notices(specific_notices_query):
    db = get_db()
    cursor = db.cursor()
    global_cursor = cursor.execute("SELECT message, is_active FROM global_announcements WHERE id = 1")
    global_announcement = global_cursor.fetchone()
    
    combined_notices = []
    if global_announcement and global_announcement['is_active'] and global_announcement['message']:
        combined_notices.append(f"AVISO GERAL::{global_announcement['message']}")
    
    specific_cursor = cursor.execute(specific_notices_query)
    specific_notices = [row['content'] for row in specific_cursor.fetchall()]
    combined_notices.extend(specific_notices)
    return combined_notices

@app.route('/api/patio/notices', methods=['GET']) 
def get_patio_notices():
    query = "SELECT content FROM patio_notices ORDER BY id"
    notices = get_combined_notices(query)
    return jsonify(notices)

@app.route('/api/secretaria/notices', methods=['GET'])
def get_secretaria_notices():
    query = "SELECT content FROM secretaria_notices ORDER BY display_order, id"
    notices = get_combined_notices(query)
    return jsonify(notices)

@app.route('/api/scheduled_images/<string:screen_type>', methods=['GET'])
def get_scheduled_images(screen_type):
    db = get_db()
    today = datetime.date.today().strftime('%Y-%m-%d')
    cursor = db.execute(
        "SELECT image_url FROM scheduled_images WHERE target_screen_type = ? AND start_date <= ? AND end_date >= ? ORDER BY display_order",
        (screen_type, today, today)
    )
    images = [url_for('static', filename=row['image_url']) for row in cursor.fetchall()]
    return jsonify(images)

@app.route('/api/patio/menu', methods=['GET']) 
def get_patio_menu():
    db = get_db()
    cursor = db.execute("SELECT text_content, image_url FROM patio_menu WHERE id = 1")
    menu_row = cursor.fetchone()
    if menu_row:
        data_to_send = {"texto": menu_row["text_content"], "imagemUrl": menu_row["image_url"]}
        if data_to_send.get('imagemUrl') and data_to_send['imagemUrl'].startswith('uploads/'):
            data_to_send['imagemUrl'] = url_for('static', filename=data_to_send['imagemUrl'])
        return jsonify(data_to_send)
    return jsonify({"texto": "Cardápio não disponível."}), 404

@app.route('/api/weather', methods=['GET'])
def get_weather():
    if not OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_API_KEY == "SUA_CHAVE_API_AQUI_DO_OPENWEATHERMAP":
        return jsonify({ "temperatura": "N/A", "condicao": "API Key não configurada"}), 500
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CIDADE},{ESTADO_CODIGO},{PAIS_CODIGO}&appid={OPENWEATHERMAP_API_KEY}&units={UNITS}&lang={LANGUAGE}"
        response = requests.get(url, timeout=10) 
        response.raise_for_status()  
        data = response.json()
        clima_info = { "temperatura": round(data['main']['temp']), "condicao": data['weather'][0]['description'].capitalize() }
        return jsonify(clima_info)
    except Exception as e:
        return jsonify({"temperatura": "N/A", "condicao": "Erro ao buscar clima"}), 500

@app.route('/api/interval/status', methods=['GET'])
def get_interval_status():
    db = get_db()
    schedule = db.execute("SELECT start_time, end_time, is_enabled FROM interval_schedule WHERE id = 1").fetchone()
    if not schedule or not schedule['is_enabled']:
        return jsonify({"active": False, "message": "Desabilitado"})
    now_dt = datetime.datetime.now()
    today_str = now_dt.strftime("%Y-%m-%d")
    try:
        start_dt_local = datetime.datetime.strptime(f"{today_str} {schedule['start_time']}", "%Y-%m-%d %H:%M")
        end_dt_local = datetime.datetime.strptime(f"{today_str} {schedule['end_time']}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"active": False, "message": "Hora inválida"}), 500
    is_active_now = start_dt_local <= now_dt < end_dt_local
    if is_active_now:
        start_timestamp_utc = start_dt_local.timestamp()
        duration_seconds = (end_dt_local - start_dt_local).total_seconds()
        return jsonify({"active": True, "duration_seconds": int(duration_seconds), "start_timestamp_utc": start_timestamp_utc})
    elif now_dt >= end_dt_local:
         return jsonify({"active": False, "message": "Intervalo Concluído"})
    else:
        return jsonify({"active": False, "message": "Fora do horário"})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == "admin" and request.form.get('password') == "admin":
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Usuário ou senha inválidos")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/edit/patio/notices', methods=['GET', 'POST'])
def admin_edit_patio_notices():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == 'POST':
        db.execute("DELETE FROM patio_notices")
        i = 0
        while True:
            aviso_content = request.form.get(f'notice{i}')
            if aviso_content is None: break
            if aviso_content.strip():
                db.execute("INSERT INTO patio_notices (content) VALUES (?)", (aviso_content.strip(),))
            i += 1
        db.commit()
        return redirect(url_for('admin_dashboard'))
    cursor = db.execute("SELECT content FROM patio_notices ORDER BY id")
    current_notices = [row['content'] for row in cursor.fetchall()]
    return render_template('admin_edit_patio_noticia.html', notices=current_notices)

@app.route('/admin/edit/patio/menu', methods=['GET', 'POST'])
def admin_edit_patio_menu():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == 'POST':
        text_content = request.form.get('menu_text')
        menu_row_for_old_image = db.execute("SELECT image_url FROM patio_menu WHERE id = 1").fetchone()
        image_url_current = menu_row_for_old_image['image_url'] if menu_row_for_old_image else None
        new_image_url = image_url_current 
        if 'menu_image_file' in request.files:
            file = request.files['menu_image_file']
            if file and file.filename and allowed_file(file.filename):
                if image_url_current and image_url_current.startswith('uploads/'):
                    old_filepath = os.path.join(app.static_folder, image_url_current)
                    if os.path.exists(old_filepath):
                        try: os.remove(old_filepath)
                        except OSError as e: print(f"Erro ao remover {old_filepath}: {e}")
                filename = f"{int(time.time())}_{secure_filename(file.filename)}"
                new_filepath_absolute = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(new_filepath_absolute)
                    new_image_url = f'uploads/{filename}'
                except Exception as e: print(f"ERRO ao salvar {new_filepath_absolute}: {e}")
        db.execute("UPDATE patio_menu SET text_content = ?, image_url = ? WHERE id = 1", (text_content, new_image_url))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    menu_row = db.execute("SELECT text_content, image_url FROM patio_menu WHERE id = 1").fetchone()
    return render_template('admin_edit_patio_menu.html', menu=dict(menu_row))

@app.route('/admin/global_announcement', methods=['GET', 'POST'])
def admin_global_announcement():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == 'POST':
        message = request.form.get('message')
        is_active = 'is_active' in request.form 
        db.execute("UPDATE global_announcements SET message = ?, is_active = ? WHERE id = 1", (message, is_active))
        db.commit()
        return redirect(url_for('admin_global_announcement')) 
    announcement_row = db.execute("SELECT message, is_active FROM global_announcements WHERE id = 1").fetchone()
    return render_template('admin_global_aviso.html', announcement=dict(announcement_row))

@app.route('/admin/images/<string:screen_type>', methods=['GET'])
def admin_list_images(screen_type):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    images = db.execute("SELECT * FROM scheduled_images WHERE target_screen_type = ? ORDER BY start_date DESC", (screen_type,)).fetchall()
    return render_template('admin_list_images.html', images=images, screen_type=screen_type)

@app.route('/admin/images/add/<string:screen_type>', methods=['GET', 'POST'])
def admin_add_image(screen_type):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        file = request.files.get('image_file')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if not all([file, file.filename, start_date, end_date]):
            return render_template('admin_add_image.html', error="Todos os campos são obrigatórios.", screen_type=screen_type)
        if allowed_file(file.filename):
            filename = f"{int(time.time())}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            db = get_db()
            db.execute("INSERT INTO scheduled_images (image_url, target_screen_type, start_date, end_date) VALUES (?, ?, ?, ?)",
                       (f"uploads/{filename}", screen_type, start_date, end_date))
            db.commit()
            return redirect(url_for('admin_list_images', screen_type=screen_type))
    return render_template('admin_add_image.html', screen_type=screen_type)

@app.route('/admin/images/delete/<int:image_id>', methods=['POST'])
def admin_delete_image(image_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    image_row = db.execute("SELECT image_url, target_screen_type FROM scheduled_images WHERE id = ?", (image_id,)).fetchone()
    if image_row:
        screen_type = image_row['target_screen_type']
        filepath = os.path.join(app.static_folder, image_row['image_url'])
        if os.path.exists(filepath):
            try: os.remove(filepath)
            except OSError as e: print(f"Erro ao remover arquivo físico: {e}")
        db.execute("DELETE FROM scheduled_images WHERE id = ?", (image_id,))
        db.commit()
        return redirect(url_for('admin_list_images', screen_type=screen_type))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/devices', methods=['GET'])
def admin_list_devices():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    cursor = db.execute("SELECT id, name, screen_type, location_notes FROM devices ORDER BY name")
    devices = [dict(row) for row in cursor.fetchall()]
    return render_template('admin_lista_dispositivo.html', devices=devices)

@app.route('/admin/devices/add', methods=['GET', 'POST'])
def admin_add_device():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        screen_type = request.form.get('screen_type')
        location_notes = request.form.get('location_notes')
        if name and screen_type:
            try:
                db.execute("INSERT INTO devices (name, screen_type, location_notes) VALUES (?, ?, ?)",
                           (name, screen_type, location_notes))
                db.commit()
                return redirect(url_for('admin_list_devices'))
            except sqlite3.IntegrityError:
                custom_screens = db.execute("SELECT id, name FROM custom_screens ORDER BY name").fetchall()
                return render_template('admin_add_dispositivo.html', error="Um dispositivo com este nome já existe.", custom_screens=custom_screens)
    
    custom_screens = db.execute("SELECT id, name FROM custom_screens ORDER BY name").fetchall()
    return render_template('admin_add_dispositivo.html', custom_screens=custom_screens)

@app.route('/admin/devices/delete/<int:device_id>', methods=['POST'])
def admin_delete_device(device_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    db.commit()
    return redirect(url_for('admin_list_devices'))

@app.route('/admin/interval/schedule', methods=['GET', 'POST'])
def admin_edit_interval_schedule():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == 'POST':
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        is_enabled = 'is_enabled' in request.form
        try:
            datetime.datetime.strptime(start_time, '%H:%M')
            datetime.datetime.strptime(end_time, '%H:%M')
        except ValueError:
            schedule = db.execute("SELECT start_time, end_time, is_enabled FROM interval_schedule WHERE id = 1").fetchone()
            return render_template('admin_edit_interval_schedule.html', schedule=dict(schedule), error="Formato inválido. Use HH:MM.")
        db.execute("UPDATE interval_schedule SET start_time = ?, end_time = ?, is_enabled = ? WHERE id = 1", (start_time, end_time, is_enabled))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    schedule = db.execute("SELECT start_time, end_time, is_enabled FROM interval_schedule WHERE id = 1").fetchone()
    return render_template('admin_edit_interval_schedule.html', schedule=dict(schedule))

@app.route('/admin/custom_screens', methods=['GET'])
def admin_list_custom_screens():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    screens = db.execute("SELECT id, name FROM custom_screens ORDER BY name").fetchall()
    return render_template('admin_list_custom_screens.html', screens=screens)

@app.route('/admin/custom_screens/add', methods=['GET', 'POST'])
def admin_add_custom_screen():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            db = get_db()
            try:
                cursor = db.execute("INSERT INTO custom_screens (name, layout_config_json) VALUES (?, ?)", (name, '{}'))
                db.commit()
                new_screen_id = cursor.lastrowid
                return redirect(url_for('admin_edit_custom_screen', screen_id=new_screen_id))
            except sqlite3.IntegrityError:
                return render_template('admin_add_custom_screen.html', error="Uma tela com este nome já existe.")
    return render_template('admin_add_custom_screen.html')

@app.route('/admin/custom_screens/edit/<int:screen_id>', methods=['GET', 'POST'])
def admin_edit_custom_screen(screen_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    if request.method == 'POST':
        layout_template = request.form.get('layout_template')
        config = {'template': layout_template}
        if layout_template == 'coluna_unica':
            config['main_content'] = request.form.get('main_content_1')
        elif layout_template == 'duas_colunas':
            config['main_content'] = request.form.get('main_content_2')
            config['sidebar_content'] = request.form.get('sidebar_content_2')
        layout_config_json = json.dumps(config)
        db.execute("UPDATE custom_screens SET layout_config_json = ? WHERE id = ?", (layout_config_json, screen_id))
        db.commit()
        return redirect(url_for('admin_list_custom_screens'))
            
    screen_row = db.execute("SELECT * FROM custom_screens WHERE id = ?", (screen_id,)).fetchone()
    if not screen_row: return "Tela não encontrada", 404
    screen = dict(screen_row)
    try:
        layout_config = json.loads(screen.get('layout_config_json', '{}'))
    except (json.JSONDecodeError, TypeError):
        layout_config = {}
        
    return render_template('admin_edit_custom_screen.html', screen=screen, layout_config=layout_config)

@app.route('/admin/custom_screens/delete/<int:screen_id>', methods=['POST'])
def admin_delete_custom_screen(screen_id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute("DELETE FROM custom_screens WHERE id = ?", (screen_id,))
    db.commit()
    return redirect(url_for('admin_list_custom_screens'))

@app.route('/display/<string:screen_type>')
def display_screen(screen_type):
    if screen_type == 'patio':
        return render_template('display_patio.html')
    elif screen_type == 'secretaria':
        return render_template('secretaria_display.html')
    elif screen_type.startswith('custom_'):
        screen_id = screen_type.split('_')[1]
        db = get_db()
        screen = db.execute("SELECT * FROM custom_screens WHERE id = ?", (screen_id,)).fetchone()
        if not screen:
            return "Tela personalizada não encontrada", 404
        try:
            layout_config = json.loads(screen['layout_config_json'])
        except (json.JSONDecodeError, TypeError):
            layout_config = {}
        return render_template('display_custom.html', screen=screen, layout_config=layout_config)
    else:
        return render_template('image_display.html', screen_type=screen_type)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
