import json

# 得到对应数据库类型的所有source字典
# 传入 flink作业流（json格式）  数据库类型
# 返回该数据库类型的sources的列表
def get_dbtype_sources(json_data, db_type):
    db_type_lower = db_type.lower()  # 将 db_type 转为小写
    return [source for source in json_data['sources'] if source['type'].lower() == db_type_lower]

# 得到对应数据库类型的所有sinks字典
# 传入 flink作业流（json格式）  数据库类型
# 返回该数据库类型的sinks的列表
def get_dbtype_sinks(json_data, db_type):
    db_type_lower = db_type.lower()  # 将 db_type 转为小写
    return [sink for sink in json_data['sinks'] if sink['type'].lower() == db_type_lower]

# 把除了sources sinks 和 udfs 三个key值之外的其他key值包装成一个字典
# 传入 flink作业流（json格式）  keys的列表,比如keys = ['sources', 'sinks', 'udfs']
# 返回一个字典
def get_basic_keys(json_data):
    new_dict = {}
    for i in json_data.keys():
        if i not in ['sources', 'sinks', 'udfs']:
            new_dict[i] = json_data[i]
    return new_dict

# 得到对应udf类型的所有udfs字典
# 传入 flink作业流（json格式）  udf类型
# 返回该udf类型的udfs的列表
def get_udfs(json_data, udf_type):
    udfs_list = []
    udfs = json_data.get('udfs', [])
    # 处理 udfs，udfs 有两种形式 [[{},{}],[{}]] 还有[{},{}]
    for udf in udfs:
        if isinstance(udf, list):
            for ud in udf:
                if ud.get('udf.type', '').lower() == udf_type.lower():
                    udfs_list.append(ud)
        else:
            if udf.get('udf.type', '').lower() == udf_type.lower():
                udfs_list.append(udf)
    return udfs_list

# 提取udfs中的GroupAggWindow算子，特殊处理key.names、wraps和JavaScript算子，特殊处理code
def get_special_key_in_udfs(json_data):
    udfs = json_data.get('udfs', [])
    key_names = []
    wraps = []
    javascripts = []
    whole = []
    for udf in udfs:
        if isinstance(udf, list):
            for ud in udf:
                if ud.get('udf.type', '').lower() == 'groupaggwindow':
                    key_names.extend(ud.get('key.names', []))
                    wraps.extend(ud.get('wraps', []))
                if ud.get('udf.type', '').lower() == 'javascript':
                    javascripts.append(ud.get('code', ''))
        else:
            if udf.get('udf.type', '').lower() == 'groupaggwindow':
                key_names.extend(udf.get('key.names', []))
                wraps.extend(udf.get('wraps', []))
            if udf.get('udf.type', '').lower() == 'javascript':
                javascripts.append(udf.get('code', ''))
    whole.append(key_names)
    whole.append(wraps)
    whole.append(javascripts)
    return whole

# 提取出所有的parser中的selectors
# 传入 flink作业流（json格式）
# 返回所有的parser中的selectors/filters/post_filters的列表 列表当中包含了所有出现过的值 [{},{},{},{}] 里面一个一个的全是selectors/filters/post_filters
def get_special_element(json_data, type_in_parser):
    selectors = []
    for i in json_data.keys():
        if i == 'parser':
            for j in json_data[i].keys():
                if j == type_in_parser:
                    selectors.extend(json_data[i][j])
    return selectors

# 得到所有的type名称以及从出现的次数以备不时之需
# 传入一个special_element的列表 [{},{},{},{}] 里面一个一个的全是selectors/filters/post_filters
# 返回一个字典 记录每个type的出现次数
def get_all_type(special_element_list):
    special_element_dict = {}
    for i in special_element_list:
        if i.get('type') not in special_element_dict:
            special_element_dict[i.get('type')] = 1
        else:
            special_element_dict[i.get('type')] += 1
    return special_element_dict

# 统计 sources sinks udfs basic_keys 列表当中某一个key值的value可能值
# 传入 sources列表 要统计分布的key值
# 传出列表 : 对应key值所有的可能值
def get_times(sources, key = None):
    key_count = []
    for source in sources:
        # 使用 '/' 分割键来处理多层嵌套
        key_parts = key.split('/') if key else []
        # 获取最外层键对应的值
        i = source.get(key_parts[0]) if key_parts else None
        # 逐级进入字典的嵌套结构
        for part in key_parts[1:]:
            if isinstance(i, dict):
                i = i.get(part)
            else:
                i = None
                break
        if i not in key_count and i is not None:
            key_count.append(i)
    return key_count

# 统计传入的sources\sinks\udfs\basic_keys列表的key值交集
# 传入sources的列表
# 传出key值交集
def get_properties_intersection(sources):
    if not sources:
        return set()
    # 递归提取字典中的键，包括嵌套的字典
    def extract_keys(source, prefix=""):
        keys = set()
        for key, value in source.items():
            # 处理嵌套字典的情况
            if isinstance(value, dict):
                # 为嵌套的字典键添加当前的前缀
                nested_keys = extract_keys(value, prefix=f"{prefix}{key}/")
                # 更新键集，确保层级关系的正确表达
                keys.update(f"{k}" for k in nested_keys)
            else:
                # 对于非字典类型，直接加入键名
                keys.add(f"{prefix}{key}")
        return keys
    # 获取第一个 source 的属性集合
    common_properties = extract_keys(sources[0])
    # 依次与其他 source 的属性集合求交集
    for source in sources[1:]:
        common_properties &= extract_keys(source)
    return common_properties


# 统计传入的sources\sinks\udfs\basic_keys列表的key值交集
# 传入sources的列表
# 传出key值并集
def get_properties_union(sources):
    if not sources:
        return set()
    # 递归提取字典中的键，包括嵌套的字典
    def extract_keys(source, prefix=""):
        keys = set()
        for key, value in source.items():
            # 处理嵌套字典的情况
            if isinstance(value, dict):
                # 为嵌套的字典键添加当前的前缀
                nested_keys = extract_keys(value, prefix=f"{prefix}{key}/")
                # 更新键集，确保层级关系的正确表达
                keys.update(f"{k}" for k in nested_keys)
            else:
                # 对于非字典类型，直接加入键名
                keys.add(f"{prefix}{key}")
        return keys
    # 初始化一个空的集合用于存放并集
    all_properties = set()
    # 依次将每个 source 的属性集合加入并集
    for source in sources:
        all_properties |= extract_keys(source)
    return all_properties

# 专属于GroupAggWindow算子，特殊处理key.names
def generate_intersection_template(list_of_lists, number):
    return_list = []
    relationship = {}
    # 获取所有列表中的出现次数大于5的键
    for item in list_of_lists:
        item = json.dumps(item)
        if item in relationship:
            relationship[item] += 1
        else:
            relationship[item] = 1
    for key, value in relationship.items():
        if value >= number:
            return_list.append(json.loads(key))
    return return_list

# 专属于GroupAggWindow算子，特殊处理key.names,也可以给wraps使用，都是可以的
def generate_union_template(list_of_lists):
    return_list = []
    relationship = {}
    # 获取所有列表中的出现次数大于5的键
    for item in list_of_lists:
        item = json.dumps(item)
        if item in relationship:
            relationship[item] += 1
        else:
            relationship[item] = 1
    for key, value in relationship.items():
        return_list.append(json.loads(key))
    return return_list

# 还要写两个专门属于javascript的函数，交集，先用分号分割为列表做比较，如果没有就用字符串来比较
def generate_intersection_template_for_javascript(list_of_lists):
    # 先再创一个以;分割的列表
    return_list = []
    new_list = []
    for i in list_of_lists:
        new_list.append(tuple(i.split(';')))

    sentences = {}
    # 获取所有列表中的出现次数大于5的键
    for item in new_list:
        if item in sentences:
            sentences[item] += 1
        else:
            sentences[item] = 1
    for key, value in sentences.items():
        if value >= 3:
            # 再拼接回来
            str = ''
            for i in key:
                str += i + ';'
            return_list.append(str)


    new_list2 = []
    sentences2 = {}
    # 将不在sentences中的元素加入
    for i in list_of_lists:
        j = tuple(i.split(';'))
        if sentences[j] < 3:
            new_list2.extend(i.split(';'))
    for item in new_list2:
        if item in sentences2:
            sentences2[item] += 1
        else:
            sentences2[item] = 1

    str = ''
    for key, value in sentences2.items():
        if value >= 3:
            str += key + ';'
    return_list.append(str)
    return return_list
