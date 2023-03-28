# -*- coding: utf-8 -*-

import os.path

PROJECT_DIR = os.path.realpath(os.path.dirname(__file__))

MYSQL_CONFS = {
    "user": {  # 用户库
        "drivername": "mysql+mysqldb",
        "host": "127.0.0.1",
        "port": 3306,
        "database": "db_test",
        "username": "dba",
        "password": "**pass**",
        "charset": "utf8",
    },
}

"""
-- Table `t_user_profiles`
CREATE TABLE `t_user_profiles` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL DEFAULT '' COMMENT '用户名',
  `nickname` varchar(50) NOT NULL DEFAULT '' COMMENT '昵称',
  `gender` enum('M','F','X') NOT NULL DEFAULT 'X' COMMENT '性别',
  `avatar` varchar(200) DEFAULT NULL COMMENT '头像',
  `mobile` char(16) DEFAULT NULL COMMENT '手机号',
  `birthday` char(10) DEFAULT NULL COMMENT '出生日期',
  `changed_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`) USING BTREE,
  KEY `changed_at` (`changed_at`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户资料表';
"""
