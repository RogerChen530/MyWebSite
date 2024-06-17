from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('show_time'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def show_time():
    return render_template('show_time.html')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

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
            session['is_admin'] = user[3] == 1
            return redirect(url_for('index'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('show_time'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, is_admin))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/announcements', methods=['GET', 'POST'])
@login_required
def announcements():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST' and session.get('is_admin'):
        if 'add' in request.form:
            title = request.form.get('title')
            content = request.form.get('content')
            if title and content:
                c.execute("INSERT INTO announcements (title, content) VALUES (?, ?)", (title, content))
                conn.commit()
        elif 'delete' in request.form:
            announcement_id = request.form.get('announcement_id')
            if announcement_id:
                c.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
                conn.commit()

    c.execute("SELECT id, title FROM announcements")
    announcements = c.fetchall()

    if 'view_content' in request.args:
        announcement_id = request.args.get('view_content')
        c.execute("SELECT content FROM announcements WHERE id = ?", (announcement_id,))
        content = c.fetchone()[0]
    else:
        content = None

    conn.close()

    return render_template('announcements.html', announcements=announcements, content=content)

@app.route('/album', methods=['GET', 'POST'])
@login_required
def album():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '':
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                c.execute("INSERT INTO photos (filename) VALUES (?)", (filename,))
        elif 'delete' in request.form:
            photo_id = request.form['photo_id']
            c.execute("SELECT filename FROM photos WHERE id = ?", (photo_id,))
            filename = c.fetchone()[0]
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            c.execute("DELETE FROM photos WHERE id = ?", (photo_id,))

        conn.commit()

    c.execute("SELECT * FROM photos")
    photos = c.fetchall()
    conn.close()

    return render_template('album.html', photos=photos)

@app.route('/account', methods=['GET', 'POST'])
@login_required
@admin_required
def account():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        user_id = request.form['user_id']
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'

        if 'update' in request.form:
            c.execute("UPDATE users SET username = ?, password = ?, is_admin = ? WHERE id = ?", 
                      (username, password, is_admin, user_id))
        elif 'delete' in request.form:
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()

    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    return render_template('account.html', users=users)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    app.run(debug=True)
