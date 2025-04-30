CREATE TABLE `data_flow_new` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `url` varchar(100) NOT NULL COMMENT '存储 git地址',
  `script` varchar(100) NOT NULL COMMENT '存储脚本路径和信息',
  `source_instance` varchar(50) NOT NULL COMMENT '存储源实例信息',
  `source_db` varchar(50) NOT NULL COMMENT '存储源库',
  `source_table` varchar(50) NOT NULL COMMENT '存储源表',
  `target_instance` varchar(50) NOT NULL COMMENT '存储目标实例信息',
  `target_db` varchar(50) NOT NULL COMMENT '存储源库',
  `target_table` varchar(50) NOT NULL COMMENT '存储目标表',
  `metric` varchar(50) NULL COMMENT '存储指标信息',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`url`, `script`,  `source_instance`, `source_db`,`source_table`, `target_instance`, `target_db`,`target_table`),
  UNIQUE KEY `unique_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='记录数据流的表'