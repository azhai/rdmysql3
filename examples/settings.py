# -*- coding: utf-8 -*-

from os.path import join, dirname

PROJECT_SRC_DIR = join(dirname(dirname(__file__)), 'src')

MYSQL_CONFS = {
    "default": {
        "drivername": "mysql",
        "host": "127.0.0.1",
        "port": 3306,
        "database": "test",
        "username": "root",
        "password": "",
        "charset": "utf8mb4",
    },
}
