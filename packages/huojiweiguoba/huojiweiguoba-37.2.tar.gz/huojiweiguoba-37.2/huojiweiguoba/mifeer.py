
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

env_path = find_dotenv(os.path.join(os.path.expanduser('~'), '.mifeer'))
assert env_path, "Not found .mifeer"
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
    id = peewee.PrimaryKeyField()
    plat_name = peewee.CharField(verbose_name='平台名称', null=True)
    finance_shop_name = peewee.CharField(verbose_name='财务店铺名称', null=True,unique=True)
    erp_shop_name = peewee.CharField(verbose_name='ERP店铺名称', null=True,unique=True)
    erp_shop_id = peewee.IntegerField(verbose_name='ERP店铺id', null=True,unique=True)
    plat_shop_name = peewee.CharField(verbose_name='平台店铺名称', null=True)
    plat_shop_id = peewee.IntegerField(verbose_name='平台店铺id', null=True,unique=True)
    cookies_1 = peewee.TextField(verbose_name='cookie1', null=True)
    cookies_2 = peewee.TextField(verbose_name='cookie2', null=True)
    cookies_3 = peewee.TextField(verbose_name='cookie3', null=True)
    is_enable = peewee.BooleanField(default=1, verbose_name='是否启用')


db.connect()
db.create_tables([Shops], safe=True)


class ShopsSdk:

    def __init__(self):
        pass

    def query(self,id=None,p_name=None,fs_name=None,es_name=None,es_id=None,ps_name=None,ps_id=None):
        '''查询'''
        shops = Shops.select()
        if id:
            shops = shops.where(Shops.id == id)
        if p_name:
            shops = shops.where(Shops.plat_name == p_name)
        if fs_name:
            shops = shops.where(Shops.finance_shop_name == fs_name)
        if es_name:
            shops = shops.where(Shops.erp_shop_name == es_name)
        if es_id:
            shops = shops.where(Shops.erp_shop_id == es_id)
        if ps_name:
            shops = shops.where(Shops.plat_shop_name == ps_name)
        if ps_id:
            shops = shops.where(Shops.plat_shop_id == ps_id)
        return [x.__idata__ for x in shops]

    def insert(self, p_name: str,fs_name=None, es_name: str = None, es_id: int = None, ps_name: str = None, ps_id: int = None,
               c1: str = None,
               c2: str = None, c3: str = None):
        '''新增'''
        create_resp = Shops.create(
            plat_name=p_name,
            erp_shop_name=es_name, erp_shop_id=es_id, plat_shop_name=ps_name,
            plat_shop_id=ps_id, cookies_1=c1, cookies_2=c2, cookies_3=c3,
            finance_shop_name=fs_name
        )
        return {"status": True, "message": "新增成功", "data": create_resp}

    def update(self, id, p_name:str=None,fs_name=None, es_name: str = None, es_id: int = None, ps_name: str = None, ps_id: int = None,
               c1: str = None,
               c2: str = None, c3: str = None):
        '''更新'''
        obj = Shops.get(id=id)
        if not obj:
            raise ValueError("店铺不存在")
        if p_name:
            obj.plat_name = p_name
        if fs_name:
            obj.finance_shop_name = fs_name
        if es_name:
            obj.erp_shop_name = es_name
        if es_id:
            obj.erp_shop_id = es_id
        if ps_name:
            obj.plat_shop_name = ps_name
        if ps_id:
            obj.plat_shop_id = ps_id
        if c1:
            obj.cookies_1 = c1
        if c2:
            obj.cookies_2 = c2
        if c3:
            obj.cookies_3 = c3
        obj.save()
        return {"status": True, "message": "更新成功", "data": obj.__idata__}

    def delete(self, id):
        '''删除'''
        obj = Shops.get(id=id)
        if not obj:
            raise ValueError("店铺不存在")
        obj.delete_instance()
        return {"status": True, "message": "删除成功", "data": obj.__idata__}

shops_sdk = ShopsSdk()
