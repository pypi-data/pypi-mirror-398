import re

def ensure_list(a):
    if isinstance(a, str):
        return a.split(',')
    return a

def normalize_filter_condition(data, field_types={}, fields=None, search_fields=[]):
    d = {}
    if search_fields:
        sv = data.get('search')
        if sv:
            v = {'$regex': sv}
            for fn in search_fields:
                d = {'$or': [d, {fn: v}]} if d else {fn: v}

    mm = {
        'exists': lambda v: {'$exists': v not in ['0', 'false', False]},
        'isnull': lambda v: {'$ne' if v in ['0', 'false', ''] else '$eq': None},
        'regex': lambda v: {'$regex': v},
        'in': lambda v: {'$in': ensure_list(v)},
        'nin': lambda v: {'$nin': ensure_list(v)},
        'all': lambda v: {'$all': ensure_list(v)},
        'gt': lambda v: {'$gt': v},
        'lt': lambda v: {'$lt': v},
        'ne': lambda v: {'$ne': v},
        'eq': lambda v: {'$eq': v},
        'size': lambda v: {'$size': v},
        'gte': lambda v: {'$gte': v},
        'lte': lambda v: {'$lte': v},
        'type': lambda v: {'$type': v},
    }
    for a in data.keys():
        if a == 'search':
            continue
        v = data[a]
        ps = a.split('__')
        if len(ps)>1:
            mn = ps[-1]
            mf = mm.get(mn)
            if mf:
                sl = len(mn)+2
                a = a[:-sl]
                a = a.replace('__', '.')
                is_not = a.endswith('.not')
                if is_not:
                    a=a[:-4]
                if isinstance(v, str):
                    format_func = field_types.get(a)
                    if format_func:
                        v = format_func(v)
                v = mf(v)
                if is_not:
                    v = {'$not': v}

        if fields:
            ps = re.split(r'__|\.', a) ##a.split('__')
            if ps[0] not in fields:
                continue
            a = ".".join(ps)
        a = a.replace('__', '.')
        format_func = field_types.get(a)
        expr = format_func(v) if not isinstance(v, dict) and format_func else v
        if a in d and isinstance(d[a], dict):
            d[a].update(expr)
        else:
            d[a] = expr

    return d
