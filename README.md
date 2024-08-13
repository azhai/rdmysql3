# rdmysql3: A simple db layer based on CyMysql for Python 3.x

## Installation

    pip install [--no-deps] rdmysql3

## Usage:

``` python
from datetime import datetime, date
from rdmysql3 import (Database, Table, Daily,
        Row, Expr, And, Or, iter_query_daily)
import settings

Database.configures.update(settings.MYSQL_CONFS)

class UserProfile(Table):
    __dbkey__ = 'user'
    __tablename__ = 't_user_profiles'
    __indexes__ = ['username']

class UserEvent(Daily):
    __dbkey__ = "default"
    __tablename__ = "t_user_events"

query = UserProfile().filter_by(username = 'ryan')
ryan = query.one(model = Row)
if ryan:
    print ryan.to_dict()
    now = datetime.now()
    today = now.strftime('%Y%m%d')
    ryan['changed_at'] = now.strftime('%Y-%m-%d %H:%M:%S')
    ryan.change('nickname', 'Ryan-%s' % today)
    query.save(ryan)
    print(query.db.sqls)


def get_all_logins(model):
    q = model.filter_by(category="login").order_by("id", "DESC")
    return q.all(model=Row, reset=True)
query = UserEvent()
rows = iter_query_daily(query, get_all_logins,
        stop=date(2024,3,1), fuse=True)
print(query.db.sqls)
```

## Methods of Table

There are some methods for class named 'Table':

    insert      param *rows
                param **kwargs

    delete      param **where

    update      param changes : dict
                param **where

    save        param changes : dict / object
                param indexes : list (optional default=[])

    filter      param expr : Expr / str
                param *args

    filter_by   param **where

    order_by    param field     : str
                param direction : 'ASC' / 'DESC' (optional default='ASC')

    group_by    param field : str

    all         param coulmns : str (optional default='*')
                param limit   : int (optional default=0)
                param offset  : int (optional default=0)

    one         param coulmns : str   (optional default='*')
                param model   : class (optional default=dict)

    apply       param name : str
                param *args
                param **kwargs

    count,sum,max,min,avg       param *args
                                param **kwargs

## Methods of Monthly/Weekly/Daily

Monthly is a subclass of Table, There are other two methods for Monthly:

    backward    param monthes : int (optional default=1)

    forward     param monthes : int (optional default=1)

    set_date    param curr_date : date

    migrate     param prev_date : date (When curr_has_suffix is False)
