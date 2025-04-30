CREATE TABLE `AliothJobExample` (
  `zzid` bigint(20) NOT NULL AUTO_INCREMENT,
  `namespace` varchar(255) NOT NULL COMMENT '命名空间',
  `identifier` varchar(255) NOT NULL COMMENT '唯一标识符',
  `display_name` varchar(255) NOT NULL COMMENT '名字',
  `template` longtext NOT NULL COMMENT '文法',
  `description` longtext NOT NULL COMMENT '作业典例描述',
  `create_user` varchar(255) NOT NULL COMMENT '创建人',
  `modify_user` varchar(255) NOT NULL COMMENT '最后修改人',
  `updatetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `newdate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `source` varchar(511) NOT NULL DEFAULT '[]',
  `sink` varchar(511) NOT NULL DEFAULT '[]',
  `udf` varchar(511) NOT NULL DEFAULT '[]',
  PRIMARY KEY (`zzid`) /*T![clustered_index] CLUSTERED */,
  UNIQUE KEY `id` (`identifier`),
  KEY `display_name` (`display_name`),
  KEY `updatetime` (`updatetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=210001