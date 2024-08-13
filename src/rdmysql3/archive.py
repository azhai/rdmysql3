# -*- coding: utf-8 -*-

from .table import Table


class Archive(Table):
    _curr_has_suffix = False
    _suffix_mask = "%03d"
    _table_names = []

    def __init__(self, tablename=""):
        super(Archive, self).__init__(tablename)
        self.set_number(0)

    def set_number(self, number=0):
        self.number = abs(int(number))
        return self

    def get_diff_units(self):
        return self.number

    def is_current(self):
        return -1 < self.get_diff_units() < 1

    def is_table_exists(self, force=False):
        table_names = self.list_our_tables(force)
        if len(table_names) == 0:
            return False
        name = self.get_table_name(quote=False)
        return len(name) > 0 and name in table_names

    def is_end_table(self, force=False):
        table_names = self.list_our_tables(force)
        if len(table_names) == 0:
            return True
        name = self.get_table_name(quote=False)
        return len(name) > 0 and name == table_names[-1]

    def get_suffix(self, number=0):
        if number < 0:
            number = self.number
        return self._suffix_mask % number

    def list_our_tables(self, force=False):
        if force or len(self._table_names) == 0:
            mask = self.__tablename__ + "_"
            self._table_names = self.db.list_tables(mask, True)
            self._table_names.sort()
        return self._table_names

    def get_table_name(self, quote=False):
        if not self._curr_has_suffix and self.is_current():
            tablename = self.__tablename__
        else:
            tablename = "%s_%s" % (self.__tablename__, self.get_suffix())
        if quote:
            return self.quote_str(tablename)
        else:
            return tablename

    def create_table(self, truncate=False):
        base_name = self.quote_str(self.__tablename__)
        curr_name = self.get_table_name(quote=True)
        if base_name != curr_name:
            sql = "CREATE TABLE IF NOT EXISTS %s LIKE %s"
            self.db.execute_write(sql % (curr_name, base_name))
        if truncate:
            self.delete(truncate=True)
        return self

    def quick_migrate(self, curr_name, prev_name, auto_incr=0):
        rsql = "RENAME TABLE %s TO %" % (curr_name, prev_name)
        self.db.execute_write(rsql)
        csql = "CREATE TABLE IF NOT EXISTS %s LIKE %s" % (curr_name, prev_name)
        self.db.execute_write(csql)
        if auto_incr:
            asql = "ALTER TABLE %s AUTO_INCREMENT = %%d" % curr_name
            self.db.execute_write(asql, auto_incr)
        return auto_incr  # 自增ID

    def partial_migrate(self, curr_name, prev_name, **where):
        csql = "CREATE TABLE IF NOT EXISTS %s LIKE %s" % (prev_name, curr_name)
        self.db.execute_write(csql, **where)
        isql = "INSERT DELAYED %s SELECT * FROM %s" % (prev_name, curr_name)
        affects = self.db.execute_write(isql, **where)
        dsql = "DELETE FROM %s" % curr_name
        self.db.execute_write(dsql, **where)
        return affects  # 影响的行数

    def _migrate(self, prev_name, **where):
        curr_name = self.get_table_name(quote=True)
        table_info = self.get_table_info("TABLE_ROWS, AUTO_INCREMENT")
        if where or table_info.get("TABLE_ROWS", 0) <= 5000:
            return self.partial_migrate(curr_name, prev_name, **where)
        else:
            auto_incr = table_info.get("AUTO_INCREMENT", 0)
            return self.quick_migrate(curr_name, prev_name, auto_incr)

    def migrate(self, number, **where):
        self.set_number(number)
        prev_name = self.get_table_name(quote=True)
        if self.is_table_exists():
            return 0
        self.set_number()
        return self._migrate(prev_name, **where)
