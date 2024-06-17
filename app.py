from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps
from datetime import datetime
import os  # 確保導入了os模塊

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('show_time'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or not session.get('is_admin'):
            return redirect(url_for('show_time'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return render_template('index.html', current_time=current_time)
    else:
        return redirect(url_for('show_time'))

@app.route('/show_time')
def show_time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('show_time.html', current_time=current_time)

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
            session['username'] = user[1]
            session['is_admin'] = user[3]
            return redirect(url_for('index'))
        else:
            flash('無效的用戶名或密碼')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('show_time'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = False
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
        content = request.form['content']
        if 'add' in request.form:
            c.execute("INSERT INTO announcements (content) VALUES (?)", (content,))
        elif 'delete' in request.form:
            announcement_id = request.form['announcement_id']
            c.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))

        conn.commit()

    c.execute("SELECT * FROM announcements")
    announcements = c.fetchall()
    conn.close()

    return render_template('announcements.html', announcements=announcements)

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

if __name__ == '__main__':
    app.run(debug=True)
