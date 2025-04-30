class Config_users:
    MYSQL_HOST = 'localhost' # 数据库的实例名
    MYSQL_DATABASE = 'ops' # 数据库的名称
    MYSQL_USER = 'hhz' # 数据库的用户名
    MYSQL_PASSWORD = 'Bigben077' # 数据库的密码

class Config_lock:
    """
    以下这些是去配置锁表的数据库的信息
    不是要备份的表的信息
    要备份的表的信息作为参数传入
    表的名称为backup_locks 创建的指令在create.sql中
    """
    MYSQL_HOST = 'localhost' # 锁表的实例名
    MYSQL_DATABASE = 'ops' # 锁表所在的数据库的名称
    MYSQL_USER = 'hhz' # 锁表所在的数据库的用户名
    MYSQL_PASSWORD = 'Bigben077' # 锁表所在的数据库的密码
    MYSQL_PORT = '3306' # 锁表所在的数据库的端口号
    EMAIL_PORT = 587 # 邮箱端口号
    EMAIL_HOST = 'smtp.qq.com' # 邮箱服务器地址
    EMAIL_USER = '2713206151@qq.com' # 你的邮箱地址
    EMAIL_PASS = 'pjaoetijfinudfcb' # 你的邮箱授权码
    ALERT_EMAIL = '1070058272@qq.com' # 告警邮箱地址、

class Config_DLM:
    # 以下信息用于配置存储数据血缘关系的数据库
    host = 'localhost'
    user = 'hhz'
    password = 'Bigben077'
    port = 3306
    database = 'ops'
    config_fn = ['config.py', 'conf.py']

class Config_alioth:
    # alioth线上作业位置
    host = '127.0.0.1'
    user = 'hhz'
    password = 'Bigben077'
    port = 3306
    database = 'ops'
    table_name = 'flink_jobs_2' # alioth线上作业表名
    field1 = 'start_param' # 启动参数
    field2 = 'remote_actual_name' # 每个流的标识符

    len_for_values = 5 # 用于控制输出的长度，定义出现次数不多于多少为`可枚举的`
    times_for_grammer = 10 # 在第一次根据第一个udfs算子筛选时，出现次数超过此值的简化的映射关系才会被记录
    times_for_grammer_2 = 10 # 出现次数超过此值的完整的映射关系才会被记录

    # 保存作业典范的在线数据库信息
    user_for_online = "hhz"
    password_for_online = "Bigben077"
    host_for_online = "localhost"
    port_for_online = '3306'
    database_for_online = 'ops'
    table_name_for_online = 'AliothJobExample'
    namespace = 'hongzhenhuang'
    create_user = 'zhongzhenhuang@gmail.com'
    modify_user = 'zhongzhenhuang@gmail.com'

    # 替换value值
    # 开发者可以自行在这里设置替换规则
    # 例如：将value值为'False//bool'的替换为'false'
    # 如果没有需要替换的就不用设置 下方都注释掉
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
