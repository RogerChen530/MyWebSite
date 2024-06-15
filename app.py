import os
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        is_admin BOOLEAN
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY,
        filepath TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY,
        title TEXT,
        content TEXT
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('show_time'))
    return render_template('index.html')

@app.route('/show_time')
def show_time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"<h1>Welcome!</h1><p>Current time: {current_time}</p><a href='/login'>Login</a> <a href='/register'>Register</a>"

@app.route('/account')
def account():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('index'))
    return render_template('account.html')

@app.route('/album')
def album():
    if not session.get('logged_in'):
        return redirect(url_for('show_time'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT filepath FROM photos')
    photos = c.fetchall()
    conn.close()
    return render_template('album.html', photos=photos)

@app.route('/announcements')
def announcements():
    if not session.get('logged_in'):
        return redirect(url_for('show_time'))
    return render_template('announcements.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin', 'off') == 'on'
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, is_admin))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['logged_in'] = True
            session['username'] = user[1]
            session['is_admin'] = user[3]
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('show_time'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_photo():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO photos (filepath) VALUES (?)", (filepath,))
            conn.commit()
            conn.close()
            return redirect(url_for('album'))
    return render_template('upload.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
