
from .lookup import normalize_filter_condition
from .config import SERVER, DB, TIMEOUT
from .utils import loadMongoDB, filed_type_func, all_fields_type_func
from .query import QuerySet
from functools import cached_property

class Store(object):
    name = 'test_mongo_store'
    timeout = TIMEOUT
    field_types = {}
    fields = None
    search_fields = []
    ordering = ('-id',)

    def __init__(self, name=None, **kwargs):
        self.db = loadMongoDB(**kwargs)
        if name:
            self.name = name
        self.collection = getattr(self.db, self.name)

    @cached_property
    def _field_type_map(self):
        fts = all_fields_type_func(self._fields)
        if not self.field_types:
            return fts
        for ft, fns in self.field_types.items():
            for fn in fns:
                if isinstance(ft, str):
                    ft = filed_type_func(ft)
                fts[fn] = ft
        return fts

    @cached_property
    def _fields(self):
        fs = {}
        for d in self.random_find(count=10):
            fs.update(json_schema(d))
        if self.fields and isinstance(self.fields, dict):
            fs.update(self.fields)
        return fs

    def random_get(self, *args, **kwargs):
        rs = list(self.random_find(args[0], count=1, **kwargs))
        return rs[0] if rs else None

    def get(self, cond):
        if isinstance(cond, text_type):
            cond = {'_id': ObjectId(cond)}
        else:
            cond = self.normalize_filter(cond)
        return self.collection.find_one(cond)

    def get_or_create(self, cond, defaults={}):
        a = self.get(cond)
        if not a:
            d = {}
            d.update(cond)
            d.update(defaults)
            rs = self.collection.insert_one(d)
            a = self.get({'_id': rs.inserted_id})
        return a

    def random_find(self, cond={}, count=10, fields=None):
        cond = self.normalize_filter(cond)
        fs = [{'$match': cond}, {'$sample': {'size': count}}]
        if fields:
            fs.append({'$project': fields})
        return self.collection.aggregate(fs)

    def find(self, filter=None, projection=None, **kwargs):
        filter = self.normalize_filter(filter)
        if 'sort' not in kwargs:
            ordering = kwargs.pop('ordering', self.ordering)
            kwargs['sort'] = [ordering_to_sort(s) for s in ordering]
        if isinstance(projection, (list, tuple, set)):
            projection = dict([(a, 1) for a in projection])
            if '_id' not in projection:
                projection['_id'] = 0
        rs = self.collection.find(filter, projection,  **kwargs)
        if not hasattr(rs, 'count'):
            setattr(rs, 'count', lambda: self.count(filter))
        return rs

    def search(self, cond, *args, **kwargs):
        # cond = self.normalize_filter(cond)
        return self.find(cond, *args, **kwargs)

    def upsert(self, cond, value, **kwargs):
        d = {'$set': value}
        for k, v in kwargs.items():
            d['$%s' % k] = v
        return self.collection.update_one(cond, d, upsert=True)

    def batch_upsert(self, data_list, key='id', preset=lambda a, i: a, **kwargs):
        i = -1
        for i, d in enumerate(data_list):
            if isinstance(d, tuple):
                d = d[-1]
            d = preset(d, i) or d
            print(d[key])
            self.upsert({key: d[key]}, d, **kwargs)
        return i + 1

    def update(self, cond, value, **kwargs):
        cond = self.normalize_filter(cond)
        d = {}
        if value:
            d['$set'] = value
        for k, v in kwargs.items():
            d['$%s' % k] = v
        return self.collection.update_many(cond, d)

    def inc(self, cond, value):
        cond = self.normalize_filter(cond)
        self.collection.update_many(cond, {'$inc': value}, upsert=True)

    def add_to_set(self, cond, value):
        cond = self.normalize_filter(cond)
        self.collection.update_many(cond, {'$addToSet': value}, upsert=True)

    def count(self, filter=None, distinct=False):
        filter = self.normalize_filter(filter)
        if distinct:
            gs = []
            if filter:
                gs.append({'$match': filter})
            gs.append({'$group': {'_id': '$%s' % distinct}}),
            gs.append({'$group': {'_id': 0, 'count': {'$sum': 1}}})
            for a in self.collection.aggregate(gs):
                return a['count']
            return 0
        if not filter:
            return self.collection.estimated_document_count()
        return self.collection.count_documents(filter)

    def sum(self, field, filter=None):
        filter = self.normalize_filter(filter)
        gs = []
        if filter:
            gs.append({'$match': filter})
        gs.append({'$group': {'_id': 0, 'result': {'$sum': '$%s' % field}}})
        for a in self.collection.aggregate(gs):
            return a['result']

    def count_by(self, field, output='dict', **kwargs):
        rs = self.group_by(field, **kwargs)
        if output == 'dict':
            rs = dict([(a['_id'], a['count']) for a in rs])
        return rs

    def group_by(self, field, aggregate={'count': {'$sum': 1}}, filter=None, unwind=False, prepare=[]):
        filter = self.normalize_filter(filter)
        ps = []+ prepare
        if filter:
            ps.append({'$match': filter})
        if unwind:
            ps.append({'$unwind': '$%s' % field})
        if isinstance(field, str):
            exp = '$%s' % field
        elif isinstance(field, (list,tuple)):
            exp= dict([(f, f'${f}') for f in field])
        else:
            exp = field
        d = {'_id': exp}
        if isinstance(aggregate, (list, tuple)):
            aggregate = dict([(f, {'$sum': f'${f}'}) for f in aggregate])
        d.update(aggregate)
        ps.append({'$group': d})
        rs = self.collection.aggregate(ps)
        return rs

    def clean_data(self, data):
        d = {}
        for a in data.keys():
            if self._fields and a not in self._fields:
                continue
            d[a] = data[a]

        for t, fs in self.field_types.items():
            for f in fs:
                if f in d:
                    d[f] = t(d[f])
        return d

    def normalize_filter(self, data, cast=False):
        if not data:
            return data
        fs = self._fields if cast else None
        fm = self._field_type_map if cast else {}
        # print(fm, fs)
        return normalize_filter_condition(data, fm , fs, self.search_fields) #

    def create_index(self):
        for i in self.keys:
            self.collection.create_index([(i, 1)])

    def eval_foreign_keys(self, d, foreign_keys=None):
        fks = foreign_keys or getattr(self, 'foreign_keys', None)
        if not fks:
            return d
        for kn, sn in fks.items():
            if kn not in d:
                continue
            id = mongo_id_value(d[kn])
            if not id:
                continue
            d[kn] = Store(name=sn).get(id)
        return d

    def change_field_type(self, type_map, filter={}):
        cond = self.normalize_filter(filter)
        ps = [{'$set': {k:{f'${v}': f'${k}'}}} for k, v in type_map.items()]
        return self.collection.update_many(cond, ps)

    def query_set(self):
        return QuerySet(self.collection)