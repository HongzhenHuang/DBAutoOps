import networkx as nx
import mysql.connector
from matplotlib.pyplot import title
from numpy.lib.utils import source
from sqlalchemy import label
from config import Config_DLM
import matplotlib.pyplot as plt
from pyvis.network import Network
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, session
import os
import uuid # For generating unique filenames

STATIC_FOLDER = 'static'
GRAPH_SUBDIR = 'lineage_graphs'
GRAPH_SAVE_DIR = os.path.join(STATIC_FOLDER, GRAPH_SUBDIR)

def draw_graph(host_name, db_name, table_name):
    """
    生成数据血缘关系图 根据实例名 库名 表名进行画图
    """
    try:
        os.makedirs(GRAPH_SAVE_DIR, exist_ok=True)
        # Generate a unique filename to avoid overwrites
        unique_filename = f"lineage_{uuid.uuid4()}.html"
        # Full path to save the file
        output_html_path = os.path.join(GRAPH_SAVE_DIR, unique_filename)
        # Relative path to use with url_for('static', ...) in Flask
        relative_html_path = os.path.join(GRAPH_SUBDIR, unique_filename).replace(os.sep, '/') # Use forward slashes for URL
        # 连接到 MySQL 数据库
        connection = mysql.connector.connect(
            host=Config_DLM.host,  # 数据库主机
            user=Config_DLM.user,  # 数据库用户名
            password=Config_DLM.password,  # 数据库密码
            database=Config_DLM.database,  # 数据库名称
            port=Config_DLM.port  # 数据库端口号
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)  # 使用 dictionary=True 以便直接获取字段名为键的字典
            # 查询所有记录
            cursor.execute("SELECT id, script, source_instance,source_db, source_table, target_instance, target_db, target_table FROM data_flow_new")
            rows = cursor.fetchall()
            # 创建一个有向图
            G = nx.DiGraph()
            # 避免重复处理
            seen = set()
            # 处理每一行记录
            for row in rows:
                # 如果该行已经处理过 跳过
                if row['id'] in seen:
                    continue
                target_instance = row['target_instance']
                target_db = row['target_db']
                target_table = row['target_table']
                source_instance = row['source_instance']
                source_db = row['source_db']
                source_table = row['source_table']
                # 寻找目标表 如果目标表在target列中
                if table_name == target_table and host_name == target_instance and db_name == target_db:
                    script_name = row['script']
                    if not G.has_node(f"{target_instance}.{target_db}.{target_table}"):
                        # 在图中添加节点 查询表节点设置为红色
                        G.add_node(f"{target_instance}.{target_db}.{target_table}")
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['instance'] = f"{target_instance}"
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['db'] = f"{target_db}"
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['table'] = f"{target_table}"
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['color'] = 'red'
                    if not (target_table == source_table and target_instance == source_instance and target_db == source_db):
                        if not G.has_node(f"{source_instance}.{source_db}.{source_table}"):
                            # 在图中添加source表节点 并添加边
                            G.add_node(f"{source_instance}.{source_db}.{source_table}")
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['instance'] = f"{source_instance}"
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['db'] = f"{source_db}"
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['table'] = f"{source_table}"
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['color'] = 'lightblue'

                    if G.has_edge(f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"):
                        existing_script = G.edges[f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"].get('script', '')
                        updated_script = existing_script + '\n' + script_name if existing_script else script_name
                        G.edges[f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"]['script'] = updated_script
                    else:
                        G.add_edge(f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}", script=script_name)

                    seen.add(row['id'])
                    # 如果source表还有上游表 继续添加节点和边
                    cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s AND target_db = %s AND target_instance = %s",(source_table,source_db,source_instance,))
                    up = cursor.fetchall()
                    while up:
                        new_up = []
                        for up_row in up:
                            if up_row['id'] in seen:
                                continue
                            up_script_name = up_row['script']
                            up_source_instance = up_row['source_instance']
                            up_source_db = up_row['source_db']
                            up_source_table = up_row['source_table']
                            up_target_instance = up_row['target_instance']
                            up_target_db = up_row['target_db']
                            up_target_table = up_row['target_table']

                            if not G.has_node(f"{up_source_instance}.{up_source_db}.{up_source_table}"):
                                G.add_node(f"{up_source_instance}.{up_source_db}.{up_source_table}")
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['instance'] = f"{up_source_instance}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['db'] = f"{up_source_db}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['table'] = f"{up_source_table}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['color'] = 'lightblue'

                            if G.has_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"):
                                existing_script = G.edges[f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"].get('script', '')
                                updated_script = existing_script + '\n' + up_script_name if existing_script else up_script_name
                                G.edges[f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"]['script'] = updated_script
                            else:
                                G.add_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}", script=up_script_name)


                            seen.add(up_row['id'])
                            cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s AND target_db = %s AND target_instance = %s",(up_source_table,up_source_db, up_source_instance,))
                            new_up.extend(cursor.fetchall())
                        up = new_up
                    # 如果target表还有下游表 继续添加节点和边
                    cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s AND source_db = %s AND source_instance = %s",(target_table,target_db, target_instance,))
                    down = cursor.fetchall()
                    while down:
                        new_down = []
                        for down_row in down:
                            if down_row['id'] in seen:
                                continue
                            down_script_name = down_row['script']
                            down_source_instance = down_row['source_instance']
                            down_source_db = down_row['source_db']
                            down_source_table = down_row['source_table']
                            down_target_instance = down_row['target_instance']
                            down_target_db = down_row['target_db']
                            down_target_table = down_row['target_table']

                            if not G.has_node(f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                G.add_node(f"{down_target_instance}.{down_target_db}.{down_target_table}")
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"]['instance'] = f"{down_target_instance}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"]['db'] = f"{down_target_db}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"]['table'] = f"{down_target_table}"
                                G.nodes[f"{down_target_instance}.{down_source_db}.{down_target_table}"]['color'] = 'green'

                            if G.has_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                existing_script = G.edges[
                                    f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"].get('script', '')
                                updated_script = existing_script + '\n' + down_script_name if existing_script else down_script_name
                                G.edges[f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"]['script'] = updated_script
                            else:
                                G.add_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}", script=down_script_name)

                            seen.add(down_row['id'])
                            cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s AND source_db = %s AND source_instance = %s ",(down_target_table,down_target_db,down_target_instance,))
                            new_down.extend(cursor.fetchall())
                        down = new_down


                # 寻找目标表 如果目标表在source列中
                elif table_name == row['source_table'] and host_name == row['source_instance'] and db_name == row['source_db']:
                    if row['id'] in seen:
                        continue
                    script_name = row['script']

                    if not G.has_node(f"{source_instance}.{source_db}.{source_table}"):
                        # 在图中添加节点 查询表节点设置为红色
                        G.add_node(f"{source_instance}.{source_db}.{source_table}")
                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['instance'] = f"{source_instance}"
                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['db'] = f"{source_db}"
                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['table'] = f"{source_table}"

                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['color'] = 'red'

                    if not (target_table == source_table and target_instance == source_instance and target_db == source_db):
                        # 在图中添加target节点，并添加边
                        if not G.has_node(f"{target_instance}.{target_db}.{target_table}"):
                            G.add_node(f"{target_instance}.{target_db}.{target_table}")
                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['instance'] = f"{target_instance}"
                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['db'] = f"{target_db}"
                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['table'] = f"{target_table}"
                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['color'] = 'green'


                    if G.has_edge(f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"):
                        existing_script = G.edges[f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"].get('script', '')
                        updated_script = existing_script + '\n' + script_name if existing_script else script_name
                        G.edges[f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"]['script'] = updated_script
                    else:
                        G.add_edge(f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}", script=script_name)

                    # G.add_edge(f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}", script=script_name)
                    seen.add(row['id'])
                    # 如果source还有上游 继续添加节点和边
                    cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s AND target_db = %s AND target_instance = %s",(source_table, source_db, source_instance,))
                    up = cursor.fetchall()
                    while up:
                        new_up = []
                        for up_row in up:
                            if up_row['id'] in seen:
                                continue
                            up_script_name = up_row['script']
                            up_source_instance = up_row['source_instance']
                            up_source_db = up_row['source_db']
                            up_source_table = up_row['source_table']
                            up_target_instance = up_row['target_instance']
                            up_target_db = up_row['target_db']
                            up_target_table = up_row['target_table']
                            if not G.has_node(f"{up_source_instance}.{up_source_db}.{up_source_table}"):
                                G.add_node(f"{up_source_instance}.{up_source_db}.{up_source_table}")
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['instance'] = f"{up_source_instance}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['db'] = f"{up_source_db}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['table'] = f"{up_source_table}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['color'] = 'lightblue'

                            if G.has_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"):
                                existing_script = G.edges[
                                    f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"].get('script', '')
                                updated_script = existing_script + '\n' + up_script_name if existing_script else up_script_name
                                G.edges[f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"]['script'] = updated_script
                            else:
                                G.add_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}", script=up_script_name)


                            seen.add(up_row['id'])
                            cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s AND target_db = %s AND target_instance = %s",(up_source_table, up_source_db, up_source_instance,))
                            new_up.extend(cursor.fetchall())
                        up = new_up
                    # 如果target还有下游 继续添加节点和边
                    cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s AND source_db = %s AND source_instance = %s",(target_table, target_db, target_instance))
                    down = cursor.fetchall()
                    while down:
                        new_down = []
                        for down_row in down:
                            if down_row['id'] in seen:
                                continue
                            down_script_name = down_row['script']
                            down_source_instance = down_row['source_instance']
                            down_source_db = down_row['source_db']
                            down_source_table = down_row['source_table']
                            down_target_instance = down_row['target_instance']
                            down_target_db = down_row['target_db']
                            down_target_table = down_row['target_table']
                            if not G.has_node(f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                G.add_node(f"{down_target_instance}.{down_target_db}.{down_target_table}")
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"]['instance'] = f"{down_target_instance}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"]['db'] = f"{down_target_db}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"]['table'] = f"{down_target_table}"

                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"]['color'] = 'green'

                            # G.add_edge(f"{down_source_instance}.{down_target_db}.{down_source_table}",f"{down_target_instance}.{down_target_db}.{down_target_table}", script=down_script_name)
                            if G.has_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                existing_script = G.edges[f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"].get('script', '')
                                updated_script = existing_script + '\n' + down_script_name if existing_script else down_script_name
                                G.edges[f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"]['script'] = updated_script
                            else:
                                G.add_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}", script=down_script_name)

                            seen.add(down_row['id'])
                            cursor.execute("SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s AND source_db = %s AND source_instance = %s",(down_target_table, down_target_db, down_target_instance,))
                            new_down.extend(cursor.fetchall())
                        down = new_down



            # 动态的
            # 创建交互式图形
            nt = Network("900px", "2000px", notebook=True, directed=True)

            nt.set_options('''
            {
              "layout": {
                "hierarchical": {
                  "enabled": true,
                  "levelSeparation": 300,
                  "nodeSpacing": 100,
                  "treeSpacing": 200,
                  "direction": "LR",
                  "sortMethod": "directed"
                }
              },
              "physics": {
                "hierarchicalRepulsion": {
                  "nodeDistance": 120,
                  "centralGravity": 0.0,
                  "springLength": 100,
                  "springConstant": 0.01,
                  "damping": 0.09
                }
              },
              "nodes": {
                "shape": "dot",  
                  "size": 10,    
                  "font": {
                  "size": 16    
                }
              }
            }
            ''')

            # 添加节点和边到图形
            for node in G.nodes:
                # 获取节点的颜色，如果没有设置，使用默认颜色
                color = G.nodes[node].get('color', 'blue')  # 默认为蓝色
                table = G.nodes[node].get('table', )
                title = f"host : {G.nodes[node].get('instance',)} \ndb : {G.nodes[node].get('db',)}"
                nt.add_node(node, color=color, label = table, title = title)
            for edge in G.edges:
                nt.add_edge(edge[0], edge[1], title = G.edges[edge].get('script', ''), color = 'lightblue')

            # 显示图形
            # nt.show("example.html")
            nt.write_html(output_html_path, notebook=False)

            legend_html = """
            <div style="position:absolute; top: 10px; right: 10px; border: 1px solid black; padding: 10px; background-color: white;">
                <h3>explain</h3>
                <p><span style="display: inline-block; width: 12px; height: 12px; background-color: red;"></span> target</p>
                <p><span style="display: inline-block; width: 12px; height: 12px; background-color: lightblue;"></span> upstream</p>
                <p><span style="display: inline-block; width: 12px; height: 12px; background-color: green;"></span> downstream</p>
            </div>
            """
            try:
                with open(output_html_path, "r", encoding='utf-8') as file:
                    html_content = file.read()
                # Insert legend before closing body tag
                html_content = html_content.replace("</body>", legend_html + "</body>")
                with open(output_html_path, "w", encoding='utf-8') as file:
                    file.write(html_content)
                logging.info(f"Graph with legend saved successfully to {output_html_path}")
            except Exception as legend_err:
                logging.error(f"Could not add legend to {output_html_path}: {legend_err}")
                # Decide if failure to add legend means failure of the function
                # We can still return the path without the legend if needed.

            # --- End Legend insertion ---

            # <<< RETURN SUCCESS >>>
            # Return the relative path for use in url_for('static', ...)
            return relative_html_path

        else:
             logging.error("Failed to connect to the database.")
             return None # Indicate failure

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        # <<< RETURN FAILURE >>>
        return None # Indicate failure due to DB error
    except nx.NetworkXError as nx_err:
        logging.error(f"NetworkX graph error: {nx_err}")
        # <<< RETURN FAILURE >>>
        return None # Indicate failure due to graph error
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(f"An unexpected error occurred in draw_graph: {e}", exc_info=True)
        # <<< RETURN FAILURE >>>
        return None # Indicate general failure

    finally:
        # Ensure database connection is closed
        if cursor:
            try:
                cursor.close()
            except Exception as cur_err:
                 logging.warning(f"Error closing cursor: {cur_err}")
        if connection and connection.is_connected():
            try:
                connection.close()
                logging.info("Database connection closed.")
            except Exception as con_err:
                 logging.warning(f"Error closing connection: {con_err}")

def draw_graph_with_table(table_name):
    """
    从数据库中获取数据并生成图形
    """
    host_name = '<default>'
    db_name = '<default>'
    # Generate a unique filename to avoid overwrites
    unique_filename = f"lineage_{uuid.uuid4()}.html"
    # Full path to save the file
    output_html_path = os.path.join(GRAPH_SAVE_DIR, unique_filename)
    # Relative path to use with url_for('static', ...) in Flask
    relative_html_path = os.path.join(GRAPH_SUBDIR, unique_filename).replace(os.sep, '/') # Use forward slashes for URL

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
            cursor = connection.cursor(dictionary=True)  # 使用 dictionary=True 以便直接获取字段名为键的字典
            # 查询所有记录
            cursor.execute(
                "SELECT id, script, source_instance,source_db, source_table, target_instance, target_db, target_table FROM data_flow_new")
            rows = cursor.fetchall()
            # 创建一个有向图
            G = nx.DiGraph()
            # 避免重复处理
            seen = set()
            # 处理每一行记录
            for row in rows:
                # 如果该行已经处理过 跳过
                if row['id'] in seen:
                    continue
                target_instance = '<default>'
                target_db = '<default>'
                target_table = row['target_table']
                source_instance = '<default>'
                source_db = '<default>'
                source_table = row['source_table']
                # 寻找目标表 如果目标表在target列中
                if table_name == target_table and host_name == target_instance and db_name == target_db:
                    script_name = row['script']
                    if not G.has_node(f"{target_instance}.{target_db}.{target_table}"):
                        # 在图中添加节点 查询表节点设置为红色
                        G.add_node(f"{target_instance}.{target_db}.{target_table}")
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['instance'] = f"{target_instance}"
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['db'] = f"{target_db}"
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['table'] = f"{target_table}"
                        G.nodes[f"{target_instance}.{target_db}.{target_table}"]['color'] = 'red'
                    if not (target_table == source_table and target_instance == source_instance and target_db == source_db):
                        if not G.has_node(f"{source_instance}.{source_db}.{source_table}"):
                            # 在图中添加source表节点 并添加边
                            G.add_node(f"{source_instance}.{source_db}.{source_table}")
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['instance'] = f"{source_instance}"
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['db'] = f"{source_db}"
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['table'] = f"{source_table}"
                            G.nodes[f"{source_instance}.{source_db}.{source_table}"]['color'] = 'lightblue'

                    if G.has_edge(f"{source_instance}.{source_db}.{source_table}",
                                  f"{target_instance}.{target_db}.{target_table}"):
                        existing_script = G.edges[
                            f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"].get(
                            'script', '')
                        updated_script = existing_script + '\n' + script_name if existing_script else script_name
                        G.edges[
                            f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"][
                            'script'] = updated_script
                    else:
                        G.add_edge(f"{source_instance}.{source_db}.{source_table}",
                                   f"{target_instance}.{target_db}.{target_table}", script=script_name)

                    seen.add(row['id'])
                    # 如果source表还有上游表 继续添加节点和边
                    cursor.execute(
                        "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s ",
                        (source_table,))
                    up = cursor.fetchall()
                    while up:
                        new_up = []
                        for up_row in up:
                            if up_row['id'] in seen:
                                continue
                            up_script_name = up_row['script']
                            up_source_instance = '<default>'
                            up_source_db = '<default>'
                            up_source_table = up_row['source_table']
                            up_target_instance = '<default>'
                            up_target_db = '<default>'
                            up_target_table = up_row['target_table']

                            if not G.has_node(f"{up_source_instance}.{up_source_db}.{up_source_table}"):
                                G.add_node(f"{up_source_instance}.{up_source_db}.{up_source_table}")

                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"][
                                    'instance'] = f"{up_source_instance}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"][
                                    'db'] = f"{up_source_db}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"][
                                    'table'] = f"{up_source_table}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['color'] = 'lightblue'

                            if G.has_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}",
                                          f"{up_target_instance}.{up_target_db}.{up_target_table}"):
                                existing_script = G.edges[
                                    f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"].get(
                                    'script', '')
                                updated_script = existing_script + '\n' + up_script_name if existing_script else up_script_name
                                G.edges[
                                    f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"][
                                    'script'] = updated_script
                            else:
                                G.add_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}",
                                           f"{up_target_instance}.{up_target_db}.{up_target_table}",
                                           script=up_script_name)

                            seen.add(up_row['id'])
                            cursor.execute(
                                "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s ",
                                (up_source_table, ))
                            new_up.extend(cursor.fetchall())
                        up = new_up
                    # 如果target表还有下游表 继续添加节点和边
                    cursor.execute(
                        "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s ",
                        (target_table,))
                    down = cursor.fetchall()
                    while down:
                        new_down = []
                        for down_row in down:
                            if down_row['id'] in seen:
                                continue
                            down_script_name = down_row['script']
                            down_source_instance = '<default>'
                            down_source_db = '<default>'
                            down_source_table = down_row['source_table']
                            down_target_instance = '<default>'
                            down_target_db = '<default>'
                            down_target_table = down_row['target_table']

                            if not G.has_node(f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                G.add_node(f"{down_target_instance}.{down_target_db}.{down_target_table}")

                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'instance'] = f"{down_target_instance}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'db'] = f"{down_target_db}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'table'] = f"{down_target_table}"
                                G.nodes[f"{down_target_instance}.{down_source_db}.{down_target_table}"][
                                    'color'] = 'green'

                            if G.has_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}",
                                          f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                existing_script = G.edges[
                                    f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"].get(
                                    'script', '')
                                updated_script = existing_script + '\n' + down_script_name if existing_script else down_script_name
                                G.edges[
                                    f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'script'] = updated_script
                            else:
                                G.add_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}",
                                           f"{down_target_instance}.{down_target_db}.{down_target_table}",
                                           script=down_script_name)

                            seen.add(down_row['id'])
                            cursor.execute(
                                "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s ",
                                (down_target_table, ))
                            new_down.extend(cursor.fetchall())
                        down = new_down


                # 寻找目标表 如果目标表在source列中
                elif table_name == source_table and host_name == source_instance and db_name == source_db:
                    if row['id'] in seen:
                        continue
                    script_name = row['script']

                    if not G.has_node(f"{source_instance}.{source_db}.{source_table}"):
                        # 在图中添加节点 查询表节点设置为红色
                        G.add_node(f"{source_instance}.{source_db}.{source_table}")

                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['instance'] = f"{source_instance}"
                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['db'] = f"{source_db}"
                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['table'] = f"{source_table}"

                        G.nodes[f"{source_instance}.{source_db}.{source_table}"]['color'] = 'red'

                    if not (
                            target_table == source_table and target_instance == source_instance and target_db == source_db):
                        # 在图中添加target节点，并添加边
                        if not G.has_node(f"{target_instance}.{target_db}.{target_table}"):
                            G.add_node(f"{target_instance}.{target_db}.{target_table}")

                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['instance'] = f"{target_instance}"
                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['db'] = f"{target_db}"
                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['table'] = f"{target_table}"
                            G.nodes[f"{target_instance}.{target_db}.{target_table}"]['color'] = 'green'

                    if G.has_edge(f"{source_instance}.{source_db}.{source_table}",
                                  f"{target_instance}.{target_db}.{target_table}"):
                        existing_script = G.edges[
                            f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"].get(
                            'script', '')
                        updated_script = existing_script + '\n' + script_name if existing_script else script_name
                        G.edges[
                            f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}"][
                            'script'] = updated_script
                    else:
                        G.add_edge(f"{source_instance}.{source_db}.{source_table}",
                                   f"{target_instance}.{target_db}.{target_table}", script=script_name)

                    # G.add_edge(f"{source_instance}.{source_db}.{source_table}", f"{target_instance}.{target_db}.{target_table}", script=script_name)
                    seen.add(row['id'])
                    # 如果source还有上游 继续添加节点和边
                    cursor.execute(
                        "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s ",
                        (source_table, ))
                    up = cursor.fetchall()
                    while up:
                        new_up = []
                        for up_row in up:
                            if up_row['id'] in seen:
                                continue
                            up_script_name = up_row['script']
                            up_source_instance = '<default>'
                            up_source_db = '<default>'
                            up_source_table = up_row['source_table']
                            up_target_instance = '<default>'
                            up_target_db = '<default>'
                            up_target_table = up_row['target_table']
                            if not G.has_node(f"{up_source_instance}.{up_source_db}.{up_source_table}"):
                                G.add_node(f"{up_source_instance}.{up_source_db}.{up_source_table}")
                                # node_labels[f"{up_source_instance}.{up_source_db}.{up_source_table}"] = f"{up_source_instance}.{up_source_db}.{up_source_table}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"][
                                    'instance'] = f"{up_source_instance}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"][
                                    'db'] = f"{up_source_db}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"][
                                    'table'] = f"{up_source_table}"
                                G.nodes[f"{up_source_instance}.{up_source_db}.{up_source_table}"]['color'] = 'lightblue'

                            if G.has_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}",
                                          f"{up_target_instance}.{up_target_db}.{up_target_table}"):
                                existing_script = G.edges[
                                    f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"].get(
                                    'script', '')
                                updated_script = existing_script + '\n' + up_script_name if existing_script else up_script_name
                                G.edges[
                                    f"{up_source_instance}.{up_source_db}.{up_source_table}", f"{up_target_instance}.{up_target_db}.{up_target_table}"][
                                    'script'] = updated_script
                            else:
                                G.add_edge(f"{up_source_instance}.{up_source_db}.{up_source_table}",
                                           f"{up_target_instance}.{up_target_db}.{up_target_table}",
                                           script=up_script_name)


                            seen.add(up_row['id'])
                            cursor.execute(
                                "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE target_table = %s ",
                                (up_source_table,))
                            new_up.extend(cursor.fetchall())
                        up = new_up
                    # 如果target还有下游 继续添加节点和边
                    cursor.execute(
                        "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s ",
                        (target_table, ))
                    down = cursor.fetchall()
                    while down:
                        new_down = []
                        for down_row in down:
                            if down_row['id'] in seen:
                                continue
                            down_script_name = down_row['script']
                            down_source_instance = '<default>'
                            down_source_db = '<default>'
                            down_source_table = down_row['source_table']
                            down_target_instance = '<default>'
                            down_target_db = '<default>'
                            down_target_table = down_row['target_table']
                            if not G.has_node(f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                G.add_node(f"{down_target_instance}.{down_target_db}.{down_target_table}")
                                # node_labels[f"{down_target_instance}.{down_target_db}.{down_target_table}"] = f"{down_target_instance}.{down_target_db}.{down_target_table}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'instance'] = f"{down_target_instance}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'db'] = f"{down_target_db}"
                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'table'] = f"{down_target_table}"

                                G.nodes[f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'color'] = 'green'


                            if G.has_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}",
                                          f"{down_target_instance}.{down_target_db}.{down_target_table}"):
                                existing_script = G.edges[
                                    f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"].get(
                                    'script', '')
                                updated_script = existing_script + '\n' + down_script_name if existing_script else down_script_name
                                G.edges[
                                    f"{down_source_instance}.{down_source_db}.{down_source_table}", f"{down_target_instance}.{down_target_db}.{down_target_table}"][
                                    'script'] = updated_script
                            else:
                                G.add_edge(f"{down_source_instance}.{down_source_db}.{down_source_table}",
                                           f"{down_target_instance}.{down_target_db}.{down_target_table}",
                                           script=down_script_name)

                            seen.add(down_row['id'])
                            cursor.execute(
                                "SELECT id, script, source_instance, source_db, source_table, target_instance, target_db, target_table FROM data_flow_new WHERE source_table = %s ",
                                (down_target_table, ))
                            new_down.extend(cursor.fetchall())
                        down = new_down

            # 动态的
            # 创建交互式图形
            nt = Network("900px", "2000px", notebook=True, directed=True)

            nt.set_options('''
            {
              "layout": {
                "hierarchical": {
                  "enabled": true,
                  "levelSeparation": 300,
                  "nodeSpacing": 100,
                  "treeSpacing": 200,
                  "direction": "LR",
                  "sortMethod": "directed"
                }
              },
              "physics": {
                "hierarchicalRepulsion": {
                  "nodeDistance": 120,
                  "centralGravity": 0.0,
                  "springLength": 100,
                  "springConstant": 0.01,
                  "damping": 0.09
                }
              },
              "nodes": {
                "shape": "dot",  
                  "size": 10,    
                  "font": {
                  "size": 16    
                }
              }
            }
            ''')

            # 添加节点和边到图形
            for node in G.nodes:
                # 获取节点的颜色，如果没有设置，使用默认颜色
                color = G.nodes[node].get('color', 'blue')  # 默认为蓝色
                table = G.nodes[node].get('table', )
                title = f"host : {G.nodes[node].get('instance', )} \ndb : {G.nodes[node].get('db', )}"
                nt.add_node(node, color=color, label=table, title=title)
            for edge in G.edges:

                nt.add_edge(edge[0], edge[1], title=G.edges[edge].get('script', ''), color='lightblue')

            # # 显示图形
            # nt.show("example.html")
            nt.write_html(output_html_path, notebook=False)


            legend_html = """
            <div style="position:absolute; top: 10px; right: 10px; border: 1px solid black; padding: 10px; background-color: white;">
                <h3>explain</h3>
                <p><span style="display: inline-block; width: 12px; height: 12px; background-color: red;"></span> target</p>
                <p><span style="display: inline-block; width: 12px; height: 12px; background-color: lightblue;"></span> upstream</p>
                <p><span style="display: inline-block; width: 12px; height: 12px; background-color: green;"></span> downstream</p>
            </div>
            """

            try:
                with open(output_html_path, "r", encoding='utf-8') as file:
                    html_content = file.read()
                # Insert legend before closing body tag
                html_content = html_content.replace("</body>", legend_html + "</body>")
                with open(output_html_path, "w", encoding='utf-8') as file:
                    file.write(html_content)
                logging.info(f"Graph with legend saved successfully to {output_html_path}")
            except Exception as legend_err:
                logging.error(f"Could not add legend to {output_html_path}: {legend_err}")

            return relative_html_path

        else:
             logging.error("Failed to connect to the database.")
             return None # Indicate failure

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        # <<< RETURN FAILURE >>>
        return None # Indicate failure due to DB error
    except nx.NetworkXError as nx_err:
        logging.error(f"NetworkX graph error: {nx_err}")
        # <<< RETURN FAILURE >>>
        return None # Indicate failure due to graph error
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(f"An unexpected error occurred in draw_graph: {e}", exc_info=True)
        # <<< RETURN FAILURE >>>
        return None # Indicate general failure

    finally:
        # Ensure database connection is closed
        if cursor:
            try:
                cursor.close()
            except Exception as cur_err:
                 logging.warning(f"Error closing cursor: {cur_err}")
        if connection and connection.is_connected():
            try:
                connection.close()
                logging.info("Database connection closed.")
            except Exception as con_err:
                 logging.warning(f"Error closing connection: {con_err}")

def draw_graph_choice(host=None, db=None, table=None):
    """
    实现多态 根据传入的参数进行函数选择
    """
    if host and db and table:
        # 根据实例名 库名 表名画图
        path = draw_graph(host, db, table)
        return path
    elif table: 
        print(2222222)
        path = draw_graph_with_table(table)
        # 根据表名画图
        return path
    else:
        raise ValueError("Insufficient arguments provided to draw the graph")

def generate_lineage_graph_route():
    """
    生成血缘图的路由
    """
    host = request.form.get('host')
    db = request.form.get('db')
    table = request.form.get('table')
    try:
        graph_path = draw_graph_choice(host=host, db=db, table=table)
        if graph_path:
            flash("血缘图生成成功！", "graph_status")
            # 需要将 graph_path 传递给模板
            print(graph_path)
            return render_template('data_lineage.html', graph_html_path=graph_path)
        else:
            flash("未能生成血缘图或无数据。", "graph_status")
    except Exception as e:
        flash(f"生成血缘图时出错: {e}", "graph_status")
    return render_template('data_lineage.html')


