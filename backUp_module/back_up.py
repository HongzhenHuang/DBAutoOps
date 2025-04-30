import os
import sys
sys.path.append('/home/ldaphome/hhz/workspace/DBAutoOps/backUp_module')
import logging
import argparse
from subprocess import call, CalledProcessError
from datetime import datetime
from config import Config_lock, Config_users
from alert import send_alert
import mysql.connector
from mysql.connector import Error
import subprocess
from utils import get_db_connection
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Flask, jsonify

def is_pid_running(pid):
    """
    进程是否在运行    
    """
    try:
        result = subprocess.run(['ps', '-p', str(pid)], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        # 遍历每一行，跳过第一行（标题行）
        for line in lines[1:]:
            columns = line.split()
            if columns and columns[0] == str(pid):  # 检查第一列是否是目标PID
                return True
        return False
    except Exception as e:
        return False

def is_table_locked(host, database_name, table_name):
    """
    检查是否上锁，同时如果进程被kill了则进行更新
    传入参数是：主机名、数据库名、表名
    返回值是是否上锁
    """
    connection = get_db_connection(Config_lock.MYSQL_HOST,Config_lock.MYSQL_USER ,Config_lock.MYSQL_PASSWORD, Config_lock.MYSQL_DATABASE)
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(f"use {Config_lock.MYSQL_DATABASE}")
        query = """
        SELECT pid
        FROM backup_locks
        WHERE host = %s AND database_name = %s AND table_name = %s
        """
        cursor.execute(query, (host, database_name, table_name))
        result = cursor.fetchone()
        # 如果能找到这条记录证明被上锁了 因为锁表当中存的全都是上锁的表
        if result:
            pid = result
            # 判断 1是在被上锁处理 2还是被kill了 两种情况
            if not is_pid_running(pid):
                # PID 不存在 删除这条记录 把这条记录移出锁表
                cursor.execute("DELETE FROM backup_locks WHERE host = %s AND database_name = %s AND table_name = %s", (host, database_name, table_name,))
                connection.commit()
                logging.info(f"未找到 PID {pid}，已解锁表: {host}.{database_name}.{table_name}")
                return False
            else:
                logging.info(f"PID {pid} 仍在运行，表已被锁定: {host}.{database_name}.{table_name}")
                return True
        else:
            logging.info(f"未找到锁记录，表未被锁定: {host}.{database_name}.{table_name}")
            return False
    except Error as e:
        logging.error(f"检查或更新表锁时出错 {host}.{database_name}.{table_name}: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def set_backup_lock(host, database_name, table_name, is_locked):
    """
    上锁和解锁
    传入参数是：主机名 数据库名 表名 上锁还是解锁
    返回值是是否成功
    """
    connection = get_db_connection(Config_lock.MYSQL_HOST,Config_lock.MYSQL_USER ,Config_lock.MYSQL_PASSWORD, Config_lock.MYSQL_DATABASE )
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(f"use {Config_lock.MYSQL_DATABASE}")
        # 上锁
        if is_locked:
            # 上锁的时候写上进程号
            this_pid = os.getgid()
            # 插入或者更新记录
            cursor.execute("INSERT INTO backup_locks (host, database_name, table_name, pid) VALUES (%s, %s, %s, %s)", (host, database_name, table_name, this_pid))
        else:
            # 解锁的时候删除记录
            cursor.execute("DELETE FROM backup_locks WHERE host = %s AND database_name = %s AND table_name = %s", (host, database_name, table_name,))
        connection.commit()
        return True
    except Error as e:
        logging.error(f"设置备份锁时发生错误，表：{table_name}，错误信息：{str(e)}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_table_row_count(host, user, password, db_name, table_name):
    """
    获取表的记录数
    """
    connection = get_db_connection(host, user, password, db_name)
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {db_name}.{table_name}")
        row_count = cursor.fetchone()[0]
        return row_count
    except Error as e:
        logging.error(f"获取表记录数时发生错误，表：{table_name}，错误信息：{str(e)}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_backup_file_row_count(backup_file):
    """
    获取备份文件的记录数（备份文件中每行是一条记录）
    """
    try:
        with open(backup_file, 'r') as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0

def backup_table(host, user, password, db_name, table_name, mode, field, start, stop, rsync_target):
    """
    数据备份功能
    """
    i = 0
    # 检查是否有备份文件
    files_and_dirs = os.listdir('.')
    # 遍历所有文件和目录
    for item in files_and_dirs:
        if os.path.isfile(item) and '_complete.txt' in item and f'{host}.{db_name}.{table_name}' in item:
            # 使用 rsync 上传备份文件到远程服务器 (目标地址由参数传入)
            rsync_cmd = f'rsync -avz {item} {rsync_target}'
            call(rsync_cmd, shell=True)
            logging.info(f"表：{host}.{db_name}.{table_name}的备份已通过rsync上传")
            # 删除本地备份文件
            os.remove(item)
            logging.info(f"表：{host}.{db_name}.{table_name}的本地备份文件已删除")
            return '备份成功'
        elif os.path.isfile(item) and '.txt' in item and f'{host}.{db_name}.{table_name}' in item:
            backup_file = item
            i += 1

    if i == 0:
        backup_file = f'{host}.{db_name}.{table_name}_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.txt'

    # 检查是否已经上锁
    if is_table_locked(host, db_name, table_name):
        logging.error(f"表：{host}.{db_name}.{table_name}的备份已在进行中")
        return '备份正在进行中'

    # 设置锁
    if not set_backup_lock(host, db_name, table_name, True):
        logging.error(f"设置备份锁失败，表：{host}.{db_name}.{table_name}")
        return "设置备份锁失败"

    try:
        # 备份前检查记录的数量
        pre_backup_count = get_table_row_count(host, user, password, db_name, table_name)
        # 用 pt-archiver 工具进行备份，实现增量备份的功能
        if mode == 'save':
            cmd = (
                f"pt-archiver --source h={host},P={Config_lock.MYSQL_PORT},D={db_name},t={table_name},"
                f"u={user},p={password} --where \"{field} < '{stop}' AND {field} > '{start}'\" "
                f"--file {backup_file} --progress 10000 --limit=10000 --txn-size 10000 "
                f"--bulk-delete --no-delete --no-check-charset --statistics"
            )
        elif mode == 'delete':
            cmd = (
                f"pt-archiver --source h={host},P={Config_lock.MYSQL_PORT},D={db_name},t={table_name},"
                f"u={user},p={password} --where \"{field} < '{stop}' AND {field} > '{start}'\" "
                f"--file {backup_file} --progress 10000 --limit=10000 --txn-size 10000 "
                f"--bulk-delete --no-check-charset --statistics"
            )
        else:
            cmd = (
                f"pt-archiver --source h={host},P={Config_lock.MYSQL_PORT},D={db_name},t={table_name},"
                f"u={user},p={password} --where \"{field} < '{stop}' AND {field} > '{start}'\" "
                f"--file {backup_file} --progress 10000 --limit=10000 --txn-size 10000 "
                f"--bulk-delete --no-delete --no-check-charset --statistics"
            )
        call(cmd, shell=True)
        logging.info(f"表：{host}.{db_name}.{table_name}的备份已成功创建")

        # 备份后检查记录的数量
        post_backup_count = get_table_row_count(host, user, password, db_name, table_name)

        # 对于删除备份的情况，检查 pre_backup_count + 备份文件的记录数 == post_backup_count
        if mode == 'delete' and (post_backup_count + get_backup_file_row_count(backup_file)) != pre_backup_count:
            error_message = (f"备份后记录数不匹配，表：{host}.{db_name}.{table_name}，数据丢失")
            logging.error(error_message)
            return '备份失败'

        # 标记完整的备份文件
        complete_backup_file = backup_file.replace('.txt', '_complete.txt')
        os.rename(backup_file, complete_backup_file)

        # 使用 rsync 上传备份文件到远程服务器 (目标地址由参数传入)
        rsync_cmd = f'rsync -avz {complete_backup_file} {rsync_target}'
        call(rsync_cmd, shell=True)
        logging.info(f"表：{host}.{db_name}.{table_name}的备份已通过rsync上传")

        # 成功备份后删除本地备份文件
        if os.path.exists(complete_backup_file):
            os.remove(complete_backup_file)
            logging.info(f"表：{host}.{db_name}.{table_name}的本地备份文件已删除")

        return '备份成功'

    except CalledProcessError as e:
        error_message = (f"在备份过程中发生错误，表：{host}.{db_name}.{table_name}，错误信息：{str(e)}")
        logging.error(error_message)
        return '备份失败'

    except OSError as e:
        error_message = (f"操作系统错误，表：{host}.{db_name}.{table_name}，错误信息：{str(e)}")
        logging.error(error_message)
        return '备份失败'

    except Exception as e:
        error_message = (f"备份过程中发生意外错误，表：{host}.{db_name}.{table_name}，错误信息：{str(e)}")
        logging.error(error_message)
        return '备份失败'

    finally:
        # 清除备份锁标志
        if is_table_locked(host, db_name, table_name):
            set_backup_lock(host, db_name, table_name, False)

def backup_table_route():
    """
    备份表的路由函数
    """
    if request.form.get("backup") == "no":
        # 用户点击了“取消备份”，重定向回 back_up.html
        return render_template("back_up.html")

    host = request.form.get('host')
    user = Config_users.MYSQL_USER          # 若 user 在表单中未提交，则可以通过其它方式提供
    password = Config_users.MYSQL_PASSWORD  # 同上
    db_name = request.form.get('database')
    table_name = request.form.get('table')
    mode = request.form.get('mode', 'save')    # 提供默认值
    field = request.form.get('field')
    start = request.form.get('start')
    stop = request.form.get('stop')
    rsync_target = request.form.get('rsync_target')  # 远程服务器地址
    
    table_info = get_table_info(host, db_name, table_name)
    result = backup_table(host, user, password, db_name, table_name, mode, field, start, stop, rsync_target)

    # 检查必要参数是否为 None 并做相应的处理
    if None in (host, user, password, db_name, table_name, mode, field, start, stop):
        return render_template('back_up.html', table_info = table_info, result="请检查输入参数")
    
    return render_template('back_up.html', table_info = table_info, result=result)

def get_table_info(host, database, table):
    """
    根据传入的 host、database 和 table 查询表信息：
      - 记录数
      - 字段数
      - 表容量（单位 MB）
    注意：这里需要根据实际情况配置数据库连接参数（用户名、密码等）
    """
    try:
        conn = get_db_connection(host, Config_users.MYSQL_USER, Config_users.MYSQL_PASSWORD, database)
        cursor = conn.cursor()

        # 查询记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]

        # 查询字段数（描述表结构）
        cursor.execute(f"DESCRIBE {table}")
        fields = cursor.fetchall()
        field_count = len(fields)

        # 查询表容量（通过 information_schema.TABLES）
        cursor.execute(f"""
            SELECT ROUND(((data_length + index_length) / 1024 / 1024), 2)
            FROM information_schema.TABLES 
            WHERE table_schema = %s AND table_name = %s;
        """, (database, table))
        size_result = cursor.fetchone()
        size = f"{size_result[0]} MB" if size_result and size_result[0] is not None else "N/A"

        cursor.close()
        conn.close()
        return {
            'host': host,
            'database': database,
            'table': table,
            'row_count': row_count,
            'field_count': field_count,
            'size': size
        }
    except Exception as e:
        print("查询表信息时出错：", e)
        return None
    
def get_table_fields(host, database, table):
    """
    获取表的字段信息
    传入参数是：主机名、数据库名、表名
    返回值是字段列表
    """
    try:
        conn = get_db_connection(host, Config_users.MYSQL_USER, Config_users.MYSQL_PASSWORD, database)
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE `{table}`")
        result = cursor.fetchall()
        field_list = [row[0] for row in result]
        cursor.close()
        conn.close()
        
        return field_list
    except Exception as e:
        print(f"获取字段失败: {e}")
        return []

def query_table():
    """
    获取表信息
    传入参数是：主机名、数据库名、表名（前端传入）
    返回值是表信息（字典格式）
    """
    table_info = None
    if request.method == 'POST':

        host = request.form.get('host')
        database = request.form.get('database')
        table = request.form.get('table')

        table_info = get_table_info(host, database, table)

        if table_info:
            table_info['field'] = get_table_fields(host, database, table)

        if not table_info:
            flash("查询失败，请检查输入参数或数据库连接信息。")
        
    return render_template('back_up.html', table_info=table_info)
