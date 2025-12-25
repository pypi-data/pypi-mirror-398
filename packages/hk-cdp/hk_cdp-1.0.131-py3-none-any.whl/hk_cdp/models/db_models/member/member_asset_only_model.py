# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-12-23 15:03:02
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class MemberAssetOnlyModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(MemberAssetOnlyModel, self).__init__(MemberAssetOnly, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类


class MemberAssetOnly:
    def __init__(self):
        super(MemberAssetOnly, self).__init__()
        self.id = 0
        self.change_no = ""  # 变更流水号(流水表的流水号)
        self.only_type = 0  # 唯一类型(1-请求 2-订单)
        self.only_id = 0  # 唯一标识(用于幂等)
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间

    @classmethod
    def get_field_list(self):
        return ['id', 'change_no', 'only_type', 'only_id', 'create_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "member_asset_only_tb"
