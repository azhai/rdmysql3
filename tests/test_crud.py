# -*- coding: utf-8 -*-

from datetime import datetime
from rdmysql3 import Row, Expr, Or

import fixure

keys = ["username", "nickname", "gender", "birthday", "changed_at"]
rows = [
    ["admin", "Admin", "X", "1985-01-01", datetime(2024, 2, 28, 17, 5)],
    ["bob", "Bob", "M", "1983-02-01", datetime(2024, 2, 28, 17, 5)],
    ["cindy", "Cindy", "F", "1988-03-01", datetime(2024, 2, 28, 17, 5)],
    ["david", "David", "M", "1990-04-01", datetime(2024, 2, 28, 17, 5)],
    ["frank", "Frank", "M", "1976-05-01", datetime(2024, 2, 28, 17, 5)],
    ["grace", "Grace", "F", "2001-06-01", datetime(2024, 2, 28, 17, 5)],
    ["helen", "Helen", "F", "1999-07-01", datetime(2024, 2, 28, 17, 5)],
    ["iris", "Iris", "F", "1993-08-01", datetime(2024, 2, 28, 17, 5)],
    ["jack", "Jack", "M", "2000-09-01", datetime(2024, 2, 28, 17, 5)],
]
admin = dict(zip(keys, rows[0]))
spec_birthday = "1988-02-29"


class TestUserProfile(fixure.TestBase):

    def test_01_insert(self):
        id = self.model.insert(admin)
        self.assertEqual(1, id)
        nums = self.model.insert_chunks(keys, rows[1:])
        self.assertEqual(len(rows) - 1, nums)

    def test_02_select_row(self):
        row = self.model.order_by("id").one(model=Row)
        self.assertEqual(1, row.id)
        self.assertEqual(admin["nickname"], row.nickname)
        self.assertEqual(admin["birthday"], row.birthday)
        self.assertEqual(admin["changed_at"], row.changed_at)

    def test_03_select_all(self):
        where = Or(Expr("id") <= 3, Expr("gender") == "F")
        rows = self.model.filter(where).all()
        self.assertEqual(6, len(rows))
        for row in rows:
            if row["username"] == "admin":
                self.assertEqual("X", row["gender"])
            elif row["username"] == "bob":
                self.assertEqual("M", row["gender"])
            else:
                self.assertEqual("F", row["gender"])

    def test_04_update(self):
        row = self.model.filter_by(username="cindy").one(model=Row)
        row["birthday"] = spec_birthday
        insert, affects = self.model.save(row)
        self.assertFalse(insert)
        self.assertEqual(1, affects)
        row = self.model.filter_by(username="cindy").one(model=Row)
        self.assertEqual(spec_birthday, row.birthday)

    def test_05_apply(self):
        num = self.model.filter_by(gender="M").count()
        self.assertEqual(4, num)
        birthday = self.model.filter(Expr("id") <= 3).max("birthday")
        self.assertEqual(spec_birthday, birthday)
