from mongoengine import *
from mongoengine.fields import *
from .config import DB, SERVER
import datetime
register_connection('default', db=DB, host=SERVER)

def infer_field_type(value):
    """根据值推断 MongoEngine 字段类型"""
    if isinstance(value, str):
        return StringField()
    elif isinstance(value, bool):
        return BooleanField()
    elif isinstance(value, int):
        return IntField()
    elif isinstance(value, float):
        # 注意：MongoDB 中整数也可能存为 float，需更精细判断
        return FloatField()
    elif isinstance(value, dict):
        # 嵌套文档：可递归处理，此处简化为 DictField
        return DictField()
    elif isinstance(value, list):
        if len(value) == 0:
            return ListField()
        else:
            # 简单取第一个元素类型
            inner_field = infer_field_type(value[0])
            return ListField(inner_field)
    elif isinstance(value, datetime.datetime):
        return DateTimeField()
    else:
        return DynamicField()  # 兜底


def reflect_mongo_document(collection_name: str, db_alias='default', sample_size=10):
    """
    动态生成 MongoEngine Document 类，基于 collection 中的样本文档
    """
    from mongoengine import get_db

    db = get_db(db_alias)
    collection = db[collection_name]

    # 采样若干文档
    samples = list(collection.find().limit(sample_size))
    if not samples:
        raise ValueError(f"Collection '{collection_name}' is empty.")

    # 合并所有字段（取并集）
    all_fields = {}
    for doc in samples:
        for key, value in doc.items():
            if key.startswith('_'):  # 跳过 _id 等系统字段
                continue
            if key not in all_fields:
                all_fields[key] = value

    # 推断字段类型
    attrs = {}
    for key, value in all_fields.items():
        attrs[key] = infer_field_type(value)

    # 创建动态类
    dynamic_class = type(
        collection_name.capitalize(),
        (DynamicDocument,),  # 使用 DynamicDocument 更安全
        {
            'meta': {
                'collection': collection_name,
                'db_alias': db_alias,
            },
            **attrs
        }
    )
    return dynamic_class
