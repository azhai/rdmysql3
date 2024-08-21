# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from .archive import Archive


class Daily(Archive):
    _suffix_mask = "%Y%m%d"

    def __init__(self, table_name=""):
        super(Daily, self).__init__(table_name)
        self.set_date()

    def set_date(self, curr_date=None):
        if curr_date is None:
            self.calender = date.today()
            return self
        try:
            curr_date = self.adjust_date(curr_date)
            self.calender = curr_date
        except (ValueError, AssertionError):
            pass
        return self

    def adjust_date(self, calender):
        if isinstance(calender, str):
            calender = datetime.strptime(calender, "%Y-%m-%d")
        if isinstance(calender, datetime):
            calender = calender.date()
        assert isinstance(calender, date)
        return calender

    def is_end_table(self, force=False):
        table_names = self.list_our_tables(force)
        if len(table_names) == 0:
            return True
        name = self.get_table_name(quote=False)
        return len(name) > 0 and name == table_names[0]

    def get_delta_days(self):
        delta = self.calender - self.adjust_date(date.today())
        return delta.days

    def get_diff_units(self):
        return self.get_delta_days()

    def get_suffix(self, calender=None):
        if not calender:
            calender = self.calender
        elif not isinstance(calender, (date, datetime)):
            calender = self.calender
        calender = self.adjust_date(calender)
        return calender.strftime(self._suffix_mask)

    def forward(self, qty=1):
        self.calender += timedelta(qty)
        return self

    def backward(self, qty=1):
        return self.forward(0 - qty)

    def migrate(self, prev_date, **where):
        self.set_date(prev_date)
        prev_name = self.get_table_name(quote=True)
        if self.is_table_exists():
            return 0
        self.set_date(date.today())
        return self._migrate(prev_name, **where)


class Weekly(Daily):
    """以周日为一周开始，跨年的一周算作前一年最后一周"""

    _suffix_mask = "%Y0%U"

    def adjust_date(self, calender):
        calender = super(Weekly, self).adjust_date(calender)
        weekday = calender.weekday()
        if weekday > 0:
            calender -= timedelta(weekday)
        return calender

    def forward(self, qty=1):
        weekday = self.calender.weekday()
        self.calender += timedelta(qty * 7 - weekday)
        return self

    def get_diff_units(self):
        return self.get_delta_days() / 7


class Monthly(Daily):
    _suffix_mask = "%Y%m"

    def adjust_date(self, calender):
        calender = super(Monthly, self).adjust_date(calender)
        if calender.day > 1:
            calender = calender.replace(day=1)
        return calender

    def forward(self, qty=1):
        offset = self.calender.month + qty - 1
        self.calender = date(
            year=self.calender.year + offset / 12,  # 负数除法向下取整
            month=offset % 12 + 1,  # 负数求余结果也是正数或零
            day=1,
        )
        return self

    def get_diff_units(self):
        today = date.today()
        result = self.calender.month - today.month
        result += (self.calender.year - today.year) * 12
        return result


class Yearly(Daily):
    _suffix_mask = "%Y"

    def adjust_date(self, calender):
        calender = super(Yearly, self).adjust_date(calender)
        if calender.month > 1 or calender.day > 1:
            calender = calender.replace(month=1, day=1)
        return calender

    def forward(self, qty=1):
        year = self.calender.year + qty
        self.calender = date(year, 1, 1)
        return self

    def get_diff_units(self):
        today = date.today()
        return self.calender.year - today.year


def iter_query_daily(model, func, stop=None, fuse=False):
    assert isinstance(model, Daily)
    result, start = [], model.calender
    while stop is None or start >= stop:
        if model.is_table_exists():
            data = func(model)
            if fuse and isinstance(data, list):
                result.extend(data)
            else:
                result.append(data)
        if model.is_end_table():
            break
        model.backward()
        start = model.calender
    return result
