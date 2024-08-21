# -*- coding: utf-8 -*-

from datetime import date, datetime
from decimal import Decimal


class Row(object):
    """单行结果"""

    _fields = []

    def __init__(self, data={}):
        self._data = {}
        self.merge(data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        if key in self._data:
            del self._data[key]

    def __getattr__(self, key):
        return self[key]

    def get(self, key, default=None):
        if key in self._data:
            return self._data[key]
        else:
            return default

    def change(self, key, value):
        self[key] = value
        return self

    def set_fields(self, fields):
        self._fields = list(fields)
        return self

    def merge(self, data):
        if self._fields and isinstance(data, (list, tuple)):
            data = dict(zip(self._fields, list(data)))
        self._data.update(data)
        return self

    def items(self):
        for k, v in self._data.items():
            yield k, self.coerce_value(v)

    def to_dict(self):
        return dict(self.items())

    @staticmethod
    def coerce_value(value):
        if isinstance(value, datetime):
            value = value.strftime("%F %T")
        elif isinstance(value, date):
            value = value.strftime("%F")
        elif isinstance(value, Decimal):
            value = float(value)
        return value
