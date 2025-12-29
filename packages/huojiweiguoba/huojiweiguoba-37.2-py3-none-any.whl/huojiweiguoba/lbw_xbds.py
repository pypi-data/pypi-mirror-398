import copy
import os.path
import inspect
import traceback

import peewee
from decimal import Decimal
from dotenv import find_dotenv, load_dotenv
from playhouse.shortcuts import ReconnectMixin
from playhouse.pool import PooledMySQLDatabase

env_path = find_dotenv(os.path.join(os.path.expanduser('~'), '.huojiweiguoba'))
assert env_path, "Not found .huojiweiguoba file"
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
        return data

    @classmethod
    def create_or_update(cls, **kwargs):
        for key in cls.unique_keys:
            assert key in kwargs, f"{key} is not in kwargs"
        try:
            obj = cls.select()
            for key in cls.unique_keys:
                assert key in kwargs, f"{key} is not in kwargs"
                obj = obj.where(getattr(cls, key) == kwargs[key])
            if not obj:
                cls.create(**kwargs)
                return "新增成功"
            else:
                obj = obj.get()
                for key, value in kwargs.items():
                    setattr(obj, key, value)
                obj.save()
                return "更新成功"
        except peewee.IntegrityError as e:
            traceback.print_exc()
            return "创建或更新失败"

    class Meta:
        database = db

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.unique_keys:
            cls._meta.indexes = [(tuple(cls.unique_keys), True)]

class Shops(BaseModel):
    unique_keys = ['shop_name']
    shop_name = peewee.CharField()
    shop_pallet = peewee.CharField()
    shop_cookies = peewee.TextField()
    shop_notes = peewee.CharField()
    is_open = peewee.BooleanField(default=1)

class PddPlatform(BaseModel):
    unique_keys = ['shop_id', 'date']
    shop_id = peewee.IntegerField()
    date = peewee.DateField()
    deal_amount = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='成交金额')
    refund_amount = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='退款金额')
    dd_search = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='多多搜索')
    dd_scene = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='多多场景')
    fxt = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='放心推')
    qztg = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='全站推广')
    bztg = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='标准推广')
    sptg = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品推广')

class JdPlatform(BaseModel):
    unique_keys = ['shop_id', 'date']
    shop_id = peewee.IntegerField()
    date = peewee.DateField()
    htkc = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='海投+快车推广')
    jbkk = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='价保扣扣')

db.connect()
db.create_tables([Shops], safe=True)
db.create_tables([PddPlatform], safe=True)
db.create_tables([JdPlatform], safe=True)
