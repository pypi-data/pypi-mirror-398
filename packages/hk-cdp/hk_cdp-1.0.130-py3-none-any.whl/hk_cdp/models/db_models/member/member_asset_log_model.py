# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-07-11 10:35:57
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class MemberAssetLogModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(MemberAssetLogModel, self).__init__(MemberAssetLog, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class MemberAssetLog:
    def __init__(self):
        super(MemberAssetLog, self).__init__()
        self.id = 0
        self.business_id = 0  # 商家标识
        self.scheme_id = 0 # 体系标识
        self.change_no = ""  # 变更流水号
        self.one_id = ""  # one_id
        self.user_id = ""  # 客户ID
        self.log_title = ""  # 标题
        self.asset_type = 0  # 资产类型(1-积分 2-成长值)
        self.asset_object_id = ""  # 资产对象标识
        self.store_id = 0  # 店铺标识
        self.business_type = 0  # 业务类型(0-初始化 1-订单赠送 2-退单扣减 3-人工调整 4-互动 5-官方直发)
        self.source_type = 0  # 来源类型(1-好客会员 2-忠诚度管理 3-淘宝会员通 4-抖音会员通 5-京东会员通)
        self.source_object_id = ""  # 来源对象标识(订单奖励来源为订单号)
        self.source_object_name = ""  # 来源对象名称
        self.operate_type = 0  # 变更类型 （0-发放 1-消费 2-过期 3-作废）
        self.operate_value = 0  # 操作值
        self.surplus_value = 0  # 剩余值
        self.history_value = 0  # 历史值
        self.processed_price = 0  # 已处理金额
        self.valid_type = 0  # 有效期类型(1-永久有效 2-指定时间)
        self.valid_end_date = '1970-01-01 00:00:00.000'  # 有效期结束时间
        self.remark = ""  # 备注
        self.operate_user_id = ""  # 操作用户标识
        self.operate_user_name = ""  # 操作用户名称
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'business_id', 'scheme_id', 'change_no', 'one_id', 'user_id', 'log_title', 'asset_type', 'asset_object_id', 'store_id', 'business_type', 'source_type', 'source_object_id', 'source_object_name', 'operate_type', 'operate_value', 'surplus_value', 'history_value',
            'processed_price', 'valid_type', 'valid_end_date', 'remark', 'operate_user_id', 'operate_user_name', 'create_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "member_asset_log_tb"
