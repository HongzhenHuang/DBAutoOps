import logging
import os.path
import mysql.connector
from config import Config_DLM
from mysql.connector import Error
import re
import importlib.util

def split(s):
    """
    以不在括号内的.进行分割 得到库名和表名
    """
    result = []
    current_part = []
    inside_braces = 0

    for char in s:
        if char == '{':
            inside_braces += 1
        elif char == '}':
            inside_braces -= 1

        if char == '.' and inside_braces == 0:
            result.append(''.join(current_part))
            current_part = []
        else:
            current_part.append(char)

    # 添加最后一部分
    if current_part:
        result.append(''.join(current_part))

    return result

def write_to_db(url, results , branch, subdir):
    """
    写入数据库
    """
    try:
        # 连接到 MySQL 数据库
        connection = mysql.connector.connect(
            host=Config_DLM.host,  # 数据库主机
            user=Config_DLM.user,  # 数据库用户名
            password=Config_DLM.password,  # 数据库密码
            database=Config_DLM.database,  # 数据库名称
            port=Config_DLM.port  # 数据库端口号
        )
        if connection.is_connected():
            cursor = connection.cursor()
            # 插入 SQL 语句
            insert_query = """
            INSERT IGNORE INTO data_flow_new (url, script, source_instance, source_db, source_table, target_instance, target_db, target_table)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            # [[[脚本1，源表若干，目标表], [脚本1，源表若干, 目标表]，……], [[脚本2，源表若干，目标表]]]
            for result in results:
                for item in result:
                    # 获取脚本名
                    script_name = item[0].split('/')[-1]
                    script = f"/blob/{branch}/{subdir}/{script_name}"
                    # 获取源表若干
                    source = item[1:-1]
                    # 获取目标表
                    target = item[-1:]
                    for target_tables in target:
                        target_db,target_table = target_tables.split('.')
                        for source_tables in source:
                            source_db,source_table = source_tables.split('.')

                            # 准备插入的数据
                            data = (
                                url,# git地址
                                script,# 文件路径
                                "<default>",
                                source_db,
                                source_table,
                                "<default>",
                                target_db,
                                target_table
                            )
                            # 执行插入操作
                            cursor.execute(insert_query, data)
                            connection.commit()

            logging.info("Data written to database successfully")
            # 关闭数据库连接
            if connection.is_connected():
                cursor.close()
                connection.close()
    # 捕获异常
    except Error as e:
        logging.error(f"Error: {e}")

def write_to_db_with_config(url, results , branch, subdir):
    """
    写入数据库
    """
    try:
        # 连接到 MySQL 数据库
        connection = mysql.connector.connect(
            host=Config_DLM.host,  # 数据库主机
            user=Config_DLM.user,  # 数据库用户名
            password=Config_DLM.password,  # 数据库密码
            database=Config_DLM.database,  # 数据库名称
            port=Config_DLM.port  # 数据库端口号
        )
        if connection.is_connected():
            cursor = connection.cursor()
            # 插入 SQL 语句
            insert_query = """
            INSERT IGNORE INTO data_flow_new (url, script, source_instance, source_db, source_table, target_instance, target_db, target_table)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            delete_query = """
            DELETE FROM data_flow_new WHERE url = %s AND script = %s 
            """
            #[[[脚本1，配置信息名，源表若干，目标表],[脚本1，配置信息名，源表若干,目标表]，……],[[脚本2，配置信息名，源表若干，目标表]]]


            # result都是同一个脚本的
            for result in results:
                # 用于跟踪每个脚本是否已经执行过删除操作
                script_deleted = set()

                for item in result:
                    # 获取脚本名
                    script_name = item[0].split('/')[-1]
                    script = f"/blob/{branch}/{subdir}/{script_name}"

                    # 如果该脚本还没有删除过，则执行删除操作
                    if f"{url}.{script}" not in script_deleted:
                        cursor.execute(delete_query, (url,script,))
                        connection.commit()  # 提交删除操作
                        script_deleted.add(f"{url}.{script}")  # 记录此脚本已经删除过

                    # 获取配置信息名
                    config = item[1]
                    # 获取源表若干
                    source = item[2:-1]
                    # 获取目标表
                    target = item[-1:]
                    for target_tables in target:
                        # 分割得到库名和表名
                        target_db,target_table = split(target_tables)
                        for source_tables in source:
                            # 分割得到库名和表名
                            source_db,source_table = split(source_tables)
                            # 默认host为<default>
                            host = '<default>'
                            config_info = search_host_db(item[0], config)
                            # 假设host是一定有的
                            if config_info:
                                host = config_info['host']
                            # 获取配置文件路径
                            if source_db == '<default>' and config_info:
                                source_db = config_info['database'] if config_info['database'] != '' else '<default>'
                            if target_db == '<default>' and config_info:
                                target_db = config_info['database'] if config_info['database'] != '' else '<default>'
                            # 准备插入的数据
                            data = (
                                url,# git地址
                                script,# 文件路径
                                host,# "<default>", # host
                                source_db, # "<default>", # source_db
                                source_table,
                                host, # "<default>", # host
                                target_db, # "<default>", #target_db
                                target_table
                            )
                            # 执行插入操作
                            cursor.execute(insert_query, data)
                            connection.commit()

            logging.info("Data written to database successfully")
            # 关闭数据库连接
            if connection.is_connected():
                cursor.close()
                connection.close()
    # 捕获异常
    except Error as e:
        logging.error(f"Error: {e}")

def search_host_db(file, name):
    """
    根据脚本文件名和配置信息名查找配置信息
    args:
        file: 脚本文件名
        name: 配置信息名
    return:
        {'host': IP_ADDRESS9, 'database': booking_system}
    """
    def read_file(filepath, encodings=['utf-8', 'latin1']):
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        logging.warning(f"Failed to read file: {filepath} with given encodings.")
        return None

    # 确保文件存在
    if not os.path.exists(file):
        logging.warning(f"File {file} does not exist.")
        return None

    # 读取并解析文件
    file_content = read_file(file)
    if not file_content:
        logging.warning(f"Unable to read content from file: {file}")
        return None

    # 对于python文件而言
    if os.path.splitext(file)[1] == '.py':
        # 提取配置信息的正则表达式
        config_pattern = re.compile(
            rf'class\s+\w+\s*\(.*object.*\):.*?self\.{name}\s*=\s*DBApi\((.*?)\)',
            re.DOTALL
        )

        match = config_pattern.search(file_content)
        if match:
            config_info = match.group(1).strip().strip("'").strip('"')
        else:
            logging.warning(f"Configuration for {name} not found in {file}")
            return None

        # 获取文件夹名
        dir_name = os.path.dirname(file)
        all_config_paths = []

        for i in Config_DLM.config_fn:
            # 添加可能的配置文件路径
            config_path = os.path.join(dir_name, i)
            # 以后见一个添加一个 因为不一定是config.py
            all_config_paths.append(config_path)

        # 遍历所有配置路径，直到找到目标配置类
        for config_path in all_config_paths:
            if os.path.exists(config_path):
                try:
                    # 动态导入 "config"参数没作用 是为动态导入的模块指定的名称
                    spec = importlib.util.spec_from_file_location("config", config_path)
                    config_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config_module)

                    # 获取配置类
                    if hasattr(config_module, config_info):
                        config_class = getattr(config_module, config_info)

                        # 如果是类，检查其属性
                        if isinstance(config_class, type):
                            if hasattr(config_class, 'host') and hasattr(config_class, 'database'):
                                host = getattr(config_class, 'host')
                                database = getattr(config_class, 'database')
                                return {'host': host, 'database': database}
                            else:
                                logging.warning(
                                    f"Class {config_info} in {config_path} does not have 'host' or 'database' attributes.")
                                return None

                        # 如果是字典，直接获取相应的配置
                        elif isinstance(config_class, dict):
                            if 'host' in config_class and 'database' in config_class:
                                return {
                                    'host': config_class['host'],
                                    'database': config_class['database']
                                }
                            else:
                                logging.warning(
                                    f"Dictionary {config_info} in {config_path} does not have 'host' or 'database' keys.")
                                return None
                    else:
                        logging.warning(f"Configuration class {config_info} not found in {config_path}")
                except Exception as e:
                    logging.warning(f"Failed to import configuration module from {config_path}: {e}")
            else:
                logging.warning(f"Configuration file {config_path} does not exist.")
        logging.warning(f"Configuration class {config_info} not found in any provided config paths.")
        return None

    # 对于shell脚本而言
    elif os.path.splitext(file)[1] == '.sh':
        # 提取命令行中的配置（如：MYSQL 或 TIDB_GAS）
        config_pattern_direct = re.compile(rf'{name}=".*?-h\s*([^\s]+).*?(?:\s(\w+))?"')

        # 尝试匹配直接的主机名和数据库名
        match_direct = config_pattern_direct.search(file_content)

        if match_direct:
            host = match_direct.group(1).strip()  # 提取主机名
            database = match_direct.group(2).strip() if match_direct.group(2) else ''  # 提取数据库名，如果没有则为空
            return {'host': host, 'database': database}

        # 如果未找到主机名，处理配置文件方式（如：--defaults-file=${BASE}/tidbluna.cnf）
        config_pattern_file = re.compile(rf'{name}=".*?--defaults-file=\$\{{BASE\}}/(.*?)\s*"', re.DOTALL)
        match_file = config_pattern_file.search(file_content)

        if match_file:
            config_info = match_file.group(1).strip()

            # 获取配置文件完整路径
            dir_name = os.path.dirname(file)
            config_file_full_path = os.path.join(dir_name, config_info)

            # 检查配置文件是否存在
            if not os.path.exists(config_file_full_path):
                logging.warning(f"Configuration file {config_file_full_path} does not exist.")
                return None

            # 读取配置文件内容
            try:
                with open(config_file_full_path, 'r') as f:
                    config_content = f.read()
            except FileNotFoundError:
                logging.warning(f"File {config_file_full_path} not found.")
                return None

            # 使用正则表达式提取[client]部分的host和database
            client_pattern = re.compile(r'\[client\](.*?)\[mysql\]', re.DOTALL)
            client_match = client_pattern.search(config_content)

            if client_match:
                client_config = client_match.group(1)
                host_match = re.search(r'host\s*=\s*(.*)', client_config)
                database_match = re.search(r'database\s*=\s*(.*)', client_config)

                if host_match and database_match:
                    host = host_match.group(1).strip()
                    database = database_match.group(1).strip()
                    return {'host': host, 'database': database}
                else:
                    logging.warning(f"'host' or 'database' not found in [client] section of {config_file_full_path}")
                    return None
            else:
                logging.warning(f"[client] section not found or not followed by [mysql] in {config_file_full_path}")
                return None
        else:
            logging.warning(f"Configuration for {name} not found in {file_content}")
            return None

    else:
        logging.warning(f"Unsupported file type: {file}")
        return None