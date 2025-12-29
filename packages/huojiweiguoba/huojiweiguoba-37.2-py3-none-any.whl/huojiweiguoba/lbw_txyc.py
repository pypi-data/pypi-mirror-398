# -*- coding:utf-8 -*-
# ProjectName：jd_listing
# FileName：db.py
# Time：2024/9/28 上午9:45
# Author：侯文杰
# IDE：PyCharm

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

env_path = find_dotenv(os.path.join(os.path.expanduser('~'), '.huojiweiguoba'))
assert env_path, "Not found .huojiweiguoba file"
load_dotenv(env_path)
assert os.getenv('JD_MYSQL_HOST'), "MYSQL_HOST is None"
assert os.getenv('JD_MYSQL_USER'), "MYSQL_USER is None"
assert os.getenv('JD_MYSQL_PWD'), "MYSQL_PASSWORD is None"
assert os.getenv('JD_MYSQL_PORT'), "MYSQL_PASSWORD is None"
assert os.getenv('JD_MYSQL_DB'), "MYSQL_PASSWORD is None"

class ReconnectDatabase(ReconnectMixin, PooledMySQLDatabase):
    '''防止连接丢失'''
    pass

db = ReconnectDatabase(
    host=os.getenv('JD_MYSQL_HOST'),
    user=os.getenv('JD_MYSQL_USER'),
    port=int(os.getenv('JD_MYSQL_PORT')),
    password=os.getenv('JD_MYSQL_PWD'),
    database=os.getenv('JD_MYSQL_DB')
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

    # def __init_subclass__(cls, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     # 建立联合唯一索引
    #     if cls.unique_keys:
    #         cls._meta.indexes = [(tuple(cls.unique_keys), True)]

    def __str__(self):
        return str(self.__idata__)

class Shops(BaseModel):
    __table_name__ = 'shops'
    unique_keys = ['shop_name']
    shop_name = peewee.CharField()
    shop_h5st = peewee.TextField()
    shop_cookies = peewee.TextField()
    shop_notes = peewee.CharField()
    is_open = peewee.BooleanField(default=1)

    class Meta:
        indexes = (
            (("shop_name", "is_open"), True),
        )
class JdGoods(BaseModel):
    __table_name__ = 'jd_goods'
    unique_keys = ['goods_authorized_no', 'goods_spec']
    goods_cost = peewee.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品成本价')
    goods_brand = peewee.CharField(null=False, verbose_name='品牌')
    goods_genericName = peewee.CharField(null=False, verbose_name='药品通用名')
    goods_manufacturer = peewee.CharField(null=False, verbose_name='生产厂家')
    goods_authorized_no = peewee.CharField(null=False,verbose_name='批准文号')
    goods_spec = peewee.CharField(null=False,verbose_name='规格')
    goods_category = peewee.CharField(null=False,verbose_name='类目')
    goods_code = peewee.CharField(null=False,verbose_name='商品代码')
    goods_limit_address = peewee.CharField(null=False, verbose_name='限购地址')
    goods_notes = peewee.CharField(null=True, verbose_name='备注')
    goods_images_local_path = peewee.TextField(null=True, verbose_name='图片本地路径')
    goods_enabled = peewee.BooleanField(default=1, verbose_name='是否启用')

    class Meta:
        indexes = (
            (("goods_authorized_no", "goods_spec"), True),
        )


class JdListing(BaseModel):
    __table_name__ = 'jd_listing'
    unique_keys = ['shop_id', 'goods_id','create_index']
    shop_id = peewee.IntegerField()
    goods_id = peewee.IntegerField()
    create_index = peewee.IntegerField(null=False,verbose_name='创建索引',default=1)
    create_date_time = peewee.DateTimeField(null=False,verbose_name='创建时间',default=datetime.datetime.now)
    done_date_time = peewee.DateTimeField(null=True,verbose_name='完成时间')
    status = peewee.CharField(null=False,verbose_name='状态')
    done_msg = peewee.TextField(null=True, verbose_name='上架消息')
    done_babyid = peewee.CharField(null=True,verbose_name='宝贝ID')
    done_limit_address_msg = peewee.TextField(null=True, verbose_name='限购地址-消息')
    done_shop_promotion_msg = peewee.TextField(null=True, verbose_name='店铺促销-消息')
    done_image_template_msg = peewee.TextField(null=True, verbose_name='图片模板-消息')
    done_limit_address_status = peewee.BooleanField(null=True, verbose_name='限购地址-状态')
    done_shop_promotion_status = peewee.TextField(null=True, verbose_name='店铺促销-状态')
    done_image_template_status = peewee.TextField(null=True, verbose_name='图片模板-状态')
    done_goods_common_name = peewee.CharField(null=True, verbose_name='商品通用名')
    done_goods_brand = peewee.CharField(null=True, verbose_name='品牌')
    done_goods_69code = peewee.CharField(null=True, verbose_name='69码')

    class Meta:
        indexes = (
            (("shop_id", "goods_id", "create_index"), True),
        )

db.connect()
db.create_tables([Shops], safe=True)
db.create_tables([JdGoods], safe=True)
db.create_tables([JdListing], safe=True)
