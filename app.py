from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = 'sdHava31wHdef1312_KHCx'  # 设置一个安全的密钥

# 数据库配置
db_config = {
    'host': 'localhost',
    'user': 'hhz',
    'password': 'Bigben077',
    'database': 'ops',
    'auth_plugin': 'mysql_native_password' 
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# 初始化数据库表
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def is_password_complex(password):
    """
    检查密码是否包含大小写字母和数字，且至少8位
    """
    return len(password) >= 8 and \
           re.search(r"\d", password) and \
           re.search(r"[A-Z]", password) and \
           re.search(r"[a-z]", password)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 检查用户名是否存在
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                flash('用户名已存在')
                return redirect(url_for('register'))
            
            if not is_password_complex(password):
                flash('密码必须包含大小写字母和数字，且至少8位')
                return redirect(url_for('register'))

            # # 哈希密码
            # hashed_password = generate_password_hash(password)
            
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                          (username, password))
            conn.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            else:
                flash('用户名或密码错误')
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)