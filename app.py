from flask import Flask
from config import Config_users
from auth import register, login, dashboard, logout, home
from utils import init_db, to_back_up, to_data_lineage
from backUp_module.back_up import query_table, backup_table_route, get_table_fields
from dlm_module.sql_extract_to_db import run_gitlab_scanner
from dlm_module.draw import generate_lineage_graph_route
from alioth_module.alioth import analyze_table, show_templates_page, view_specific_template

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
app.add_url_rule('/to_back_up', 'to_back_up', to_back_up, methods=['GET', 'POST'])
app.add_url_rule('/query_table', 'query_table', query_table, methods=['GET', 'POST'])
app.add_url_rule('/backup_table_route', 'backup_table_route', backup_table_route, methods=['GET', 'POST'])
app.add_url_rule('/get_table_fields', 'get_table_fields', get_table_fields, methods=['GET', 'POST'])

app.add_url_rule('/to_data_lineage', 'to_data_lineage', to_data_lineage, methods=['GET', 'POST'])
app.add_url_rule('/run_gitlab_scanner', 'run_gitlab_scanner', run_gitlab_scanner, methods=['GET', 'POST'])
app.add_url_rule('/generate_lineage_graph_route', 'generate_lineage_graph_route', generate_lineage_graph_route, methods=['GET', 'POST'])

app.add_url_rule('/analyze_table', 'analyze_table', analyze_table, methods=['GET', 'POST'])
app.add_url_rule('/show_templates_page', 'show_templates_page', show_templates_page, methods=['GET', 'POST'])
app.add_url_rule('/view_specific_template', 'view_specific_template', view_specific_template, methods=['GET'])

if __name__ == '__main__':
    init_db(Config_users.MYSQL_HOST, Config_users.MYSQL_USER, Config_users.MYSQL_PASSWORD, Config_users.MYSQL_DATABASE)
    app.run(debug=True, port = 5001, use_reloader=False)