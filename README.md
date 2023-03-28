# rdmysql: a simple db layer based on ultra-mysql

## Installation

    pip install [--no-deps] rdmysql

It required umysql. If you use pypy, use https://github.com/NextThought/ultramysql instand of it.

## Usage:

``` python
from datetime import datetime
from rdmysql import Database, Table, Row, Expr, And, Or
import settings

Database.configures.update(settings.MYSQL_CONFS)

class UserProfile(Table):
    __dbkey__ = 'user'
    __tablename__ = 't_user_profiles'
    __indexes__ = ['username']

query = UserProfile().filter_by(username = 'ryan')
ryan = query.one(model = Row)
if ryan:
    print ryan.to_dict()
    now = datetime.now()
    today = now.strftime('%Y%m%d')
    changed_at = now.strftime('%Y-%m-%d %H:%M:%S')
    ryan.change('nickname', 'Ryan-%s' % today)
    ryan.change('changed_at', changed_at)
    query.save(ryan)
    print query.db.sqls
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

## Methods of Monthly

Monthly is a subclass of Table, There are other two methods for Monthly:
    
    backward    param monthes : int (optional default=1)
    
    forward     param monthes : int (optional default=1)
    
    set_date    param curr_date : date
    
    migrate     param prev_date : date (When curr_has_suffix is False)
