# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta
from random import randint, choice
from rdmysql3 import Daily, Row, Expr, iter_query_daily

import fixure

create_sql = """
-- Table `t_user_events`
CREATE TABLE IF NOT EXISTS `t_user_events` (
    `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` int(10) UNSIGNED NOT NULL DEFAULT 0 COMMENT '用ID',
    `username` varchar(30) NOT NULL DEFAULT '' COMMENT '用户名',
    `category` varchar(50) NOT NULL DEFAULT '' COMMENT '类别',
    `content` varchar(500) NULL DEFAULT NULL COMMENT '事件描述',
    `created_at` timestamp NULL DEFAULT NULL COMMENT '发生时间',
    PRIMARY KEY (`id`) USING BTREE,
    INDEX `user_id`(`user_id`) USING BTREE,
    INDEX `created_at`(`created_at`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户事件表'
"""


class UserEvent(Daily):
    __dbkey__ = "default"
    __tablename__ = "t_user_events"


class TestUserProfile(fixure.TestBase):
    event = UserEvent()

    def setUp(self):
        self.event.db.execute_write(create_sql)
        self.event.delete(truncate=True)
        keys = ["user_id", "category", "created_at"]
        cates = ["login", "logout", "browse", "order",
                 "pay", "charge", "refund", "comment"]
        evdata, created_at = {}, datetime(2024, 2, 28, 17, 5)
        for i in range(2717):
            created_at += timedelta(minutes=randint(1, 5))
            evdate = created_at.date()
            if evdate not in evdata:
                evdata[evdate] = []
            evdata[evdate].append([1, choice(cates), created_at])
        for evdate, rows in evdata.items():
            self.event.set_date(evdate).create_table(truncate=True)
            self.event.insert_chunks(keys, rows)

    def tearDown(self):
        """ print all SQL """
        # print("\nSQL List:")
        # for sql in self.event.db.sqls:
        #     print(sql + ";")
        self.event.db.sqls = []

    def test_01_iter_all(self):
        def query_all(model):
            q = model.filter_by(category="login").order_by("id", "DESC")
            return q.all(model=Row, reset=True)

        self.event.set_date(date(2024, 3, 3))
        rows = iter_query_daily(self.event, query_all,
                                stop=date(2024, 3, 1), fuse=True)
        # 大约200行
        self.assertLessEqual(100, len(rows))
        self.assertGreaterEqual(300, len(rows))
        # 第一条在2024-03-03 23:00以后
        first_row = rows[0]
        self.assertEqual(date(2024, 3, 3), first_row.created_at.date())
        self.assertIn(first_row.created_at.hour, [23, 22])
        # 最后一条在2024-03-01 00:00以后
        last_row = rows[-1]
        self.assertEqual(date(2024, 3, 1), last_row.created_at.date())
        self.assertIn(last_row.created_at.hour, [0, 1])

    def test_02_iter_cate(self):
        def query_cate(model):
            return self.event.count("DISTINCT(category)", reset=False)

        self.event.set_date(date(2024, 3, 3))
        self.event.filter(Expr("id") >= 10)
        rows = iter_query_daily(self.event, query_cate, stop=date(2024, 3, 1))
        self.assertEqual(3, len(rows))
        self.assertSequenceEqual([8, 8, 8], rows)
