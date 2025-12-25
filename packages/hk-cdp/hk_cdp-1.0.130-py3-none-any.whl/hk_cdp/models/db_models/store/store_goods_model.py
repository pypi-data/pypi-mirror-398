# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-12-26 19:49:36
@LastEditTime: 2025-10-27 18:07:24
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class StoreGoodsModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(StoreGoodsModel, self).__init__(StoreGoods, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class StoreGoods:
    def __init__(self):
        super(StoreGoods, self).__init__()
        self.id = 0  # ID
        self.guid = ""  # GUID
        self.business_id = 0  # 商家标识
        self.store_id = 0  # 店铺标识
        self.platform_id = 0  # 平台标识
        self.plat_store_id = ""  # 平台店铺标识
        self.cid = ""  # 分类ID
        self.goods_id = ""  # 商品ID
        self.goods_code = ""  # 商家编码
        self.goods_name = ""  # 商品名称
        self.goods_pic = ""  # 商品主图片
        self.approve_status = ""  # 商品状态
        self.price = 0.0000  # 商品价格
        self.goods_num = 0  # 商品件数
        self.create_date = "1970-01-01 00:00:00.000"  # 创建时间
        self.modify_date = "1970-01-01 00:00:00.000"  # 修改时间
        self.is_delete = 0  # 是否删除

    @classmethod
    def get_field_list(self):
        return ['id', 'guid', 'business_id', 'store_id', 'platform_id', 'plat_store_id', 'cid', 'goods_id', 'goods_code', 'goods_name', 'goods_pic', 'approve_status', 'price', 'goods_num', 'create_date', 'modify_date', 'is_delete']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "store_goods_tb"
