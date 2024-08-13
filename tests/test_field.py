# -*- coding: utf-8 -*-

import unittest
import fixure, settings


class TestField(fixure.TestBase):

    def test_01_table_name(self):
        table = self.model.get_table_name()
        self.assertEqual(settings.TEST_TABLE_NAME, table)

    def test_02_table_info(self):
        info = self.model.get_table_info()
        self.assertEqual(settings.TEST_TABLE_NAME, info["TABLE_NAME"])
        self.assertEqual(0, info["TABLE_ROWS"])

    def test_03_table_fields(self):
        fs = [
            {"name":"id", "type":"int(10) unsigned"},
            {"name":"username", "type":"varchar(30)"},
            {"name":"nickname", "type":"varchar(50)"},
            {"name":"gender", "type":"enum('M','F','X')"},
            {"name":"avatar", "type":"varchar(200)"},
            {"name":"mobile", "type":"char(16)"},
            {"name":"birthday", "type":"char(10)"},
            {"name":"changed_at", "type":"timestamp"},
        ]
        fields = self.model.get_table_fields()
        self.assertEqual(len(fs), len(fields))
        for i in range(len(fields)):
            self.assertEqual(fs[i]["name"], fields[i]["COLUMN_NAME"])
            self.assertEqual(fs[i]["type"], fields[i]["COLUMN_TYPE"])
