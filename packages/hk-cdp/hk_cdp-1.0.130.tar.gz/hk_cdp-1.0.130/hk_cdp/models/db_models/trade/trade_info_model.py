# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-06-18 14:05:21
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class TradeInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TradeInfoModel, self).__init__(TradeInfo, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class TradeInfo:
    def __init__(self):
        super(TradeInfo, self).__init__()
        self.id = 0 # id
        self.main_pay_order_no = "" # 主订单号
        self.store_id = 0 # 店铺标识
        self.business_id = 0 # 商家标识
        self.one_id = "" # one_id
        self.user_id = "" # 客户ID
        self.ouid = "" # ouid
        self.platform_id = 0 # 平台标识
        self.seller_nick = "" # 卖家昵称
        self.trade_type = "" # 交易类型
        self.step_trade_status = "" # 分阶段付款的订单状态
        self.order_price = 0.0 # 订单金额
        self.pay_price = 0.0 # 支付金额
        self.postage = 0.0 # 邮费
        self.discount_price = 0.0 # 优惠金额
        self.refund_price = 0.0 # 退款金额
        self.settle_price = 0.0 # 结算金额
        self.buy_num = 0 # 商品件数
        self.order_num = 0 # 子订单数量
        self.order_status = "" # 订单状态
        self.plat_store_id = "" # 平台店铺标识
        self.receiver = "" # 收货人
        self.telephone = "" # 收货人手机号
        self.receiver_province = "" # 收货人所在省份
        self.receiver_city = "" # 收货人所在城市
        self.receiver_county = "" # 收货人所在城区
        self.receiver_address = "" # 收货人所在地址
        self.buyer_remark = ""  # 买家备注
        self.seller_remark = "" # 卖家备注
        self.seller_flag = 0 # 卖家备注旗帜
        self.buyer_rate = 0 # 买家是否已评价(0-未评价 1-已评价)
        self.seller_rate = 0 # 卖家是否已评价(0-未评价 1-已评价)
        self.expand_card_basic_price = 0  # 购物金金额
        self.trade_source_types = "" # 交易内部来源。WAP(手机);HITAO(嗨淘);TOP(TOP平台);TAOBAO(普通淘宝);JHS(聚划算)一笔订单可能同时有以上多个标记，则以逗号分隔
        self.create_date = "1970-01-01 00:00:00.000" # 下单时间
        self.pay_date = "1970-01-01 00:00:00.000" # 付款时间
        self.consign_date = "1970-01-01 00:00:00.000" # 发货时间
        self.end_date = "1970-01-01 00:00:00.000" # 交易结束时间。交易成功时间(更新交易状态为成功的同时更新)/确认收货时间或者交易关闭时间
        self.source_type = 0 # 来源类型（1-历史备份数据导入 2-天猫会员通 3-抖音会员通）
        self.source_title = "" # 来源说明
        self.modify_date = "1970-01-01 00:00:00.000" # 修改时间(跟rds同步)
        self.inside_date = "1970-01-01 00:00:00.000"  # 内部修改时间(用于触发订单变动相关业务)
        self.is_incr_data = 0 # 是否增量数据(1-是 0-否)
        self.process_date = "1970-01-01 00:00:00.000" # 处理时间
        self.reward_process_status = 0  # 奖励处理状态：0-无需处理1-待处理2-已处理3-延迟处理10-订单异常
        self.refund_process_status = 0 # 退款处理状态(0-无需处理 1-待处理 2-已处理 10-订单异常)
        self.surplus_refund_price = 0 # 剩余退款金额

    @classmethod
    def get_field_list(self):
        return [
            'id', 'main_pay_order_no', 'store_id', 'business_id', 'one_id', 'user_id', 'ouid', 'platform_id', 'seller_nick', 'trade_type', 'step_trade_status', 'order_price', 'pay_price', 'postage', 'discount_price', 'refund_price', 'settle_price', 'buy_num', 'order_num',
            'order_status', 'plat_store_id', 'receiver', 'telephone', 'receiver_province', 'receiver_city', 'receiver_county', 'receiver_address', 'buyer_remark', 'seller_remark', 'seller_flag', 'buyer_rate', 'seller_rate', 'expand_card_basic_price', 'trade_source_types',
            'create_date', 'pay_date', 'consign_date', 'end_date', 'source_type', 'source_title', 'modify_date', 'inside_date', 'is_incr_data', 'process_date', 'reward_process_status', 'refund_process_status', 'surplus_refund_price'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "trade_info_tb"
