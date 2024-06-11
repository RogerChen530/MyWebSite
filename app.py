import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY, filepath TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (id INTEGER PRIMARY KEY, title TEXT, content TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/album')
def album():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT filepath FROM photos')
    photos = c.fetchall()
    conn.close()
    return render_template('album.html', photos=photos)

@app.route('/announcements')
def announcements():
    return render_template('announcements.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    # Implement login logic
    pass

@app.route('/update', methods=['POST'])
def update_account():
    old_username = request.form['old_username']
    new_username = request.form['new_username']
    new_password = request.form['new_password']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET username = ?, password = ? WHERE username = ?", (new_username, new_password, old_username))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_account():
    username = request.form['username']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_photo():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO photos (filepath) VALUES (?)", (filepath,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('album'))
    return redirect(request.url)

@app.route('/add_announcement', methods=['POST'])
def add_announcement():
    title = request.form['title']
    content = request.form['content']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO announcements (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Additional routes for update_photo, delete_photo, update_announcement, delete_announcement

if __name__ == '__main__':
    init_db()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
