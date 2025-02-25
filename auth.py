from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Flask
from werkzeug.security import generate_password_hash, check_password_hash
from utils import get_db_connection
import re

def is_password_complex(password):
    """
    检查密码是否包含大小写字母和数字，且至少8位
    """
    return len(password) >= 8 and \
           re.search(r"\d", password) and \
           re.search(r"[A-Z]", password) and \
           re.search(r"[a-z]", password)

def home():
    """
    主页"""
    return redirect(url_for('login'))

def register():
    """
    注册
    """
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

def login():
    """
    登录
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            
            # 后期这里可以考虑使用哈希验证
            if user and (user['password'] == password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            else:
                flash('用户名或密码错误')
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')

def dashboard():
    """
    仪表盘
    """
    if 'user_id' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

def logout():
    """
    登出
    """
    session.clear()
    return redirect(url_for('login'))