class Config_users:
    """
    配置用户登录的数据库信息
    创表代码：create.sql
    """
    MYSQL_HOST = 'localhost'  # 数据库的实例名
    MYSQL_DATABASE = 'ops'  # 数据库的名称
    MYSQL_USER = 'user_name'  # 数据库的用户名
    MYSQL_PASSWORD = 'your_password'  # 数据库的密码


class Config_lock:
    """
    配置锁表的数据库的信息
    创表代码：backUp_module/create.sql
    """
    MYSQL_HOST = 'localhost'  # 锁表的实例名
    MYSQL_DATABASE = 'ops'  # 锁表所在的数据库的名称
    MYSQL_USER = 'user_name'  # 锁表所在的数据库的用户名
    MYSQL_PASSWORD = 'your_password'  # 锁表所在的数据库的密码
    MYSQL_PORT = 3306  # 锁表所在的数据库的端口号

    # 邮箱配置
    EMAIL_PORT = 587  # 邮箱端口号
    EMAIL_HOST = 'smtp.example.com'  # 邮箱服务器地址
    EMAIL_USER = 'example@example.com'  # 你的邮箱地址
    EMAIL_PASS = 'your_email_app_password'  # 邮箱授权码
    ALERT_EMAIL = 'alert@example.com'  # 告警邮箱地址


class Config_DLM:
    """
    配置存储数据血缘关系的数据库的信息
    创表代码：dlm_module/create.sql
    """
    host = 'localhost'
    user = 'user_name'
    password = 'your_password'
    port = 3306
    database = 'ops'
    config_fn = ['config.py', 'conf.py']


class Config_alioth:
    """
    配置alioth线上作业存储位置和保存作业典范的数据库信息
    """
    # alioth线上作业的存储位置的数据库信息
    host = '127.0.0.1'
    user = 'user_name'
    password = 'your_password'
    port = 3306
    database = 'ops'
    table_name = 'flink_jobs_2'  # alioth线上作业表名
    field1 = 'start_param'  # 启动参数
    field2 = 'remote_actual_name'  # 每个流的标识符

    len_for_values = 5  # 控制输出长度，定义出现次数不多于多少为“可枚举的”
    times_for_grammer = 10  # 第一次筛选时出现次数阈值
    times_for_grammer_2 = 10  # 第二次筛选时出现次数阈值

    # 保存作业典范的数据库信息
    # 创表代码：alioth_module/create.sql
    user_for_online = "user_name"
    password_for_online = "your_password"
    host_for_online = "localhost"
    port_for_online = 3306
    database_for_online = "ops"
    table_name_for_online = "AliothJobExample"
    namespace = "namespace_placeholder"
    create_user = "your_email@example.com"
    modify_user = "your_email@example.com"

    # 替换 value 值规则
    before1 = 'True, False//bool'
    after1 = 'true, false'
    before2 = 'False, True//bool'
    after2 = 'false, true'
    before3 = 'False//bool'
    after3 = 'false'
    before4 = 'True//bool'
    after4 = 'true'
    # before5 = 'None//bool'
    # after5 = 'None'
