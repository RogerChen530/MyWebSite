from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 確保 static/uploads 目錄存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT NOT NULL UNIQUE,
                 password TEXT NOT NULL,
                 is_admin INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('index.html', current_time=current_time)

@app.route('/announcements')
def announcements():
    # 假設這裡有一些公告的數據
    announcements = ["公告1", "公告2", "公告3"]
    return render_template('announcement.html', announcements=announcements)

@app.route('/album', methods=['GET', 'POST'])
def album():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'photo' not in request.files:
            return redirect(request.url)
        
        photo = request.files['photo']
        if photo.filename == '':
            return redirect(request.url)
        
        if photo:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('album'))
    
    photos = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('album.html', photos=photos)

@app.route('/account')
def account():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('account.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = user[1]
            session['is_admin'] = bool(user[3])
            return redirect(url_for('index'))
        else:
            return "登入失敗，請檢查帳號和密碼"
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = 0
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, is_admin))
            conn.commit()
        except sqlite3.IntegrityError:
            return "註冊失敗，帳號已存在"
        conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
