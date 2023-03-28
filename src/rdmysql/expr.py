# -*- coding: utf-8 -*-


class Expr(object):
    """ 表达式 """
    _field = ''

    def __init__(self, field, table=''):
        self.orig_field = field
        self.orig_table = table
        self.conds = []

    def __str__(self):
        operation, params = self.build()
        return operation.replace('%s', "'%s'") % tuple(params)

    @property
    def field(self):
        if not self._field and self.orig_field:
            if '(' in self.orig_field or '`' in self.orig_field:
                self._field = '%s' % self.orig_field
            else:
                self._field = '`%s`' % self.orig_field
                if self.orig_table:
                    table = '`%s`' % self.orig_table
                    self._field = '%s.%s' % (table, self._field)
        return self._field

    def flatten(self):
        wheres, params = [], []
        for where, values in self.conds:
            wheres.append(where)
            params.extend(values)
        return wheres, params

    def build(self):
        wheres, params = self.flatten()
        and_where = ' AND '.join(wheres)
        return and_where, params

    def merge(self, other):
        if other.field == self.field:
            self.conds.extend(other.conds)
        return self

    def first_param(self):
        if self.conds:
            values = self.conds[0][1]
            if values:
                return values[0]

    def _op(self, opname):
        if '%' not in opname:
            opname = opname.strip()
            if opname in ['IS NULL', 'IS NOT NULL']:
                opname = '%(field)s ' + opname
            else:
                opname = '%(field)s ' + opname + ' %%s'
        return opname % {'field': self.field}

    def op(self, opname, *values):
        if len(values) == 1 and values[0] is None:
            assert opname in ('=', '<>')  # NULL不能比较大小
        operation = self._op(opname)
        self.conds.append((operation, values))
        return self

    def __eq__(self, value):
        if value is None:
            return self.op('IS NULL')
        else:
            return self.op('=', value)

    def __ne__(self, value):
        if value is None:
            return self.op('IS NOT NULL')
        else:
            return self.op('<>', value)

    def __gt__(self, value):
        return self.op('>', value)

    def __ge__(self, value):
        return self.op('>=', value)

    def __lt__(self, value):
        return self.op('<', value)

    def __le__(self, value):
        return self.op('<=', value)

    def within(self, values, is_not=False):
        if isinstance(values, set):
            values = list(values)
        else:
            assert isinstance(values, (list, tuple))
        length = len(values)
        if length == 0:
            opname = 'IS NOT NULL' if is_not else 'IS NULL'
            return self.op(opname)
        elif length == 1:
            opname = '<>' if is_not else '='
            return self.op(opname, values[0])
        else:
            cons = 'NOT IN' if is_not else 'IN'
            masks = '%%s' + ',%%s' * (length - 1)
            opname = '%%(field)s %s (%s)' % (cons, masks)
            return self.op(opname, *values)

    def without(self, values):
        return self.within(values, is_not=True)

    def like(self, value, **kwargs):
        if kwargs.get('left'):
            value = '%%' + value
        elif kwargs.get('right'):
            value = value + '%%'
        else:
            value = '%%' + value + '%%'
        opname = 'NOT LIKE' if kwargs.get('is_not') else 'LIKE'
        return self.op(opname, value)

    def unlike(self, value, **kwargs):
        kwargs['is_not'] = True
        return self.like(value, **kwargs)


class And(object):
    """ 与 """

    def __init__(self, *args, **kwargs):
        self.expressions = []
        for expr in args:
            self.append(expr)
        self.extend(**kwargs)

    def append(self, expr):
        if isinstance(expr, (Expr, And)):
            self.expressions.append(expr)
        return self

    def extend(self, **where):
        for field, value in where.iteritems():
            self.append(Expr(field) == value)
        return self

    def clone(self):
        klass = self.__class__
        return klass(*[expr for expr in self.expressions])

    def flatten(self):
        wheres, params = [], []
        for expr in self.expressions:
            where, values = expr.build()
            wheres.append(where)
            params.extend(values)
        return wheres, params

    def build(self):
        wheres, params = self.flatten()
        and_where = ' AND '.join(wheres)
        return and_where, params


class Or(And):
    """ 或 """

    def build(self):
        wheres, params = self.flatten()
        or_where = ' OR '.join(wheres)
        if len(wheres) > 1:
            or_where = '(' + or_where + ')'
        return or_where, params
