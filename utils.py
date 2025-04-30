import mysql.connector
from flask import render_template
from mysql.connector import Error
import logging

# 数据库连接
def get_db_connection(host, user, password, database):
    try:
        connection = mysql.connector.connect(
            host = host,
            user = user,
            password = password,
            database = database,
        )
        return connection
    except Error as e:
        logging.error(f"Error connecting to MySQL: {str(e)}")
        return None

def init_db(host, user, password, database):
    """
    初始化数据库
    """
    conn = get_db_connection(host, user, password, database)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_locks (
            host VARCHAR(100) NOT NULL,
            database_name VARCHAR(100) NOT NULL,
            table_name VARCHAR(100) NOT NULL,
            pid VARCHAR(50) NOT NULL,
            primary key(host, database_name, table_name)
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def to_back_up():
    """
    跳转到功能1页面
    """
    return render_template('back_up.html')

def to_data_lineage():
    """
    跳转到功能2页面
    """
    return render_template('data_lineage.html')