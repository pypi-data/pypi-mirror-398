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

class MemberLevelLogModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(MemberLevelLogModel, self).__init__(MemberLevelLog, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class MemberLevelLog:
    def __init__(self):
        super(MemberLevelLog, self).__init__()
        self.id = 0
        self.business_id = 0  # 商家标识
        self.scheme_id = 0 # 体系标识
        self.change_no = ""  # 变更流水号
        self.one_id = ""  # one_id
        self.log_title = ""  # 标题
        self.source_type = 0  # 来源类型(1-系统 2-人工)
        self.source_object_id = ""  # 来源对象标识
        self.source_object_name = ""  # 来源对象名称
        self.operate_type = 0  # 变更类型 （0-初始化 1-升级 2-降级 3-保级）
        self.old_level_id = 0  # 变更前等级标识
        self.new_level_id = 0  # 变更后等级标识
        self.valid_type = 0  # 有效期类型(1-永久有效 2-指定时间)
        self.level_valid_date = '1970-01-01 00:00:00.000'  # 会员等级有效期
        self.remark = ""  # 备注
        self.operate_user_id = ""  # 操作用户标识
        self.operate_user_name = ""  # 操作用户名称
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'business_id', 'scheme_id', 'change_no', 'one_id', 'log_title', 'source_type', 'source_object_id', 'source_object_name', 'operate_type', 'old_level_id', 'new_level_id', 'valid_type', 'level_valid_date', 'remark', 'operate_user_id', 'operate_user_name',
            'create_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "member_level_log_tb"
