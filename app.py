from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from config import db_config
from auth import register, login, dashboard, logout, home
from utils import get_db_connection, init_db, feature1, feature2, feature3

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'sdHava31wHdef1312_KHCx'  # 设置一个安全的密钥

# 注册路由
app.add_url_rule('/', '', home)
app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
app.add_url_rule('/dashboard', 'dashboard', dashboard)
app.add_url_rule('/logout', 'logout', logout)

# dashboard页面跳转
app.add_url_rule('/feature1', 'feature1', feature1)
app.add_url_rule('/feature2', 'feature2', feature2)
app.add_url_rule('/feature3', 'feature3', feature3)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)