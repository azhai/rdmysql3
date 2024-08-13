# -*- coding: utf-8 -*-

import cymysql

from .expr import And


class Database(object):
    """ MySQL数据库 """

    configures = {}
    connections = {}

    def __init__(self, current="default"):
        self.current = current
        self.is_auto_commit = False
        self.is_readonly = False
        self.is_verbose = False
        self.sqls = []
        self.conn = None
        self.logger = None

    @classmethod
    def add_configure(cls, name, **configure):
        cls.configures[name] = configure

    @classmethod
    def set_logger(cls, logger):
        cls.logger = logger

    def close(self):
        if isinstance(self.conn, cymysql.Connection):
            self.conn.close()
        self.__class__.connections.pop(self.current)

    def connect(self, conf, **env):
        """ 根据配置连接数据库 """
        conn = cymysql.connect(
            host=conf.get("host", "127.0.0.1"),
            user=conf.get("username", "root"),
            passwd=conf.get("password", ""),
            db=conf.get("database", None),
            port=int(conf.get("port", 3306)),
            charset=conf.get("charset", "utf8mb4"),
            cursorclass=cymysql.cursors.DictCursor
        )
        if conf.get("autocommit") or env.get("autocommit"):
            self.is_auto_commit = True
        conn.autocommit(self.is_auto_commit)
        self.is_readonly = conf.get("readonly", False)
        self.is_verbose = conf.get("verbose", False)
        return conn

    def reconnect(self, force=False, **env):
        is_connected = False
        if not self.conn:  # 重用连接
            self.conn = self.__class__.connections.get(self.current)
        if self.conn:
            if force:
                self.conn.close()  # 强制断开
            else:
                try:
                    is_connected = self.conn.ping(True)  # 需要时重连
                except:
                    print("The connection has losted !")
                    is_connected = False
        if not is_connected:  # 重连
            conf = self.__class__.configures.get(self.current, {})
            self.conn = self.connect(conf, **env)
            self.__class__.connections[self.current] = self.conn
        return self.conn

    def add_sql(self, sql, *params, **kwargs):
        """ 将当前SQL记录到历史中 """
        if len(self.sqls) > 50:
            del self.sqls[:-49]
        conn = self.reconnect(False)
        full_sql = sql.strip() % tuple([conn.escape(p) for p in params])
        self.sqls.append(full_sql)
        if self.logger:
            if kwargs.get("is_write", False):
                self.logger.info(full_sql + ";")
            else:
                self.logger.debug(full_sql + ";")
        elif self.is_verbose:
            print(full_sql + ";")
        return full_sql

    def parse_cond(self, sql, condition=None, **where):
        if condition is None:
            condition = And(**where)
        else:
            assert isinstance(condition, And)
            if len(where) > 0:
                condition = condition.clone().extend(**where)
        sql_where, params = condition.build()
        if sql_where:
            sql += " WHERE " + sql_where
        return sql, params

    def execute_cond(self, sql, condition=None, addition="", *values, **kwargs):
        """ 执行操作，返回结果 """
        sql, params = self.parse_cond(sql, condition)
        if addition:
            sql += " " + addition.strip()
        if len(values) > 0:
            params = list(values) + params
        word = sql.lstrip().split(" ")[0].upper()
        if kwargs.get("type", "").lower() == "write":
            return self.execute_write(sql, *params, **kwargs)
        elif word not in ["DESC", "SELECT", "SHOW"]:
            return self.execute_write(sql, *params, **kwargs)
        else:
            return [r for r in self.execute_read(sql, *params, **kwargs)]

    def execute_write(self, sql, *params, **kwargs) -> int:
        """ 执行写操作，返回影响行数 """
        full_sql = self.add_sql(sql, *params, is_write=True)
        if self.is_readonly:  # 只读，不执行
            return 0
        self.reconnect(False).query(full_sql)
        # return self.conn.affected_rows()
        return self.conn._result.affected_rows

    def execute_read(self, sql, *params, **kwargs):
        """ 执行读操作，以迭代形式返回每行 """
        self.add_sql(sql, *params, is_write=False)
        model, count = kwargs.get("model", dict), 0
        with self.reconnect(False).cursor() as cur:
            cur.execute(sql, params)
            size = kwargs.get("size", -1)
            if size != 0:
                row = cur.fetchone()
                while row:
                    yield model(row)
                    count += 1
                    if size >= 1 and count >= size:
                        break
                    row = cur.fetchone()

    def execute_column(self, sql, *params, **kwargs):
        """ 执行读操作，返回单个值或指定列数组 """
        self.add_sql(sql, *params, is_write=False)
        index = kwargs.get("index", 0)
        cur_class = cymysql.cursors.Cursor
        with self.reconnect(False).cursor(cur_class) as cur:
            cur.execute(sql, params)
            size = kwargs.get("size", -1)
            if size == 1:
                row = cur.fetchone()
                return row[index]
            else:
                return [r[index] for r in cur.fetchall()]

    def get_dbname(self):
        """ 获取当前数据库名称 """
        sql = "SELECT DATABASE()"
        return self.execute_column(sql, size=1)

    def list_tables(self, tablename="", is_wild=True):
        """ 列出当前库符合条件的表 """
        sql = "SHOW TABLES LIKE %s"
        if is_wild:
            tablename += "%"
        return self.execute_column(sql, tablename)

    def commit(self):
        if self.conn:
            self.conn.commit()

    def rollback(self):
        if self.conn:
            self.rollback.commit()

    def insert_id(self) -> int:
        """ 新插入行的ID """
        if self.conn:
            return self.conn.insert_id()
        else:
            return 0
