import re
import logging
import os

def extract_sql_from_content(file_content, file_extension):
    """
    根据文件类型从文件内容中提取SQL语句
    Args:
        file_content: 文件内容
        file_extension: 文件格式
    Returns:
        list: 提取出的所有SQL语句
    ["DELETE FROM dwm_pay_account_daily\nWHERE day between '{self.date}' AND '{self.end_date}' and client_type=1 {gameids}",,,]
    """
    if file_extension == '.py':
        # 提取 Python 文件中的 SQL 语句（以三重引号包围的内容）
        return re.findall(r'sql.*?=\s*f?"""(.*?)"""', file_content, re.IGNORECASE|re.DOTALL)
    elif file_extension == '.sh':
        # 提取 shell 文件中的 SQL 语句（在 ${my} -vvv -e " 和 " 之间）
        return re.findall(r'\$\{my\}\s+-vvv\s+-e\s*"(.*?)"', file_content, re.DOTALL)
    else:
        logging.error(f"Unsupported file extension: {file_extension}")
        return []

def extract_sql_from_content_with_config (file_content, file_extension):
    """
    根据文件类型从文件内容中提取SQL语句和配置信息
    Args:
        file_content: 文件内容
        file_extension: 文件格式
    Returns:
        list: 提取出的所有SQL语句和配置信息
    [("DELETE FROM dwm_pay_account_daily\nWHERE day between '{self.date}' AND '{self.end_date}' and client_type=1 {gameids}", 'my'),(),()]
    """
    if file_extension == '.py':
        # 提取 Python 文件中的 SQL 语句（以三重引号包围的内容）
        pattern = re.compile(
            r'sql.*?=\s*f?"""(.*?)"""\s*.*?(?:self\.(\w+)\.)?',
            re.DOTALL | re.IGNORECASE
        )
        matches = pattern.findall(file_content)
        return matches
    elif file_extension == '.sh':
        # 后续如果shell脚本当中的每个sql语句的数据库信息不同，可以在这里进行修改，只要提取 -vvv -e ""之间的内容，去匹配前面的，然后再去开头扫
        pattern = re.compile(r'\$\{?([^\s{}]+)}?\s.{0,10}-e\s*"(.*?)"', re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(file_content)
        new_list = []
        for i in range(len(matches)):
            new_list.append(tuple(reversed(matches[i])))
        return new_list
    else:
        logging.error(f"Unsupported file extension: {file_extension}")
        return []

def ensure_database_name(table, default_dbname="<default>"):
    """
    确保提取的表名前有库名
    Args:
        table: 表名
        default_dbname: 默认数据库名称
    Returns:
        str: 确保表名前有库名的表名
    """
    # 定义正则表达式，匹配不在大括号内的点
    pattern = re.compile(r'\.(?![^{}]*\})')
    # 如果没有点，直接添加默认数据库名称
    if '.' not in table:
        return f'{default_dbname}.{table}'
    # 如果有点，但点在大括号内
    if not pattern.search(table):
        return f'{default_dbname}.{table}'
    else:
        return table

def extract_tables_from_sql(sql):
    """
    从SQL语句中提取源表和目标表
    Args:
        sql: SQL语句
    Returns:
        list: 提取出的所有源表和目标表
    输出 [源表1，源表2，目标表] （如果没有源表或没有目标表则输出空）
    """
    # 用于存储目标表
    target_tables = []

    # 匹配INSERT INTO语句中的表名
    insert_match = re.findall(r'INSERT\s+INTO\s+([^\s;()]+)', sql, re.IGNORECASE)
    # 匹配REPLACE INTO语句中的表名
    replace_match = re.findall(r'REPLACE\s+INTO\s+([^\s;()]+)', sql, re.IGNORECASE)
    # 匹配UPDATE语句中的表名
    update_match = re.findall(r'UPDATE\s+([^\s;()]+)', sql, re.IGNORECASE)

    if insert_match:
        target_tables.extend(insert_match)

    elif replace_match:
        target_tables.extend(replace_match)

    elif update_match:
        target_tables.extend(update_match)

    # 三个都没扫到那target_tables就为空

    source_tables=[]

    # 提取源表 (FROM, JOIN)
    from_tables = re.findall(r'FROM\s+([^\s;()]+)', sql, re.IGNORECASE)

    if from_tables:
        source_tables.extend(from_tables)
    join_tables = re.findall(r'JOIN\s+([^\s;()]+)', sql, re.IGNORECASE)
    if join_tables:
        source_tables.extend(join_tables)


    # 如果提取到了目标表和源表
    if len(target_tables)!=0 and len(source_tables)!=0:

        # 确保提取的表名前有库名
        target_tables = [ensure_database_name(table) for table in target_tables]
        source_tables = [ensure_database_name(table) for table in source_tables]

        result = []
        result.extend(source_tables)
        result.extend(target_tables)

        return result
        # [源表，若干，目标表]

    else:
        return None

def process_files(files):
    """
    处理所有的文件
    Args:
        files: 所有文件的路径列表
    Returns:
        list: 处理后的结果列表
    ['sql_file\\jobs\\tidbluna_outdated_data_clear\\delete.sh',
    'sql_file\\jobs\\tidbluna_outdated_data_clear\\dumbo_tidbluna_clear_outdated_data.sh']
    输出类似： [[[脚本1，源表若干，目标表],[脚本1，源表若干,目标表]，……],[[脚本2，源表若干，目标表]]] sql->文件->所有文件
    """
    # 用于存储所有文件
    list_for_files = []
    # 对于每一个文件
    for file in files:
        # 读取文件内容
        try:
            with open(file, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file, 'r', encoding='latin1') as f:
                    file_content = f.read()
            except UnicodeDecodeError:
                logging.error(f"Failed to read file: {file}")
                continue

        # 获取文件扩展名
        file_extension = os.path.splitext(file)[1]

        # 提取 SQL 语句
        # 传入文件内容 文件格式
        # 返回提取出的SQL语句列表
        sql_statements = extract_sql_from_content(file_content, file_extension)

        # 用于存储一个文件
        list_for_file = []

        # 对于每一个文件中的sql语句
        for sql in sql_statements:

            sql = sql.strip()
            if not sql:
                continue

            # 从提取的 SQL 中提取目标表和源表
            tables = extract_tables_from_sql(sql)
            # [源表1，源表2，目标表]
            if tables:
                list_for_sql = []
                list_for_sql.append(file)
                list_for_sql.extend(tables)
                list_for_file.append(list_for_sql)

        list_for_files.append(list_for_file)

    logging.info(f"Processed {len(files)} files")
    return list_for_files
    #[[[脚本1，源表若干，目标表],[脚本1，源表若干,目标表]，……],[[脚本2，源表若干，目标表]]]

def process_files_with_config (files):
    """
    处理所有的文件
    Args:
        files: 所有文件的路径列表
    Returns:
        list: 处理后的结果列表
    ['sql_file\\jobs\\tidbluna_outdated_data_clear\\delete.sh',
    'sql_file\\jobs\\tidbluna_outdated_data_clear\\dumbo_tidbluna_clear_outdated_data.sh']
    输出类似： [[[脚本1，配置信息名，源表若干，目标表],[脚本1，配置信息名，源表若干,目标表]，……],[[脚本2，配置信息名，源表若干，目标表]]]
    """
    # 用于存储所有文件
    list_for_files = []
    # 对于每一个文件
    for file in files:
        # 读取文件内容
        try:
            with open(file, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file, 'r', encoding='latin1') as f:
                    file_content = f.read()
            except UnicodeDecodeError:
                logging.error(f"Failed to read file: {file}")
                continue

        # 获取文件扩展名
        file_extension = os.path.splitext(file)[1]

        # 提取 SQL 语句
        # 传入文件内容 文件格式
        # 返回提取出的SQL语句列表
        sql_statements_with_self_object =  extract_sql_from_content_with_config(file_content, file_extension)

        # 用于存储一个文件
        list_for_file = []

        # 对于每一个文件中的sql语句和配置信息
        # [('',''),(),()]
        for sql_with_dbi in sql_statements_with_self_object:
            # sql语句
            sql = sql_with_dbi[0]
            sql = sql.strip()
            if not sql:
                continue

            # 从提取的 SQL 中提取目标表和源表
            tables = extract_tables_from_sql(sql)
            # [源表，若干，目标表]
            if tables:
                list_for_sql = []
                list_for_sql.append(file)
                list_for_sql.append(sql_with_dbi[1])
                list_for_sql.extend(tables)
                list_for_file.append(list_for_sql)

        list_for_files.append(list_for_file)

    logging.info(f"Processed {len(files)} files")
    return list_for_files