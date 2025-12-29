import copy
import os.path
import inspect
import traceback
import datetime
import peewee

from decimal import Decimal
from dotenv import find_dotenv, load_dotenv
from playhouse.shortcuts import ReconnectMixin
from playhouse.pool import PooledMySQLDatabase

env_file_name = ".ysgj_manage"
env_path = find_dotenv(os.path.join(os.path.expanduser('~'), env_file_name))
assert env_path, f"Not found {env_file_name} file"
load_dotenv(env_path)
assert os.getenv('MYSQL_HOST'), "MYSQL_HOST is None"
assert os.getenv('MYSQL_U'), "MYSQL_USER is None"
assert os.getenv('MYSQL_P'), "MYSQL_PASSWORD is None"


class ReconnectDatabase(ReconnectMixin, PooledMySQLDatabase):
    '''防止连接丢失'''
    pass


db = ReconnectDatabase(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_U'),
    password=os.getenv('MYSQL_P'),
    database=os.getenv('MYSQL_DB')
)


class BaseModel(peewee.Model):
    id = peewee.AutoField(primary_key=True)
    unique_keys = None

    @property
    def __idata__(self):
        data = copy.deepcopy(self.__data__)
        for field_name, field_value in data.items():
            if isinstance(field_value, Decimal):
                data[field_name] = float(field_value)
            if isinstance(field_value, datetime.date):
                data[field_name] = field_value.strftime("%Y-%m-%d")
        return data

    @classmethod
    def batch_create_or_update(cls, data_list):
        """
        批量创建或更新数据（基于唯一键）

        Args:
            data_list: 字典列表，每个字典代表一条记录

        Returns:
            tuple: (新增数量, 更新数量, 失败数量, 错误信息列表)
        """
        if not cls.unique_keys:
            raise ValueError("该方法需要定义 unique_keys")

        create_count = 0
        update_count = 0
        fail_count = 0
        errors = []

        for data in data_list:
            try:
                # 构建查询条件
                query = cls.select()
                for key in cls.unique_keys:
                    if key not in data:
                        raise ValueError(f"缺少唯一键字段: {key}")
                    query = query.where(getattr(cls, key) == data[key])

                # 执行查询并处理
                existing_obj = query.first()
                if not existing_obj:
                    cls.create(**data)
                    create_count += 1
                else:
                    for key, value in data.items():
                        setattr(existing_obj, key, value)
                    existing_obj.save()
                    update_count += 1

            except Exception as e:
                fail_count += 1
                errors.append({
                    'data': data,
                    'error': str(e)
                })
                traceback.print_exc()

        return create_count, update_count, fail_count, errors

    @classmethod
    def query_all(cls, conditions=None, order_by=None, limit=None):
        """
        通用查询方法

        Args:
            conditions: 查询条件字典 {字段: 值} 或 peewee表达式
            order_by: 排序字段，如 '-id' 或 'name'
            limit: 限制返回条数

        Returns:
            查询结果列表
        """
        query = cls.select()

        # 处理查询条件
        if conditions:
            if isinstance(conditions, dict):
                for field, value in conditions.items():
                    if field.endswith('__in') and isinstance(value, (list, tuple)):
                        field_name = field.replace('__in', '')
                        query = query.where(getattr(cls, field_name).in_(value))
                    elif field.endswith('__like'):
                        field_name = field.replace('__like', '')
                        query = query.where(getattr(cls, field_name).contains(value))
                    elif field.endswith('__gt'):
                        field_name = field.replace('__gt', '')
                        query = query.where(getattr(cls, field_name) > value)
                    elif field.endswith('__gte'):
                        field_name = field.replace('__gte', '')
                        query = query.where(getattr(cls, field_name) >= value)
                    elif field.endswith('__lt'):
                        field_name = field.replace('__lt', '')
                        query = query.where(getattr(cls, field_name) < value)
                    elif field.endswith('__lte'):
                        field_name = field.replace('__lte', '')
                        query = query.where(getattr(cls, field_name) <= value)
                    elif field.endswith('__ne'):
                        field_name = field.replace('__ne', '')
                        query = query.where(getattr(cls, field_name) != value)
                    else:
                        query = query.where(getattr(cls, field) == value)
            else:
                # 支持直接传入peewee表达式
                query = query.where(conditions)

        # 处理排序
        if order_by:
            if order_by.startswith('-'):
                field_name = order_by[1:]
                query = query.order_by(getattr(cls, field_name).desc())
            else:
                query = query.order_by(getattr(cls, order_by))

        # 处理限制条数
        if limit:
            query = query.limit(limit)

        return list(query)

    class Meta:
        database = db

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.unique_keys:
            cls._meta.indexes = [(tuple(cls.unique_keys), True)]


class CookiesManagement(BaseModel):
    table_name = "cookies_management"
    unique_keys = ['platform_name', 'common_name', 'platform_user']
    management_id = peewee.PrimaryKeyField()
    platform_name = peewee.CharField(verbose_name='平台名')  # 平台名
    common_name = peewee.CharField(verbose_name='通用名')  # 通用名
    platform_user = peewee.CharField(verbose_name='平台账号')  # 平台账号
    platform_pwd = peewee.CharField(verbose_name='平台密码')  # 平台密码
    platform_salt = peewee.CharField(verbose_name='平台盐', null=True)  # 平台盐
    platform_cookies_1 = peewee.TextField(verbose_name='cookie1', null=True)
    platform_cookies_2 = peewee.TextField(verbose_name='cookie2', null=True)
    platform_cookies_3 = peewee.TextField(verbose_name='cookie3', null=True)


db.connect()
db.create_tables([CookiesManagement], safe=True)
