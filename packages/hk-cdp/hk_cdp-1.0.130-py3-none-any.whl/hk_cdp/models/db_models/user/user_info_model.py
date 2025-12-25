# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-03-06 17:44:05
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class UserInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(UserInfoModel, self).__init__(UserInfo, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class UserInfo:
    def __init__(self):
        super(UserInfo, self).__init__()
        self.id = 0 # id
        self.user_id = "" # 客户ID
        self.user_nick = "" # 昵称
        self.avatar = "" # 头像
        self.business_id = 0 # 商家标识
        self.store_id = 0 # 店铺标识
        self.platform_id = 0 # 平台标识(1-淘宝 2-抖音 3-京东)
        self.scheme_id = 0 # 会员体系标识
        self.one_id = "" # 会员id
        self.omid = "" # 品牌用户标识（淘宝-omid 抖音-unionID）
        self.ouid = "" # 平台用户标识（ouid）
        self.telephone = "" # 最新入会手机号
        self.encrypt_telephone = "" # 最新入会手机号密文
        self.new_telephone = "" # 最新手机号
        self.one_id_telephone = "" # oneid手机号
        self.real_name = "" # 姓名
        self.birthday = "1970-01-01 00:00:00.000" # 生日
        self.sex = 0 # 性别(0-未知 1-男 2-女)
        self.email = "" # 邮箱
        self.province = "" # 省
        self.city = "" # 市
        self.address = "" # 地址
        self.career = "" # 职业
        self.marital_status = 0 # 婚姻状态(0-未知 1-已婚 2-未婚)
        self.init_one_id = "" # 初始one_id
        self.behavior_type = 0 # 最近入会行为类型(1-注册 2-绑定 3-激活)
        self.plat_store_id = "" # 平台店铺标识
        self.active_status = 0 # 会员激活状态(1-激活 0-未激活)
        self.active_date = "1970-01-01 00:00:00.000" # 会员激活时间
        self.join_source_type = 0 # 入会来源类型（1-会员历史备份数据导入 2-天猫会员通 3-抖音会员通）
        self.join_source_title = "" # 入会来源说明
        self.first_join_date = "1970-01-01 00:00:00.000" # 首次入会时间
        self.last_join_date = "1970-01-01 00:00:00.000" # 最近入会时间
        self.extend_info = {} # 扩展信息json（"real_name":"姓名","birthday":"生日","sex":"性别","email":"邮箱","address":"所在地址","career":"职业","marital_status":"婚姻状态"）
        self.user_status = 1 # 用户状态(0-删除 1-正常)
        self.member_status = 2 # 会员状态(1-会员 2-非会员)
        self.is_join_settled = 0 # 是否入会结算过（1-是 0-否）
        self.settled_date = "1970-01-01 00:00:00.000" # 结算时间
        self.create_date = "1970-01-01 00:00:00.000" # 创建时间
        self.modify_date = "1970-01-01 00:00:00.000" # 修改时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'user_id', 'user_nick', 'avatar', 'business_id', 'store_id', 'platform_id', 'scheme_id', 'one_id','omid', 'ouid', 'telephone', 'encrypt_telephone', 'new_telephone', 'one_id_telephone',
            'real_name', 'birthday', 'sex', 'email', 'province', 'city','address', 'career', 'marital_status', 'init_one_id', 'behavior_type',
            'plat_store_id', 'active_status', 'active_date','join_source_type', 'join_source_title', 'first_join_date', 'last_join_date', 'extend_info','user_status', 'member_status', 'is_join_settled', 'settled_date', 'create_date', 'modify_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "user_info_tb"
