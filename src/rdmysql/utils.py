# -*- coding: utf-8 -*-

def _reset_pk(query, pk = 'id', num = 0):
    """ 找出需要重新排列的主键 """
    last_diff, changes = 0, []
    start, stop = 0, 0
    if num > 0:
        query = query.filter(Expr(pk)>num)
    for row in query.order_by(pk).iter(pk):
        id, num = row[pk], num + 1
        curr_diff = id - num
        if curr_diff == 0:
            continue
        if last_diff != curr_diff:
            if last_diff > 0:
                changes.append((last_diff, start, stop))
            start, stop, last_diff = id, id, curr_diff
        else:
            stop = id
    if last_diff > 0:
        changes.append((last_diff, start, stop))
    return changes


def reset_model_pk(query, pk = 'id', num = 0):
    """ 重新排列自增主键 """
    try:
        assert issubclass(query, Table)
        query = query()
    except TypeError:
        assert isinstance(query, Table)
    table = query.__tablename__
    changes = _reset_pk(query, pk = pk, num = num)
    tpl = "UPDATE `%s` SET `%s`=`%s`-%%d WHERE `%s`>=%%d AND `%s`<=%%d" % (table, pk, pk, pk, pk)
    for chg in changes:
        query.db.execute(tpl % chg, type='write')
    query.reset()
    maxid = query.apply('MAX', pk)
    if maxid is not None and maxid > 0:
        tpl = "ALTER TABLE `%s` AUTO_INCREMENT=%d"
        query.db.execute(tpl % (table, maxid + 1), type='write')
        return maxid + 1
    return 0
