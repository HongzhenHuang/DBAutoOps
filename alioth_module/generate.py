import re
import json
import mysql.connector
from config import Config_alioth
from extract import get_dbtype_sources, generate_intersection_template_for_javascript, get_dbtype_sinks, get_udfs, get_basic_keys, get_times, generate_intersection_template,  get_properties_intersection, get_properties_union, get_special_element, get_all_type, get_special_key_in_udfs,  generate_union_template, get_properties_intersection, get_properties_union

# 根据提供的sources列表和keys集合生成字典
# sources当中全部都是一种type了
# 传入 sources的列表  keys集合
# 传出 字典
def generate_json_model_sources(sources, keys):
    # 初始化空的 JSON 结构
    source_template = {}
    # 初始化空的嵌套模板
    nested_templates = {}

    # 递归设置嵌套字典
    def set_nested_key(template, key_path, value):
        # 将嵌套路径通过 '/' 分割为多层键
        keys = key_path.split('/')
        current = template
        for k in keys[:-1]:  # 处理中间层次的键
            if k not in current:
                current[k] = {}
            current = current[k]
        # 最后一层键赋值
        current[keys[-1]] = value

    # 动态创建 JSON 结构
    for key in keys:
        # 检查是否为嵌套属性
        if '/' in key:
            # 使用 '/' 分割主键和子键
            if get_times(sources, key) is None:
                if type(get_times(sources, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(sources, key)[0]).__name__}')
            elif len(get_times(sources, key)) <= Config_alioth.len_for_values:
                if type(get_times(sources, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, ', '.join(str(count) for count in get_times(sources, key)))
                elif type(get_times(sources, key)[0]).__name__ == 'list':
                    set_nested_key(nested_templates, key, [ i for i in get_times(sources, key)])
                else:
                    set_nested_key(nested_templates, key, (', '.join(str(count) for count in get_times(sources, key))) + ('//'+type(get_times(sources, key)[0]).__name__))
            else:
                if type(get_times(sources, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(sources, key)[0]).__name__}')
        else:
            if get_times(sources, key) is None:
                if type(get_times(sources, key)[0]).__name__ == 'str' :
                    source_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    source_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(sources, key)[0]).__name__}'
            elif len(get_times(sources, key)) <= Config_alioth.len_for_values:
                if type(get_times(sources, key)[0]).__name__ == 'str' :
                    source_template[key] = (', '.join(str(count) for count in get_times(sources, key)))
                elif type(get_times(sources, key)[0]).__name__ == 'list':
                    source_template[key] = [ i for i in get_times(sources, key)]
                else:
                    source_template[key] = (', '.join(str(count) for count in get_times(sources, key))) + ('//' + type(get_times(sources, key)[0]).__name__)
            else:
                if type(get_times(sources, key)[0]).__name__ == 'str' :
                    source_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    source_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(sources, key)[0]).__name__}'
    # 将嵌套模板添加到源模板中
    for main_key, props in nested_templates.items():
        source_template[main_key] = props
    return source_template


# 根据提供的sinks列表和keys集合生成字典
# sinks当中全部都是一种type了
# 传入 sinks的列表  keys集合
# 传出 字典
def generate_json_model_sinks(sinks, keys):
    # 初始化空的 JSON 结构
    sink_template = {}
    # 初始化空的嵌套模板
    nested_templates = {}

    # 递归设置嵌套字典
    def set_nested_key(template, key_path, value):
        # 将嵌套路径通过 '/' 分割为多层键
        keys = key_path.split('/')
        current = template
        for k in keys[:-1]:  # 处理中间层次的键
            if k not in current:
                current[k] = {}
            current = current[k]
        # 最后一层键赋值
        current[keys[-1]] = value

    # 动态创建 JSON 结构
    for key in keys:
        # 检查是否为嵌套属性
        if '/' in key:
            # 使用 '/' 分割主键和子键
            if get_times(sinks, key) is None:
                if type(get_times(sinks, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(sinks, key)[0]).__name__}')
            elif len(get_times(sinks, key)) <= Config_alioth.len_for_values:
                if type(get_times(sinks, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, ', '.join(str(count) for count in get_times(sinks, key)))
                elif type(get_times(sinks, key)[0]).__name__ == 'list':
                    set_nested_key(nested_templates, key, [ i for i in get_times(sinks, key)])
                else:
                    set_nested_key(nested_templates, key, (', '.join(str(count) for count in get_times(sinks, key))) + ('//'+type(get_times(sinks, key)[0]).__name__))
            else:
                if type(get_times(sinks, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(sinks, key)[0]).__name__}')
        else:
            if get_times(sinks, key) is None:
                if type(get_times(sinks, key)[0]).__name__ == 'str' :
                    sink_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    sink_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(sinks, key)[0]).__name__}'
            elif len(get_times(sinks, key)) <= Config_alioth.len_for_values:
                if type(get_times(sinks, key)[0]).__name__ == 'str' :
                    sink_template[key] = (', '.join(str(count) for count in get_times(sinks, key)))
                elif type(get_times(sinks, key)[0]).__name__ == 'list':
                    sink_template[key] = [ i for i in get_times(sinks, key)]
                else:
                    sink_template[key] = (', '.join(str(count) for count in get_times(sinks, key))) + ('//' + type(get_times(sinks, key)[0]).__name__)
            else:
                if type(get_times(sinks, key)[0]).__name__ == 'str' :
                    sink_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    sink_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(sinks, key)[0]).__name__}'

    # 将嵌套模板添加到源模板中
    for main_key, props in nested_templates.items():
        sink_template[main_key] = props
    return sink_template


# 根据提供的udfs列表和keys集合生成包含一个字典的列表
# 传入的udfs列表当中全部都是一种type了
# 传入 udfs的列表  keys集合
# 传出 字典
def generate_json_model_udfs(udfs, keys, list_of_key_names, list_of_wraps, list_of_codes, inter_or_unioin):
    # 初始化空的 JSON 结构
    udfs_template = {}
    # 初始化空的嵌套模板
    nested_templates = {}

    # 递归设置嵌套字典
    def set_nested_key(template, key_path, value):
        # 将嵌套路径通过 '/' 分割为多层键
        keys = key_path.split('/')
        current = template
        for k in keys[:-1]:  # 处理中间层次的键
            if k not in current:
                current[k] = {}
            current = current[k]
        # 最后一层键赋值
        current[keys[-1]] = value

    # 动态创建 JSON 结构
    for key in keys:
        # 检查是否为嵌套属性
        if '/' in key:
            # 使用 '/' 分割主键和子键
            if get_times(udfs, key) is None:
                if type(get_times(udfs, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(udfs, key)[0]).__name__}')
            elif len(get_times(udfs, key)) <= Config_alioth.len_for_values:
                if type(get_times(udfs, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, ', '.join(str(count) for count in get_times(udfs, key)))
                elif type(get_times(udfs, key)[0]).__name__ == 'list':
                    set_nested_key(nested_templates, key, [ i for i in get_times(udfs, key)])
                else:
                    set_nested_key(nested_templates, key, (', '.join(str(count) for count in get_times(udfs, key))) + ('//'+type(get_times(udfs, key)[0]).__name__))
            else:
                if type(get_times(udfs, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(udfs, key)[0]).__name__}')
        else:
            if get_times(udfs, key) is None:
                if type(get_times(udfs, key)[0]).__name__ == 'str' :
                    udfs_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    udfs_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(udfs, key)[0]).__name__}'
            elif len(get_times(udfs, key)) <= Config_alioth.len_for_values:
                if type(get_times(udfs, key)[0]).__name__ == 'str' :
                    udfs_template[key] = (', '.join(str(count) for count in get_times(udfs, key)))
                elif type(get_times(udfs, key)[0]).__name__ == 'list':
                    udfs_template[key] = [ i for i in get_times(udfs, key)]
                else:
                    udfs_template[key] = (', '.join(str(count) for count in get_times(udfs, key)))+ ('//' + type(get_times(udfs, key)[0]).__name__)
            else:
                if type(get_times(udfs, key)[0]).__name__ == 'str' :
                    udfs_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    udfs_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(udfs, key)[0]).__name__}'
    # 将嵌套模板添加到源模板中
    for main_key, props in nested_templates.items():
        udfs_template[main_key] = props

    # 记录需要更新的项
    updates = {}

    for key, value in udfs_template.items():
        # 再添加一次判断，如果udfs的type为GroupAggWindow算子，特殊处理key.names
        if key == 'udf.type' and value == 'GroupAggWindow' and inter_or_unioin == 'intersection':
            updates['key.names'] = generate_intersection_template(list_of_key_names,5)
        if key == 'udf.type' and value == 'GroupAggWindow' and inter_or_unioin == 'union':
            updates['key.names'] = generate_union_template(list_of_key_names)

        # 再添加一次判断，如果udfs的type为GroupAggWindow算子，特殊处理wraps
        if key == 'udf.type' and value == 'GroupAggWindow' and inter_or_unioin == 'intersection':
            updates['wraps'] = generate_intersection_template(list_of_wraps, 2)
        if key == 'udf.type' and value == 'GroupAggWindow' and inter_or_unioin == 'union':
            updates['wraps'] = generate_union_template(list_of_wraps)

        # 再添加一次判断，如果udfs的type为javascript算子，特殊处理code
        if key == 'udf.type' and value == 'JavaScript' and 'code' in udfs_template.keys():
            updates['code'] = generate_intersection_template_for_javascript(list_of_codes)
    # 统一进行更新
    udfs_template.update(updates)

    return udfs_template

# 根据提供的basic列表和keys集合生成字典
# 传入 basic的列表  keys集合
# 传出 字典
def generate_json_model_basic(basic, keys):
    # 初始化空的 JSON 结构
    basic_template = {}
    # 初始化空的嵌套模板
    nested_templates = {}

    # 递归设置嵌套字典
    def set_nested_key(template, key_path, value):
        # 将嵌套路径通过 '/' 分割为多层键
        keys = key_path.split('/')
        current = template
        for k in keys[:-1] :  # 处理中间层次的键
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        # 最后一层键赋值
        current[keys[-1]] = value

    # 动态创建 JSON 结构
    for key in keys:
        # 检查是否为嵌套属性
        if '/' in key:
            # 使用 '/' 分割主键和子键
            if get_times(basic, key) is None:
                if type(get_times(basic, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(basic, key)[0]).__name__}')
            elif len(get_times(basic, key)) <= Config_alioth.len_for_values:
                if type(get_times(basic, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, ', '.join(str(count) for count in get_times(basic, key)))
                elif type(get_times(basic, key)[0]).__name__ == 'list':
                    set_nested_key(nested_templates, key, [ i for i in get_times(basic, key)])
                else:
                    set_nested_key(nested_templates, key, (', '.join(str(count) for count in get_times(basic, key)))+ ('//'+type(get_times(basic, key)[0]).__name__))
            else:
                if type(get_times(basic, key)[0]).__name__ == 'str' :
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}')
                else:
                    set_nested_key(nested_templates, key, f'{{__{key.split("/")[-1]}__}}//{type(get_times(basic, key)[0]).__name__}')
        else:
            if get_times(basic, key) is None:
                if type(get_times(basic, key)[0]).__name__ == 'str' :
                    basic_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    basic_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(basic, key)[0]).__name__}'
            elif len(get_times(basic, key)) <= Config_alioth.len_for_values:
                if type(get_times(basic, key)[0]).__name__ == 'str' :
                    basic_template[key] = (', '.join(str(count) for count in get_times(basic, key)))

                elif type(get_times(basic, key)[0]).__name__ == 'list':
                    basic_template[key] = [ i for i in get_times(basic, key)]
                else:
                    basic_template[key] = (', '.join(str(count) for count in get_times(basic, key))) + ('//' + type(get_times(basic, key)[0]).__name__)
            else:
                if type(get_times(basic, key)[0]).__name__ == 'str' :
                    basic_template[key] = f'{{__{key.split("/")[-1]}__}}'
                else:
                    basic_template[key] = f'{{__{key.split("/")[-1]}__}}//{type(get_times(basic, key)[0]).__name__}'
    # 将嵌套模板添加到源模板中
    for main_key, props in nested_templates.items():
        basic_template[main_key] = props
    # 包装成最终的 JSON 结构
    return basic_template



# 传入一个special_element的列表
# 返回一个json模板的列表
# 用于在parser的基础上进行拼接
def generate_json_model_basic_special_element(special_element_list, inter_or_union):
    # 所有的type的名字
    all_type_names = get_all_type(special_element_list)
    list0 = []
    for i in all_type_names.keys():
        list1 = []
        for j in special_element_list:
            if j.get('type') == i:
                list1.append(j)
        if inter_or_union == 'intersection':
            list0.append(generate_json_model_basic(list1, get_properties_intersection(list1)))
        elif inter_or_union == 'union':
            list0.append(generate_json_model_basic(list1, get_properties_union(list1)))
    return list0


# 要实现一个函数，传入type名就能输出模板
def output_json_grammar_based_on_type_sources(type_name, inter_or_union):
    # 数据库连接信息
    db_config = {'user': Config_alioth.user, 'password': Config_alioth.password, 'host': Config_alioth.host, 'database': Config_alioth.database, 'charset': 'utf8mb4'}
    # 连接到数据库
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    # 查询数据
    select_query = f"SELECT {Config_alioth.field1} FROM {Config_alioth.table_name}"
    cursor.execute(select_query)
    # 指定数据库类型
    target = type_name
    # sources和sinks列表
    dbtype_sources = []
    # 加载和处理JSON数据
    for (job_data,) in cursor.fetchall():
        try:
            job_data = re.sub(r'--template\s+', '', job_data)
            # json_data是字典
            json_data = json.loads(json.loads(job_data))
            dbtype_sources.extend(get_dbtype_sources(json_data, target))
        except json.JSONDecodeError:
            print("Error decoding JSON")
    # 关闭游标和连接
    cursor.close()
    connection.close()
    # 对于sources
    # 获取属性的交集
    if inter_or_union == 'intersection':
        intersecting_properties = get_properties_intersection(dbtype_sources)
        return generate_json_model_sources(dbtype_sources, intersecting_properties)
    elif inter_or_union == 'union':
        union_properties = get_properties_union(dbtype_sources)
        return generate_json_model_sources(dbtype_sources, union_properties)


# 要实现一个函数，传入type名就能输出模板
def output_json_grammar_based_on_type_sinks(type_name, inter_or_union):
    # 数据库连接信息
    db_config = {'user': Config_alioth.user, 'password': Config_alioth.password, 'host': Config_alioth.host, 'database': Config_alioth.database, 'charset': 'utf8mb4'}
    # 连接到数据库
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    # 查询数据
    select_query = f"SELECT {Config_alioth.field1} FROM {Config_alioth.table_name}"
    cursor.execute(select_query)
    # 指定数据库类型
    target = type_name
    # sources和sinks列表
    dbtype_sinks = []
    # 加载和处理JSON数据
    for (job_data,) in cursor.fetchall():
        try:
            job_data = re.sub(r'--template\s+', '', job_data)
            # json_data是字典
            json_data = json.loads(json.loads(job_data))
            dbtype_sinks.extend(get_dbtype_sinks(json_data, target))
        except json.JSONDecodeError:
            print("Error decoding JSON")
    # 关闭游标和连接
    cursor.close()
    connection.close()
    # 对于sinks
    # 获取属性的交集
    if inter_or_union == 'intersection':
        intersecting_properties = get_properties_intersection(dbtype_sinks)
        return generate_json_model_sinks(dbtype_sinks, intersecting_properties)
    elif inter_or_union == 'union':
        union_properties = get_properties_union(dbtype_sinks)
        return generate_json_model_sinks(dbtype_sinks, union_properties)

# 要实现一个函数，传入type名就能输出模板
def output_json_grammar_based_on_type_udfs(type_name, inter_or_union):
    # 数据库连接信息
    db_config = {'user': Config_alioth.user, 'password': Config_alioth.password, 'host': Config_alioth.host, 'database': Config_alioth.database, 'charset': 'utf8mb4'}
    # 连接到数据库
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    # 查询数据
    select_query = f"SELECT {Config_alioth.field1} FROM {Config_alioth.table_name}"
    cursor.execute(select_query)

    # 指定udfs类型
    target = type_name

    # udfs列表
    udfs_list = []

    # 还要添加三个特殊列表
    key_names = []
    wraps = []
    javascripts = []
    # 加载和处理JSON数据
    for (job_data,) in cursor.fetchall():
        try:
            job_data = re.sub(r'--template\s+', '', job_data)
            # json_data是字典
            json_data = json.loads(json.loads(job_data))
            udfs_list.extend(get_udfs(json_data, target))
            key_names.extend(get_special_key_in_udfs(json_data)[0])
            wraps.extend(get_special_key_in_udfs(json_data)[1])
            javascripts.extend(get_special_key_in_udfs(json_data)[2])
        except json.JSONDecodeError:
            print("Error decoding JSON")
    # 关闭游标和连接
    cursor.close()
    connection.close()
    # 对于udfs
    # 获取属性的交集
    if inter_or_union == 'intersection':
        intersecting_properties = get_properties_intersection(udfs_list)
        return generate_json_model_udfs(udfs_list, intersecting_properties, key_names, wraps, javascripts, 'intersection')
    elif inter_or_union == 'union':
        union_properties = get_properties_union(udfs_list)
        return generate_json_model_udfs(udfs_list, union_properties, key_names, wraps, javascripts, 'union')

# 要实现一个函数，传入type名就能输出模板
def output_json_grammar_based_on_type_basic(inter_or_union):
    # 数据库连接信息
    db_config = {'user': Config_alioth.user, 'password': Config_alioth.password, 'host': Config_alioth.host, 'database': Config_alioth.database, 'charset': 'utf8mb4'}
    # 连接到数据库
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    # 查询数据
    select_query = f"SELECT {Config_alioth.field1} FROM {Config_alioth.table_name}"
    cursor.execute(select_query)
    key_list = []
    # 加载和处理JSON数据
    for (job_data,) in cursor.fetchall():
        try:
            job_data = re.sub(r'--template\s+', '', job_data)
            # json_data是字典
            json_data = json.loads(json.loads(job_data))
            key_list.append(get_basic_keys(json_data))
        except json.JSONDecodeError:
            print("Error decoding JSON")
    # 关闭游标和连接
    cursor.close()
    connection.close()
    # 对于basic
    # 获取属性的交集
    if inter_or_union == 'intersection':
        intersecting_properties = get_properties_intersection(key_list)
        return generate_json_model_basic(key_list, intersecting_properties)
    elif inter_or_union == 'union':
        union_properties = get_properties_union(key_list)
        return generate_json_model_basic(key_list, union_properties)

# 这个函数直接用于输出parser文法，不再被其他函数调用
def output_json_grammar_based_on_type_special_element(inter_or_union):
    # 数据库连接信息
    db_config = {'user': Config_alioth.user, 'password': Config_alioth.password, 'host': Config_alioth.host, 'database': Config_alioth.database,
                 'charset': 'utf8mb4'}
    # 连接到数据库
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    # 查询数据
    select_query = f"SELECT {Config_alioth.field1} FROM {Config_alioth.table_name}"
    cursor.execute(select_query)
    selectors = []
    filters = []
    post_filters = []
    # 加载和处理JSON数据
    for (job_data,) in cursor.fetchall():
        try:
            job_data = re.sub(r'--template\s+', '', job_data)
            # json_data是字典
            json_data = json.loads(json.loads(job_data))
            selectors.extend(get_special_element(json_data, 'selectors'))
            filters.extend(get_special_element(json_data, 'filters'))
            post_filters.extend(get_special_element(json_data, 'post_filters'))
        except json.JSONDecodeError:
            print("Error decoding JSON")
    # 关闭游标和连接
    cursor.close()
    connection.close()
    # 对于basic
    # 获取属性的交集
    if inter_or_union == 'intersection':
        # 字典 只提取精简的属性 即parser
        origin_parser = output_json_grammar_based_on_type_basic('union').get('parser')

        if origin_parser is not None:
            if 'selectors' in origin_parser.keys():
                origin_parser['selectors'] = generate_json_model_basic_special_element(selectors, 'intersection')
            if 'filters' in origin_parser.keys():
                origin_parser['filters'] = generate_json_model_basic_special_element(filters, 'intersection')
            if 'post_filters' in origin_parser.keys():
                origin_parser['post_filters'] = generate_json_model_basic_special_element(post_filters, 'intersection')
        return json.dumps(origin_parser)

    elif inter_or_union == 'union':
        # 字典 只提取精简的属性 即parser
        origin_parser = output_json_grammar_based_on_type_basic('union').get('parser')

        if origin_parser is not None:
            if 'selectors' in origin_parser.keys():
                origin_parser['selectors'] = generate_json_model_basic_special_element(selectors, 'union')
            if 'filters' in origin_parser.keys():
                origin_parser['filters'] = generate_json_model_basic_special_element(filters, 'union')
            if 'post_filters' in origin_parser.keys():
                origin_parser['post_filters'] = generate_json_model_basic_special_element(post_filters, 'union')
        return json.dumps(origin_parser)


# 根据映射关系输出json文法
def output_json_grammar(relationship, inter_or_union):
    # 创建一个字典来存储json
    json_dict = {}
    for key in relationship.keys():
        my_dict = {}
        sources, udfs, sinks = key.split('->')
        source = sources.split('.')
        udf = udfs.split('/')
        sink = sinks.split('.')
        # 创建一个字典来存储source
        sources_list = []
        for i in source:
            sources_list.append(output_json_grammar_based_on_type_sources(i, inter_or_union))
        sinks_list = []
        for i in sink:
            sinks_list.append(output_json_grammar_based_on_type_sinks(i, inter_or_union))
        udfs_list_1 = []
        for i in udf:
            udfs_list_2 = []
            for j in i.split('.'):
                udfs_list_2.append(output_json_grammar_based_on_type_udfs(j, inter_or_union))
            udfs_list_1.append(udfs_list_2)
        my_dict.update(output_json_grammar_based_on_type_basic(inter_or_union))
        my_dict['sources'] = sources_list
        my_dict['udfs'] = udfs_list_1
        my_dict['sinks'] = sinks_list
        my_dict_json = json.dumps(my_dict)
        json_dict[key] = my_dict_json
    return json_dict