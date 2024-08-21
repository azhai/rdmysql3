# -*- coding: utf-8 -*-

from .database import Database
from .expr import Expr, And, Or


class Table(object):
    """数据表"""

    __dbkey__ = "default"
    __tablename__ = ""
    __indexes__ = ["id"]

    def __init__(self, table_name=""):
        if table_name:
            self.__tablename__ = table_name
        self.reset()

    @staticmethod
    def quote_str(name):
        return "`%s`" % name

    @property
    def db(self):
        if not hasattr(self, "_db") or not self._db:
            db = Database(self.__dbkey__)
            self.set_db(db)
        return self._db

    def set_db(self, db):
        if isinstance(db, Database):
            self._db = db
        return self

    def is_table_exists(self):
        """当前数据表是否存在"""
        table_name = self.get_table_name(quote=False)
        tables = self.db.list_tables(table_name, False)
        return len(tables) > 0

    def get_tablename(self, quote=False):
        """数据表名称"""
        return self.get_table_name(quote=quote)

    def get_table_name(self, quote=False):
        """数据表名称"""
        if quote:
            return self.quote_str(self.__tablename__)
        else:
            return self.__tablename__

    def get_table_info(self, columns="TABLE_NAME, TABLE_COMMENT, TABLE_ROWS"):
        """数据表总体信息"""
        if isinstance(columns, (list, tuple, set)):
            columns = ",".join(columns)
        dbname = self.db.get_dbname()
        table_name = self.get_table_name(quote=False)
        sql = "SELECT %s FROM `information_schema`.`TABLES`" % columns
        condition = And(TABLE_SCHEMA=dbname, TABLE_NAME=table_name)
        rows = self.db.execute_cond(sql, condition, limit=1, size=1)
        if isinstance(rows, list) and len(rows) > 0:
            return rows[0]
        return {}

    def get_table_fields(self, columns=None):
        """数据表各列的信息"""
        if columns is None:
            columns = [
                "COLUMN_NAME",
                "IS_NULLABLE",
                "DATA_TYPE",
                "COLUMN_TYPE",
                "COLUMN_COMMENT",
            ]
        if isinstance(columns, (list, tuple, set)):
            columns = ",".join(columns)
        dbname = self.db.get_dbname()
        table_name = self.get_table_name(quote=False)
        sql = "SELECT %s FROM `information_schema`.`COLUMNS`" % columns
        condition = And(TABLE_SCHEMA=dbname, TABLE_NAME=table_name)
        addition = "ORDER BY ORDINAL_POSITION"
        return self.db.execute_cond(sql, condition, addition)

    def reset(self, or_cond=False):
        """清空当前的Where、Group by、Order by、Limit等条件"""
        self.condition = Or() if or_cond else And()
        self.additions = {}
        return self

    def filter(self, expr, *args):
        if isinstance(expr, str):
            expr = Expr(expr).op(*args)
        self.condition.append(expr)
        return self

    def filter_by(self, **where):
        self.condition.extend(**where)
        return self

    def order_by(self, field, direction="ASC"):
        if "ORDER BY" not in self.additions:
            self.additions["ORDER BY"] = []
        order = "%s %s" % (field, direction)
        self.additions["ORDER BY"].append(order)
        return self

    def group_by(self, field):
        if "GROUP BY" not in self.additions:
            self.additions["GROUP BY"] = []
        self.additions["GROUP BY"].append(field)
        return self

    def build_group_order(self, reset=False):
        """生成Group by、Order by、Limit部分的SQL"""
        group_order = ""
        for key, vals in self.additions.items():
            item = " %s %s" % (key, ", ".join(vals))
            group_order += item
        if reset:
            self.additions = {}
        return group_order

    @staticmethod
    def unzip_pairs(row, keys=None):
        if isinstance(row, dict):
            keys = row.keys()
        to_val = lambda v: v.first_param() if isinstance(v, Expr) else v
        if isinstance(row, (list, tuple)) and len(keys) > 0:
            fields = "(`%s`)" % "`,`".join(keys)
            values = [to_val(row[key]) for key in keys]
        else:
            fields = ""
            values = [to_val(val) for val in list(row)]
        return keys, values, fields

    def insert(self, *rows, **kwargs) -> int:
        action = kwargs.get("action", "INSERT INTO")
        if len(rows) == 0:
            return 0
        rows = list(rows)
        row = rows.pop(0)
        keys, params, fields = self.unzip_pairs(row)
        holders = ",".join(["%s"] * len(params))
        table_name = self.get_table_name(quote=True)
        head = "%s %s %s VALUES (%s)" % (action, table_name, fields, holders)
        if len(rows) == 0:
            sql = head
        else:  # 插入更多行
            sql = head + (", (%s)" % holders) * len(rows)
            for row in rows:
                keys, values, _ = self.unzip_pairs(row, keys)
                params.extend(values)
        self.db.execute_write(sql, *params)
        return self.db.insert_id()  # 最后的自增ID

    def insert_chunks(self, keys, rows, **kwargs) -> int:
        if len(rows) == 0:
            return 0
        rows, count = list(rows), len(rows)
        action = kwargs.get("action", "INSERT INTO")
        size = kwargs.get("size", 100)
        fields = "(`%s`)" % "`,`".join(keys)
        holders = ",".join(["%s"] * len(keys))
        table_name = self.get_table_name(quote=True)
        head = "%s %s %s VALUES (%s)" % (action, table_name, fields, holders)
        # 改为手动一次提交，最后需要将自动提交恢复（如果是）
        self.db.set_auto_commit(False)
        for i in range(0, count, size):
            chunk, params = rows[i : i + size], []
            sql = head + (", (%s)" % holders) * (len(chunk) - 1)
            for row in chunk:
                params.extend(list(row))
            self.db.execute_write(sql, *params)
            self.db.commit()
        self.db.set_auto_commit(None)
        return count  # 新增的行数

    def delete(self, reset=True, **where) -> int:
        table_name = self.get_table_name(quote=True)
        if where.pop("truncate", False):
            sql = "TRUNCATE TABLE %s" % table_name
        else:
            sql = "DELETE FROM %s" % table_name
        sql, params = self.db.parse_cond(sql, self.condition, **where)
        if reset:
            self.reset()
        return self.db.execute_write(sql, *params)  # 影响的行数

    def update(self, changes, reset=True, **where) -> int:
        assert isinstance(changes, dict)
        holders, values = [], []
        for key, value in changes.items():
            if isinstance(value, Expr):
                exps, vals = value.build()
                holders.append("`%s`=%s" % (key, exps))
                values.extend(vals)
            else:
                holders.append("`%s`=%%s" % key)
                values.append(value)
        fields = ",".join(holders)
        table_name = self.get_table_name(quote=True)
        sql = "UPDATE %s SET %s" % (table_name, fields)
        sql, params = self.db.parse_cond(sql, self.condition, **where)
        if len(values) > 0:
            params = list(values) + params
        if reset:
            self.reset()
        return self.db.execute_write(sql, *params)  # 影响的行数

    def save(self, row, indexes=None, reset=True):
        """根据主键对应id已存在，决定是更新还是插入"""
        assert hasattr(row, "items")
        if indexes is None:  # 使用主键
            indexes = self.__indexes__
        data, where = {}, {}
        for key, value in row.items():
            if key not in indexes:
                data[key] = value
            elif value is not None:
                where[key] = value
        affect_rows = 0
        if len(where) > 0:  # 先尝试更新
            affect_rows = self.update(data, reset=reset, **where)
        if not affect_rows:  # 再尝试插入/替换
            data.update(where)
            insert_id = self.insert(data, action="REPLACE INTO")
            return True, insert_id
        else:
            return False, affect_rows

    def iter(self, columns="*", model=None, index=None, **kwargs):
        """读查询，返回迭代结果"""
        limit = int(kwargs.get("limit", -1))
        offset = int(kwargs.get("offset", 0))
        addition = self.build_group_order()
        if limit > 0 or offset > 0:
            addition += " LIMIT %d, %d" % (offset, limit)
        if isinstance(columns, (list, tuple, set)):
            columns = ",".join(columns)
        table_name = self.get_table_name(quote=True)
        sql = "SELECT %s FROM %s" % (columns, table_name)
        sql, params = self.db.parse_cond(sql, self.condition)
        if addition:
            sql += " " + addition.strip()
        if kwargs.pop("reset", True):
            self.reset()
        if model is not None:
            kwargs["model"] = model
        for row in self.db.execute_read(sql, *params, **kwargs):
            if index is None:
                yield row
            else:
                key = row.get(index, None)
                if key is not None:
                    yield key, row

    def all(self, columns="*", model=None, index=None, **kwargs):
        return [r for r in self.iter(columns, model, index, **kwargs)]

    def one(self, columns="*", model=None):
        for row in self.iter(columns, model=model, limit=1, size=1):
            return row
        if model is dict:
            return {}

    def apply(self, name, *args, **kwargs):
        """单个值或单列的读查询"""
        name = name.strip().upper()
        if name == "COUNT" and len(args) == 0:
            column = "COUNT(*)"
        else:
            column = "%s(%s)" % (name, ", ".join(args))
        table_name = self.get_table_name(quote=True)
        sql = "SELECT %s FROM %s" % (column, table_name)
        sql, params = self.db.parse_cond(sql, self.condition)
        kwargs["size"] = 1
        if kwargs.pop("reset", True):
            self.reset()
        result = self.db.execute_column(sql, *params, **kwargs)
        if result is None:
            result = kwargs.pop("default", None)
        if "coerce" in kwargs:
            result = kwargs["coerce"](result)
        return result

    def count(self, *args, **kwargs):
        kwargs["coerce"] = int
        if "default" not in kwargs:
            kwargs["default"] = 0
        return self.apply("count", *args, **kwargs)

    def sum(self, *args, **kwargs):
        if "default" not in kwargs:
            kwargs["default"] = 0
        return self.apply("sum", *args, **kwargs)

    def max(self, *args, **kwargs):
        return self.apply("max", *args, **kwargs)

    def min(self, *args, **kwargs):
        return self.apply("min", *args, **kwargs)

    def avg(self, *args, **kwargs):
        return self.apply("avg", *args, **kwargs)
