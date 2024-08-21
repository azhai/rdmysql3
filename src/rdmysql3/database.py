# -*- coding: utf-8 -*-

import cymysql
from .expr import And


class Database(object):
    """MySQL数据库"""

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
        """根据配置连接数据库"""
        conn = cymysql.connect(
            host=conf.get("host", "127.0.0.1"),
            user=conf.get("username", "root"),
            passwd=conf.get("password", ""),
            db=conf.get("database", None),
            port=int(conf.get("port", 3306)),
            charset=conf.get("charset", "utf8mb4"),
            cursorclass=cymysql.cursors.DictCursor,
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
                except cymysql.Error:
                    print("The connection has lost !")
                    is_connected = False
        if not is_connected:  # 重连
            conf = self.__class__.configures.get(self.current, {})
            self.conn = self.connect(conf, **env)
            self.__class__.connections[self.current] = self.conn
        return self.conn

    def escape(self, param, check=False):
        if check and not self.conn:
            self.reconnect(False)
        if isinstance(param, list):
            return [self.escape(p) for p in param]
        if self.conn:
            return self.conn.escape(param)
        else:
            return "'%s'" % param

    def query(self, sql):
        if not self.conn:
            self.reconnect(False)
        if self.conn:
            return self.conn.query(sql)
        return False

    def cursor(self, use_dict=True):
        if not self.conn:
            self.reconnect(False)
        if not self.conn:
            return
        klass = None
        if use_dict is False:
            klass = cymysql.cursors.Cursor
        return self.conn.cursor(klass)

    def add_sql(self, sql, *params, **kwargs) -> str:
        """将当前SQL记录到历史中"""
        if len(self.sqls) > 50:
            del self.sqls[:-49]
        full_sql = sql.strip() % tuple(self.escape(params, True))
        self.sqls.append(full_sql)
        if self.logger:
            if kwargs.get("is_write", False):
                self.logger.info(full_sql + ";")
            else:
                self.logger.debug(full_sql + ";")
        elif self.is_verbose:
            print(full_sql + ";")
        return full_sql

    @staticmethod
    def parse_cond(sql, condition=None, **where):
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
        """执行操作，返回结果"""
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
        """执行写操作，返回影响行数"""
        kwargs["is_write"] = True
        full_sql = self.add_sql(sql, *params, **kwargs)
        if self.is_readonly:  # 只读，不执行
            return 0
        if self.query(full_sql) is False:
            return 0
        if self.conn and self.conn._result:
            return self.conn._result.affected_rows
            # return self.conn.affected_rows()
        else:
            return 0

    def execute_read(self, sql, *params, **kwargs):
        """执行读操作，以迭代形式返回每行"""
        self.add_sql(sql, *params, is_write=False)
        model, count = kwargs.get("model", dict), 0
        with self.cursor() as cur:
            cur.execute(sql, params)
            size = kwargs.get("size", -1)
            if size != 0:
                row = cur.fetchone()
                while row:
                    yield model(row)
                    count += 1
                    if 1 <= size <= count:
                        break
                    row = cur.fetchone()

    def execute_column(self, sql, *params, **kwargs):
        """执行读操作，返回单个值或指定列数组"""
        self.add_sql(sql, *params, is_write=False)
        index = kwargs.get("index", 0)
        with self.cursor(False) as cur:
            cur.execute(sql, params)
            size = kwargs.get("size", -1)
            if size == 1:
                row = cur.fetchone()
                return row[index]
            else:
                return [r[index] for r in cur.fetchall()]

    def get_dbname(self):
        """获取当前数据库名称"""
        sql = "SELECT DATABASE()"
        return self.execute_column(sql, size=1)

    def list_tables(self, table_name="", is_wild=True):
        """列出当前库符合条件的表"""
        sql = "SHOW TABLES LIKE %s"
        if is_wild:
            table_name += "%"
        return self.execute_column(sql, table_name)

    def commit(self):
        if self.conn:
            self.conn.commit()
        return False

    def rollback(self):
        if self.conn:
            self.conn.rollback()
        return False

    def set_auto_commit(self, state=None):
        if state is None:  # 恢复原先的设置
            state = self.is_auto_commit
        if not self.conn:
            self.reconnect(force=False)  # 保证conn存在
        if self.conn:
            self.conn.autocommit(state)
        return False

    def insert_id(self) -> int:
        """新插入行的ID"""
        if not self.conn:
            return 0
        last = self.conn.insert_id()
        return last if isinstance(last, int) else 0
