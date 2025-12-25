# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-04-17 11:01:05
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class TaobaoSourceHistoryMemberModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TaobaoSourceHistoryMemberModel, self).__init__(TaobaoSourceHistoryMember, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class TaobaoSourceHistoryMember:
    def __init__(self):
        super(TaobaoSourceHistoryMember, self).__init__()
        self.ouid = "" # 外部用户ID
        self.store_id = "" # 店铺id
        self.grade = 0 # 等级编码
        self.grade_name = ""  # 等级名称
        self.snapshot_info = ""  # 版本拓展信息
        self.gmt_modified = '1900-01-01 00:00:00.000' # 记录最后修改时间
        self.points = "" # 消费者积分余额
        self.mix_mobile = "" # 加密手机号
        self.mobile = "" # 手机号
        self.mask_mobile = "" # 掩码手机号
        self.first_entry_time = "1900-01-01 00:00:00" # 首次入会时间
        self.last_entry_time = "1900-01-01 00:00:00" # 首次入会时间
        self.modify_time = "1900-01-01 00:00:00.000" # 修改时间
        self.create_time = "1900-01-01 00:00:00.000" # 创建时间

    @classmethod
    def get_field_list(self):
        return ["ouid", "store_id", "grade", "grade_name", "snapshot_info", "gmt_modified", "points", "mix_mobile", "mobile", 'mask_mobile', "first_entry_time", "last_entry_time", "modify_time", "create_time"]

    @classmethod
    def get_primary_key(self):
        return "ouid"

    def __str__(self):
        return "taobao_source_history_member_tb"
