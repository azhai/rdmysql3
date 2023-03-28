# -*- coding: utf-8 -*-

from .table import Table


class Archive(Table):
    curr_has_suffix = False
    suffix_mask = '%03d'

    def __init__(self, tablename=''):
        super(Archive, self).__init__(tablename)
        self.set_number(0)

    def set_number(self, number=0):
        self.number = abs(int(number))
        return self

    def get_diff_units(self):
        return self.number

    def is_current(self):
        return -1 < self.get_diff_units() < 1

    def get_suffix(self, number=0):
        if number < 0:
            number = self.number
        return self.suffix_mask % number

    def get_tablename(self, quote=False):
        if not self.curr_has_suffix and self.is_current():
            tablename = self.__tablename__
        else:
            tablename = '%s_%s' % (self.__tablename__, self.get_suffix())
        if quote:
            return self.quote_str(tablename)
        else:
            return tablename

    def quick_migrate(self, curr_name, prev_name, auto_incr=0):
        rsql = "RENAME TABLE %s TO %" % (curr_name, prev_name)
        self.db.execute(rsql, type='write')
        csql = "CREATE TABLE IF NOT EXISTS %s LIKE %s" % (curr_name, prev_name)
        self.db.execute(csql, type='write')
        if auto_incr:
            asql = "ALTER TABLE %s AUTO_INCREMENT = %%d" % curr_name
            self.db.execute(asql, auto_incr, type='write')
        return auto_incr  # 自增ID

    def partial_migrate(self, curr_name, prev_name, **where):
        where['type'] = 'write'
        csql = "CREATE TABLE IF NOT EXISTS %s LIKE %s" % (prev_name, curr_name)
        self.db.execute(csql, **where)
        isql = "INSERT DELAYED %s SELECT * FROM %s" % (prev_name, curr_name)
        rs = self.db.execute(isql, **where)
        dsql = "DELETE FROM %s" % curr_name
        self.db.execute(dsql, **where)
        return rs[0] if rs else -1  # 影响的行数

    def _migrate(self, prev_name, **where):
        curr_name = self.get_tablename(quote=True)
        table_info = self.get_tableinfo(['TABLE_ROWS', 'AUTO_INCREMENT'])
        if where or table_info['TABLE_ROWS'] <= 5000:
            return self.partial_migrate(curr_name, prev_name, **where)
        else:
            auto_incr = table_info['AUTO_INCREMENT']
            return self.quick_migrate(curr_name, prev_name, auto_incr)

    def migrate(self, number, **where):
        self.set_number(number)
        prev_name = self.get_tablename(quote=True)
        if self.is_exists():
            return 0
        self.set_number()
        return self._migrate(prev_name, **where)
