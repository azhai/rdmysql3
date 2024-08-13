# -*- coding: utf-8 -*-

from datetime import datetime
import sys, settings
sys.path.insert(0, settings.PROJECT_SRC_DIR)
from rdmysql3 import Database, Table, Row, Expr, Or
Database.configures.update(settings.MYSQL_CONFS)


class UserProfile(Table):
    __dbkey__ = "default"
    __tablename__ = "t_user_profiles"


def test_query_all():
    where = Or(Expr('id') < 100, Expr('id') == 100)  # Expr('id') <= 100
    query = UserProfile().filter(where)
    profs = query.order_by('id', 'DESC').all('*', limit=3)
    if profs is not None:
        assert len(profs) <= 3
    print(query.db.sqls[-1])
    return profs or []


def test_query_one(username):
    query = UserProfile().filter(Expr('username') == username)
    ryan = query.one('*', model=Row)
    if ryan is not None:
        assert ryan.username == username
        print(ryan.to_dict())
    print(query.db.sqls[-1])
    return ryan


def test_query_save(obj, **kwargs):
    assert isinstance(obj, Row)
    for key, value in kwargs.items():
        obj.change(key, value)
    obj.set_pkey('id')
    query = UserProfile()
    query.save(obj)
    print(query.db.sqls[-1])

    obj.change('id', None)
    obj.change('username', 'ryan2')
    query.save(obj)
    print(query.db.sqls[-1])
    return obj


if __name__ == '__main__':
    test_query_all()
    ryan = test_query_one(username='ryan')
    if ryan:
        now = datetime.now()
        today = now.strftime('%Y%m%d')
        changed_at = now.strftime('%Y-%m-%d %H:%M:%S')
        nickname = 'Ryan-%s' % today
        test_query_save(ryan, nickname=nickname, changed_at=changed_at)
