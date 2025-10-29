CREATE TABLE IF NOT EXISTS backup_locks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    host VARCHAR(255) NOT NULL COMMENT '主机名',
    database_name VARCHAR(255) NOT NULL COMMENT '数据库名',
    table_name VARCHAR(255) NOT NULL COMMENT '表名',
    pid BIGINT NOT NULL COMMENT '进程号',
    lock_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上锁时间',
    UNIQUE KEY unique_lock (host, database_name, table_name),
    INDEX idx_pid (pid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='备份任务表锁记录';
