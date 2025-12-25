# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2024-11-14 15:22:28
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class MemberAssetModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(MemberAssetModel, self).__init__(MemberAsset, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class MemberAsset:
    def __init__(self):
        super(MemberAsset, self).__init__()
        self.id = 0
        self.id_md5 = ""  # id_md5
        self.business_id = 0  # 商家标识
        self.one_id = ""  # one_id
        self.asset_type = 0  # 资产类型(1-积分 2-成长值)
        self.asset_object_id = ""  # 资产对象标识
        self.asset_value = 0  # 资产值
        self.asset_check_code = ""  # 资产检验码(id+asset_value+加密签名)md5生成
        self.total_incr_value = 0  # 累计获得资产值
        self.total_decr_value = 0  # 累计消耗资产值
        self.total_expire_value = 0  # 累计过期资产值
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000'  # 修改时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'id_md5', 'business_id', 'one_id', 'asset_type', 'asset_object_id', 'asset_value', 'asset_check_code', 'total_incr_value', 'total_decr_value', 'total_expire_value', 'create_date', 'modify_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "member_asset_tb"
