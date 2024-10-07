from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management

# Configure upload folder
UPLOAD_FOLDER = '/home/ubuntu/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SQLite setup
conn = sqlite3.connect('/home/ubuntu/flaskapp/mydatabase.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username TEXT, password TEXT, firstname TEXT, lastname TEXT, email TEXT, filename TEXT)''')
conn.commit()
conn.close()

@app.route('/')
def index():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('/home/ubuntu/flaskapp/mydatabase.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        # Store the username in session
        session['username'] = username
        return redirect(url_for('profile', username=username))
    else:
        flash('Invalid username or password')
        return redirect(url_for('login_page'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']

    # Handle file upload
    file = request.files['filename']
    if file and file.filename != '':
        filename = secure_filename(file.filename)  # Secure the filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = None  # No file uploaded

    try:
        # Open a connection to the database with a timeout
        with sqlite3.connect('/home/ubuntu/flaskapp/mydatabase.db', timeout=10) as conn:
            c = conn.cursor()
            c.execute('PRAGMA journal_mode=WAL;')
            c.execute("INSERT INTO users (username, password, firstname, lastname, email, filename) VALUES (?, ?, ?, ?, ?, ?)",
                      (username, password, firstname, lastname, email, filename))
            conn.commit()
    except sqlite3.Error as e:
        # Handle the error (e.g., log it, return a message, etc.)
        print(f"An error occurred: {e}")
        return "An error occurred while registering. Please try again."
    
    return redirect(url_for('profile', username=username))  # Redirect to the profile page after registration

@app.route('/profile/<username>')
def profile(username):
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('/home/ubuntu/flaskapp/mydatabase.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    # Count the number of words in the uploaded file
    word_count = 0
    if user and user[6]:  # Check if a file was uploaded
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], user[6])
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                word_count = len(content.split())  # Split by whitespace to count words
        except FileNotFoundError:
            print(f"File not found: {file_path}")  # Log the error for debugging

    return render_template('profile.html', user=user, word_count=word_count)

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
