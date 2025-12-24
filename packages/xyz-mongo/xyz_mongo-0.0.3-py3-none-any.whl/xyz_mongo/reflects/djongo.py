
from django.db.models import Model
from djongo import models as djongo_models
from datetime import datetime
from typing import Dict, Any, Tuple
from ..utils import loadMongoDB

# 推断字段类型 (Djongo字段类型映射)
def infer_field_type(value: Any) -> Tuple[type, Dict[str, Any]]:
    """将Python值推断为Djongo字段类型"""
    if isinstance(value, str):
        return (djongo_models.CharField, {'max_length': 255, 'null': True})
    elif isinstance(value, int):
        return (djongo_models.IntegerField, {'null': True})
    elif isinstance(value, float):
        return (djongo_models.FloatField, {'null': True})
    elif isinstance(value, bool):
        return (djongo_models.BooleanField, {'null': True})
    elif isinstance(value, datetime):
        return (djongo_models.DateTimeField, {'null': True})
    elif isinstance(value, list):
        # Djongo的ListField需要指定嵌套字段类型（这里默认用字符串）
        return (djongo_models.JSONField, {'null': True, 'default': list})
    elif isinstance(value, dict):
        # Djongo的DictField需要指定值类型（这里默认用字符串）
        return (djongo_models.JSONField, {'null': True, 'default': dict})
    else:
        # 默认用TextField（存储任意类型）
        return (djongo_models.TextField, {'null': True})


def reflect_mongo_document(collection_name: str, db_alias: str = 'default', sample_size: int = 10,
                           id_field: bool = True, **kwargs) -> type:
    """
    从MongoDB集合动态生成Djongo模型（基于样本文档）

    :param collection_name: MongoDB集合名称
    :param db_alias: 数据库别名（默认'default'）
    :param sample_size: 采样文档数量（默认10）
    :param id_field: 是否生成'db_id'字段（Djongo会自动处理主键，此字段为普通字段）
    :return: 动态生成的Djongo模型类
    """
    # 获取Djongo数据库连接
    try:
        db = loadMongoDB(**kwargs)
        collection = db[collection_name]
    except Exception as e:
        raise RuntimeError(f"数据库连接失败: {str(e)}") from e

    # 采样文档
    samples = list(collection.find().limit(sample_size))
    if not samples:
        raise ValueError(f"集合 '{collection_name}' 为空")

    # 合并所有字段（跳过系统字段）
    all_fields = {}
    for doc in samples:
        for key, value in doc.items():
            if key.startswith('_') or key == '_id':  # 跳过系统字段
                continue
            all_fields[key] = value


    # 生成字段定义
    fields = {}
    for key, value in all_fields.items():
        field_type, kwargs = infer_field_type(value)
        print(key, field_type)
        fields[key] = field_type(**kwargs)

    # 添加id字段（普通字段，非主键）
    if id_field:
        fields['id'] = djongo_models.CharField(max_length=255, null=True, default=None)

    # 生成模型类
    model_class = type(
        f"{collection_name.capitalize()}Model",
        (Model,),
        {
            '__module__': __name__,
            **fields,
            'Meta': type('Meta', (), {
                'db_table': collection_name,   # ⭐ 正确指定 mongo collection
                'managed': False,
                'app_label': 'xyz_mongo'
            })
        }
    )

    print(f"✅ 生成模型: {model_class.__name__} (集合: {collection_name})")
    print("   字段映射:", {k: v.__class__.__name__ for k, v in fields.items()})
    return model_class

