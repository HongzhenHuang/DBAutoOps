from os import name

import sys
sys.path.append('/home/ldaphome/hhz/workspace/DBAutoOps/alioth_module')
import mysql.connector
import json
from config import Config_alioth
import re
import hashlib
import logging
from collections import OrderedDict
from generate import output_json_grammar, output_json_grammar_based_on_type_special_element
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

def generate_identifier(str1: str, str2: str, str3: str, str4: str) -> str:
    """
    根据四个字符串进行哈希映射
    :param str1: 第一个字符串
    :param str2: 第二个字符串
    :param str3: 第三个字符串
    :param str4: 第四个字符串
    :return: 生成的哈希值
    """
    # 将四个字符串组合成一个字典
    combined_dict = {
        "sources": str1,
        "udfs": str2,
        "sinks": str3,
        "version": str4
    }
    # 对字典按键排序
    sorted_combined_dict = OrderedDict(sorted(combined_dict.items(), key=lambda x: x[0]))
    # 将排序后的字典转换为 JSON 字符串，并生成 MD5 哈希值
    return hashlib.md5(json.dumps(sorted_combined_dict, separators=(',', ':')).encode()).hexdigest()

def generate_identifier_for_parser(str1: str, str2: str) -> str:
    """
    根据两个字符串进行哈希映射
    :param str1: 第一个字符串
    :param str2: 第二个字符串
    :return: 生成的哈希值
    """
    # 将四个字符串组合成一个字典
    combined_dict = {
        "parser": str1,
        "version": str2,
    }
    # 对字典按键排序
    sorted_combined_dict = OrderedDict(sorted(combined_dict.items(), key=lambda x: x[0]))
    # 将排序后的字典转换为 JSON 字符串，并生成 MD5 哈希值
    return hashlib.md5(json.dumps(sorted_combined_dict, separators=(',', ':')).encode()).hexdigest()

def simplify_udf_group_string(udf_group_string):
    """
    简化 UDF 组字符串
    :param udf_group_string: 原始的 UDF 组字符串
    :return: 简化后的 UDF 组字符串
    """
    if not udf_group_string:
        return ""
    # 使用 "/" 分割不同部分
    parts = udf_group_string.split('/')
    # 处理每一部分，保留每一部分的第一段字符
    simplified_parts = []
    for part in parts:
        segments = part.split('.')
        if segments:
            simplified_parts.append(segments[0])
    # 用 "/" 合并简化后的部分
    return '/'.join(simplified_parts)

def find_most_frequent_full_relationship(relationship_data, relationship):
    """
    找出出现次数最多的完整关系
    :param relationship_data: 关系数据字典
    :param relationship: 要匹配的关系
    :return: 出现次数最多的完整关系及其出现次数
    """
    # 用于记录符合条件的完整关系及其出现次数
    filtered_relationships = {}
    relationship_parts = relationship.split('->')
    for full_relationship, count in relationship_data.items():
        # 将完整关系拆分为组件
        parts = full_relationship.split('->')
        # 检查第一个和最后一个部分是否都为 'jdbc'
        if len(parts) >= 2 and parts[0] == relationship_parts[0] and parts[-1] == relationship_parts[-1]:
            if full_relationship in filtered_relationships:
                filtered_relationships[full_relationship] += count
            else:
                filtered_relationships[full_relationship] = count
    # 找出出现次数最多的完整关系
    most_frequent_relationship = max(filtered_relationships, key=filtered_relationships.get, default=None)
    max_count = filtered_relationships.get(most_frequent_relationship, 0)

    return most_frequent_relationship, max_count


def replace_in_json_grammar(input_dict, str1, str2):
    """
    遍历字典，将所有 JSON 格式的文法字符串中的指定值 str1 替换为 str2。
    :param input_dict: 输入的字典，键是文件名，值是 JSON 格式的文法字符串
    :param str1: 要替换的字符串
    :param str2: 替换后的字符串
    :return: 处理后的新字典
    """
    def replace_value(val, old_value, new_value):
        # 判断值是否为 JSON 格式字符串
        try:
            json_val = json.loads(val)
            if isinstance(json_val, (dict, list)):
                return json.dumps(replace_in_dict(json_val, old_value, new_value))
            else:
                return val.replace(old_value, new_value)
        except (ValueError, TypeError):
            return val.replace(old_value, new_value) if isinstance(val, str) else val

    def replace_in_dict(data, old_value, new_value):
        if isinstance(data, dict):
            return {k: replace_in_dict(v, old_value, new_value) for k, v in data.items()}
        elif isinstance(data, list):
            return [replace_in_dict(item, old_value, new_value) for item in data]
        elif isinstance(data, str):
            return data.replace(old_value, new_value)
        else:
            return data

    if isinstance(input_dict, dict):
        output_dict = {}
        for filename, json_grammar in input_dict.items():
            output_dict[filename] = replace_value(json_grammar, str1, str2)

        return output_dict

    elif isinstance(input_dict, str):
        return replace_value(input_dict, str1, str2)

    else:
        return input_dict

def replace_all_configs(output_json_grammar_intersection, output_json_grammar_union, parser_intersection, parser_union, Config):
    """
    遍历字典，将所有 JSON 格式的文法字符串中的指定值 str1 替换为 str2。
    :param input_dict: 输入的字典，键是文件名，值是 JSON 格式的文法字符串
    :param str1: 要替换的字符串
    :param str2: 替换后的字符串
    :return: 处理后的新字典
    """
    i = 1
    while True:
        # 构造 before 和 after 的属性名称
        before_attr = f"before{i}"
        after_attr = f"after{i}"

        # 检查 Config 是否有对应的 before 和 after 属性
        if hasattr(Config, before_attr) and hasattr(Config, after_attr):
            before_value = getattr(Config, before_attr)
            after_value = getattr(Config, after_attr)

            # 如果 before_value 或 after_value 为空，退出循环
            if not before_value or not after_value:
                break

            output_json_grammar_intersection = replace_in_json_grammar(output_json_grammar_intersection, before_value, after_value)
            output_json_grammar_union = replace_in_json_grammar(output_json_grammar_union, before_value, after_value)
            parser_intersection = replace_in_json_grammar(parser_intersection, before_value, after_value)
            parser_union = replace_in_json_grammar(parser_union, before_value, after_value)

            # 递增 i，继续下一个替换
            i += 1
        else:
            # 如果没有更多的 before 和 after，退出循环
            break

    return output_json_grammar_intersection, output_json_grammar_union, parser_intersection, parser_union

def analyze_and_generate_grammar(db_instance: str, db_name: str, table_name: str):
    """
    分析并生成文法。
    :param db_instance: 数据库实例
    :param db_name: 数据库名称
    :param table_name: 表名
    :return: 处理后的新字典
    """
    messages = []
    # 数据库连接信息（只读）
    db_config = {
        'user': Config_alioth.user,
        'password': Config_alioth.password,
        'host': db_instance,
        'database': db_name
    }

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    select_query = f"SELECT {Config_alioth.field1}, {Config_alioth.field2} FROM {table_name}"
    cursor.execute(select_query)

    relationship_count_sus = {}
    relationship_count_ss = {}
    relationship_count_whole = {}

    for (job_data, remote_start_name,) in cursor.fetchall():
        try:
            job_data = re.sub(r'--template\s+', '', job_data)
            json_data = json.loads(json.loads(job_data))
            sources = [source['type'] for source in json_data['sources']]
            sinks = [sink['type'] for sink in json_data['sinks']]

            def unique_dot_str(items):
                seen, out = set(), ''
                for i in items:
                    if i not in seen:
                        seen.add(i)
                        out += i + '.'
                return out.rstrip('.')

            sources_string = unique_dot_str(sources)
            sinks_string = unique_dot_str(sinks)

            udf_group_string = ''
            if 'udfs' in json_data and len(json_data['udfs']) > 0:
                udfs = json_data['udfs']
                if isinstance(udfs[0], list):
                    for udf_group in udfs:
                        for udf in udf_group:
                            udf_group_string += udf.get('udf.type', '') + '.'
                        udf_group_string = udf_group_string.rstrip('.') + '/'
                    udf_group_string = udf_group_string.rstrip('/')
                else:
                    for udf in udfs:
                        udf_group_string += udf.get('udf.type', '') + '.'
                    udf_group_string = udf_group_string.rstrip('.')

            rel_whole = f"{sources_string.lower()}->{udf_group_string.lower()}->{sinks_string.lower()}"
            relationship_count_whole.setdefault(rel_whole, []).append(remote_start_name)

            udf_group_simple = simplify_udf_group_string(udf_group_string)
            rel_sus = f"{sources_string.lower()}->{udf_group_simple.lower()}->{sinks_string.lower()}"
            rel_ss = f"{sources_string.lower()}->{sinks_string.lower()}"

            relationship_count_sus[rel_sus] = relationship_count_sus.get(rel_sus, 0) + 1
            relationship_count_ss[rel_ss] = relationship_count_ss.get(rel_ss, 0) + 1

        except json.JSONDecodeError:
            print(f"无效的JSON数据: {job_data}")

    relationship_count_sus_limit = {
        rel: count for rel, count in relationship_count_sus.items()
        if count > Config_alioth.times_for_grammer
    }

    for rel_ss in relationship_count_ss:
        if not any(
            rel_ss.split('->')[0] == k.split('->')[0] and rel_ss.split('->')[-1] == k.split('->')[-1]
            for k in relationship_count_sus_limit
        ):
            key, value = find_most_frequent_full_relationship(relationship_count_sus, rel_ss)
            relationship_count_sus_limit[key] = value

    for rel, streams in relationship_count_whole.items():
        if len(streams) > Config_alioth.times_for_grammer_2:
            relationship_count_sus_limit[rel] = streams

    for key, value in relationship_count_sus_limit.items():
        message = f"关系: {key}, 出现次数: {len(value) if isinstance(value, list) else value}"
        print(message)
        messages.append(message)
        # print(f"关系: {key}, 出现次数: {len(value) if isinstance(value, list) else value}")

    output_json_grammar_intersection = output_json_grammar(relationship_count_sus_limit, 'intersection')
    output_json_grammar_union = output_json_grammar(relationship_count_sus_limit, 'union')

    parser_union = output_json_grammar_based_on_type_special_element('union')
    parser_intersection = output_json_grammar_based_on_type_special_element('intersection')

    output_json_grammar_intersection, output_json_grammar_union, parser_intersection, parser_union = \
        replace_all_configs(output_json_grammar_intersection, output_json_grammar_union,
                            parser_intersection, parser_union, Config_alioth)

    cursor.close()
    connection.close()

    # 写入到在线数据库（写死）
    db_config_online = {
        'user': Config_alioth.user_for_online,
        'password': Config_alioth.password_for_online,
        'host': Config_alioth.host_for_online,
        'database': Config_alioth.database_for_online,
        'port': Config_alioth.port_for_online
    }

    connection = mysql.connector.connect(**db_config_online)
    cursor = connection.cursor()
    replace_query = f'REPLACE INTO {Config_alioth.table_name_for_online} (namespace, identifier, display_name, template, description, create_user, modify_user, source, sink, udf) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

    def get_origin_data(key):
        matched_streams, matched_rels = [], []
        for rel in relationship_count_whole:
            parts = rel.split('->')
            parts[1] = simplify_udf_group_string(parts[1])
            if f"{parts[0]}->{parts[1]}->{parts[2]}" == key or rel == key:
                matched_rels.append(rel)
                matched_streams.extend(relationship_count_whole[rel])
        return matched_rels, matched_streams

    for grammar_type, output in [('略', output_json_grammar_intersection), ('详', output_json_grammar_union)]:
        for key, value in output.items():
            matched_rels, matched_streams = get_origin_data(key)
            desc = {
                'original_relationship': matched_rels,
                'included_streams': matched_streams
            }
            cursor.execute(replace_query, (
                Config_alioth.namespace,
                generate_identifier(*key.split('->'), grammar_type),
                key.replace('->', '_') + f"({grammar_type})",
                value,
                json.dumps(desc),
                Config_alioth.create_user,
                Config_alioth.modify_user,
                str(key.split('->')[0].split('.')),
                str(key.split('->')[2].split('.')),
                str([item for sub in key.split('->')[1].split('.') for item in sub.split('/')])
            ))

    cursor.execute(replace_query, (
        Config_alioth.namespace,
        generate_identifier_for_parser('parser', '详'),
        'parser(详)',
        parser_union,
        'parser详细版本，selectors, filters和post_filters展开',
        Config_alioth.create_user,
        Config_alioth.modify_user,
        '[]', '[]', '[]'))

    cursor.execute(replace_query, (
        Config_alioth.namespace,
        generate_identifier_for_parser('parser', '略'),
        'parser(略)',
        parser_intersection,
        'parser简略版本，selectors, filters和post_filters展开',
        Config_alioth.create_user,
        Config_alioth.modify_user,
        '[]', '[]', '[]'))

    connection.commit()

    # 查询典范数量
    count_query = f"SELECT COUNT(*) FROM {Config_alioth.table_name_for_online}"
    cursor.execute(count_query)
    count_result = cursor.fetchone()
    print(f"目前作业典范表中有 {count_result[0]} 个模板")
    messages.append(f"目前作业典范表中有 {count_result[0]} 个模板")

    cursor.close()
    connection.close()
    return messages

def analyze_table():
    """
    分析表结构并生成语法规则 (处理 POST 请求，然后重定向)
    """
    # 这个函数只处理 POST 逻辑，不再直接渲染模板
    if request.method == 'POST':
        host = request.form.get('host')
        database = request.form.get('database')
        table = request.form.get('table')
        all_messages = []

        # 添加基本的输入验证
        if not all([host, database, table]):
             # 使用正确的 category!
             flash("实例名、数据库名和表名都不能为空。", 'generation_status')
             # 重定向回显示表单的页面，假设其端点名为 'show_alioth_example_page'
             return redirect(url_for('show_alioth_example_page')) # <--- 修改点 1: 重定向

        print(f"Analyzing: host={host}, database={database}, table={table}")

        try:
            # 假设 analyze_and_generate_grammar 返回消息列表
            messages = analyze_and_generate_grammar(host, database, table)
            all_messages.extend(messages)
            # 可以考虑加一个最终的成功提示
            if messages and not any("失败" in msg or "错误" in msg for msg in messages):
                 all_messages.append("分析成功完成。")

        except Exception as e:
            logging.error(f"Error during analysis: {e}", exc_info=True) # 记录详细错误
            all_messages.append(f"分析失败：{str(e)}")

        # 使用正确的 category!
        if all_messages:
            flash('<br>'.join(all_messages), 'generation_status') # <--- 修改点 2: 添加 category

        # 重定向回显示表单和结果的页面
        # 替换 'show_alioth_example_page' 为你实际用于显示 alioth_example.html 的路由端点名
        return redirect(url_for('show_templates_page')) # <--- 修改点 1: 重定向

def get_db_connection():
    """建立并返回一个数据库连接。"""
    db_config_online = {
        'user': Config_alioth.user_for_online,
        'password': Config_alioth.password_for_online,
        'host': Config_alioth.host_for_online,
        'database': Config_alioth.database_for_online,
        'port': Config_alioth.port_for_online
    }
    try:
        connection = mysql.connector.connect(**db_config_online)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"数据库连接错误: {err}")
        return None

# 1. 保留你原来的数据获取函数 (作为工具函数)
def fetch_all_display_names():
    """从数据库获取所有的 identifier 和 display_name。(这是一个工具函数)"""
    connection = get_db_connection()
    if not connection:
        # 对于 API，直接返回错误信息可能比返回 None 更好处理
        return None, "数据库连接失败"
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT identifier, display_name FROM AliothJobExample ORDER BY display_name"
        cursor.execute(query)
        results = cursor.fetchall()
        return results, None # 返回数据 和 错误信息(None代表无错误)
    except mysql.connector.Error as err:
        logging.error(f"获取 display_name 列表时出错: {err}")
        return None, f"数据库查询错误: {err}"
    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()

def show_templates_page():
    """
    路由函数 1: 只获取所有模板名称列表，并渲染显示页面的 HTML 骨架和列表。
    用户应该首先访问这个路由对应的 URL。
    """
    # 1. 只获取所有模板名称列表
    available_templates, error_msg_names = fetch_all_display_names()
    if error_msg_names:
        flash(f"加载模板列表时出错: {error_msg_names}", "error")
        available_templates = []

    # 2. 渲染 HTML 模板，只传递列表数据
    #    此时没有选中的 display_name，也没有 template_content
    return render_template(
        'alioth_example.html',  # 指向你的 HTML 文件名
        available_templates=available_templates,
        display_name=None,
        template_content=None
    )

# 1. 保留你原来的数据获取函数 (作为工具函数)
def fetch_template_by_name(display_name):
    """根据 display_name 获取模板内容。(这是一个工具函数)"""
    if not display_name:
         return None, "未提供 display_name" # 这个检查在视图函数层做更合适

    connection = get_db_connection()
    if not connection:
        return None, "数据库连接失败"
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT template FROM AliothJobExample WHERE display_name = %s LIMIT 1"
        cursor.execute(query, (display_name,))
        result = cursor.fetchone()
        if result:
            return result['template'], None # 返回模板内容 和 错误信息(None)
        else:
            # 返回具体的未找到错误
            return None, f"未找到名为 '{display_name}' 的模板"
    except mysql.connector.Error as err:
        logging.error(f"查询模板 '{display_name}' 时出错: {err}")
        return None, f"数据库查询错误: {err}"
    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()

def view_specific_template():
    """
    路由函数 2: 当用户在页面上选择了模板并点击“查看”后，此函数被调用。
    它获取具体的模板内容，并重新渲染页面以显示所有信息。
    """
    # 1. 从 URL 查询参数获取用户选择的 display_name
    selected_display_name = request.args.get('display_name')

    # 2. 检查用户是否真的选择了 (如果 display_name 参数不存在或为空)
    if not selected_display_name:
        flash("请先选择一个模板再点击查看。", "view_status")
        # 重定向回初始列表页面通常是更好的用户体验
        return redirect(url_for('show_templates_page')) # 假设 'show_templates_page' 是路由1的端点名

    # 3. 获取选定模板的内容
    template_content, error_msg_template = fetch_template_by_name(selected_display_name)
    if error_msg_template:
        flash(f"{error_msg_template}", "view_status")
        template_content = None # 获取失败则内容为空

    # 4. !! 重要：重新渲染页面时，仍需包含完整的模板列表 !!
    #    否则下拉列表在页面刷新后会是空的。
    available_templates, error_msg_names = fetch_all_display_names()
    if error_msg_names:
        flash(f"重新加载模板列表时出错: {error_msg_names}", "error")
        available_templates = []
        # 考虑在这种情况下是否也应该清除 template_content
        # template_content = None

    # 5. 渲染同一个 HTML 模板，但这次传入所有数据
    return render_template(
        'alioth_example.html',  # 指向你的 HTML 文件名
        available_templates=available_templates, # 再次传递列表
        display_name=selected_display_name,      # 传递选中的名称，用于在下拉框中保持选中
        template_content=template_content        # 传递获取到的模板内容
    )

