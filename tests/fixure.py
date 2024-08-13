# -*- coding: utf-8 -*-

import sys, unittest
import settings
sys.path.insert(0, settings.PROJECT_SRC_DIR)
from rdmysql3 import Database, Table
Database.configures.update(settings.MYSQL_CONFS)


class UserProfile(Table):
    __dbkey__ = "default"
    __tablename__ = settings.TEST_TABLE_NAME


class TestBase(unittest.TestCase):

    model = UserProfile()

    @classmethod
    def setUpClass(cls):
        """ Create table """
        cls.model.db.execute_write(settings.TEST_CREATE_TABLE_SQL)
        cls.model.delete(truncate=True)

    @classmethod
    def tearDownClass(cls):
        """ Drop table """
        # cls.model.db.execute_write("DROP TABLE " + settings.TEST_TABLE_NAME)
        cls.printAllSQL(reset=True)

    @classmethod
    def printAllSQL(cls, reset=False):
        """ print all SQL """
        # print("\nSQL List:")
        # for sql in cls.model.db.sqls:
        #     print(sql + ";")
        if reset:
            cls.model.db.sqls = []
