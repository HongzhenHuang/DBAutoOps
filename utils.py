import mysql.connector
from config import db_config
from flask import render_template

def get_db_connection():
    """
    获取数据库连接
    """
    conn = mysql.connector.connect(**db_config)
    return conn

def init_db():
    """
    初始化数据库
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def feature1():
    return render_template('feature1.html')

def feature2():
    return render_template('feature2.html')

def feature3():
    return render_template('feature3.html')