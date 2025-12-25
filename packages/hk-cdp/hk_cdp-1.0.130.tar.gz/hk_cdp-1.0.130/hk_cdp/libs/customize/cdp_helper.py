# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-11-18 18:57:33
@LastEditTime: 2025-11-05 13:49:33
@LastEditors: HuangJianYi
@Description: 帮助类
"""
import datetime
import math
from copy import deepcopy
from seven_cloudapp_frame.libs.customize.seven_helper import *
from seven_cloudapp_frame.libs.customize.safe_helper import *
from hk_cdp.models.enum import *


class CdpHelper:
    
    @classmethod
    def decrypt_cdp_db_config(self, cdp_db_config):
        """
        :description: 获取对应的数据库名
        :param business_code: 商家代码
        :param cdp_db_config: 数据库连接串
        :last_editors: HuangJianYi
        """
        return cdp_db_config

    @classmethod
    def get_business_db(self, business_code, cdp_db_config):
        """
        :description: 获取对应的数据库名
        :param business_code: 商家代码
        :param cdp_db_config: 数据库连接串
        :last_editors: HuangJianYi
        """
        cdp_db_config = SevenHelper.json_loads(cdp_db_config)
        rawdata_db_config = deepcopy(cdp_db_config)
        rawdata_db_config['db'] = f"hk_{business_code}_rawdata"
        return rawdata_db_config, cdp_db_config

    @classmethod
    def get_cdp_db(self, business_code, cdp_db_config):
        """
        :description: 获取cdp对应的数据库名
        :param business_code: 商家代码
        :param cdp_db_config: 数据库连接串
        :last_editors: HuangJianYi
        """
        cdp_db_config = SevenHelper.json_loads(cdp_db_config)
        if business_code not in cdp_db_config['db']:
            return None
        return cdp_db_config

    @classmethod
    def get_valid_date(self, valid_type, expire_type, expire_value, expire_year, expire_month, expire_day):
        """
        :description: 计算积分/成长值过期时间
        :param valid_type: 有效类型(1-永久有效 2-指定时间)
        :param expire_type: 过期类型(1-指定天 2-指定时间)
        :param expire_value: 过期值
        :param expire_year: 过期年
        :param expire_month: 过期月
        :param expire_day: 过期日
        :last_editors: HuangJianYi
        """
        if valid_type == ValidType.forever.value:
            return '2900-01-01 00:00:00'
        else:
            if expire_type == None:
                raise Exception("过期类型不能为空")
            if expire_type == ExpireType.appoint_day.value: # 指定天过期
                return (datetime.datetime.now() + datetime.timedelta(days=int(expire_value))).strftime("%Y-%m-%d 23:59:59")
            else:
                if expire_year != None and expire_month != None and expire_day !=None:
                    current_year = datetime.datetime.now().year
                    expire_date = datetime.datetime(current_year + int(expire_year), int(expire_month), int(expire_day), 23, 59, 59)
                    return expire_date.strftime("%Y-%m-%d 23:59:59")
                else:
                    raise Exception("过期年/过期月/过期日不能为空")

    @classmethod
    def get_valid_date_v2(self, scheme_level_dict, level_info_dict):
        """
        :description: 计算积分/成长值过期时间
        :param scheme_level_dict: scheme_level_dict
        :param level_info_dict: level_info_dict
        :last_editors: HuangJianYi
        """
        valid_type = scheme_level_dict['valid_type'] if scheme_level_dict and scheme_level_dict['is_unify_valid'] == 1 else level_info_dict.get('valid_type', 0)
        expire_type = scheme_level_dict['expire_type'] if scheme_level_dict and scheme_level_dict['is_unify_valid'] == 1 else level_info_dict.get('expire_type', 0)
        expire_value = scheme_level_dict['expire_value'] if scheme_level_dict and scheme_level_dict['is_unify_valid'] == 1 else level_info_dict.get('expire_value', 0)
        expire_year = scheme_level_dict['expire_year'] if scheme_level_dict and scheme_level_dict['is_unify_valid'] == 1 else level_info_dict.get('expire_year', None)
        expire_month = scheme_level_dict['expire_month'] if scheme_level_dict and scheme_level_dict['is_unify_valid'] == 1 else level_info_dict.get('expire_month', None)
        expire_day = scheme_level_dict['expire_day'] if scheme_level_dict and scheme_level_dict['is_unify_valid'] == 1 else level_info_dict.get('expire_day', None)
        if valid_type == ValidType.forever.value:
            return '2900-01-01 00:00:00'
        else:
            if expire_type is None:
                raise Exception("过期类型不能为空")
            if expire_type == ExpireType.appoint_day.value: # 指定天过期
                return (datetime.datetime.now() + datetime.timedelta(days=int(expire_value))).strftime("%Y-%m-%d 23:59:59")
            else:
                if expire_year is not None and expire_month is not None and expire_day is not None:
                    current_year = datetime.datetime.now().year
                    expire_date = datetime.datetime(current_year + int(expire_year), int(expire_month), int(expire_day), 23, 59, 59)
                    return expire_date.strftime("%Y-%m-%d 23:59:59")
                else:
                    raise Exception("过期年/过期月/过期日不能为空")

    @classmethod
    def reward_algorithm(self, value_type, reward_value):
        """
        :description: 奖励算法
        :param value_type: 算法类型(1-四舍五入 2-向上取整 3-向下取整)
        :param reward_value: 根据订单算法的值
        :last_editors: HuangJianYi
        """
        if value_type == RoundingType.half_up.value: # 四舍五入
            reward_value = round(reward_value)
        elif value_type == RoundingType.ceiling.value: # 向上取整
            reward_value = math.ceil(reward_value)
        elif value_type == RoundingType.floor.value: # 向下取整
            reward_value = math.floor(reward_value)
        return reward_value

    @classmethod
    def convert_order_status(self, platform_id, order_status):
        """
        :description: 转换各平台订单状态,统一各平台订单状态
        :param platform_id: 平台标识
        :param order_status: 订单状态
        :return: 统一后的订单状态
        :last_editors: HuangJianYi
        """
        order_status = str(order_status)
        if platform_id == 1:
            if order_status == "TRADE_CLOSED_BY_TAOBAO":
                return OrderStatus.TRADE_CANCEL.name
            elif order_status == "TRADE_NO_CREATE_PAY":
                return OrderStatus.WAIT_BUYER_PAY.name
            else:
                return order_status
        elif platform_id == 2:
            if order_status == "1":
                return OrderStatus.WAIT_BUYER_PAY.name
            elif order_status == "103":
                return OrderStatus.BUYER_PART_PAY.name
            elif order_status in ["2", "105"]:
                return OrderStatus.WAIT_SELLER_SEND_GOODS.name
            elif order_status == "101":
                return OrderStatus.SELLER_CONSIGNED_PART.name
            elif order_status == "3":
                return OrderStatus.WAIT_BUYER_CONFIRM_GOODS.name
            elif order_status == "5":
                return OrderStatus.TRADE_FINISHED.name
            elif order_status in ["21", "22", "39"]:
                return OrderStatus.TRADE_CLOSED.name
            elif order_status == "4":
                return OrderStatus.TRADE_CANCEL.name
            else:
                return order_status

    @classmethod
    def convert_refund_status(self, platform_id, refund_status):
        """
        :description: 转换各平台退款状态,统一各平台退款状态
        :param platform_id: 平台标识
        :param refund_status: 退款状态
        :return: 统一后的退款状态
        :last_editors: HuangJianYi
        """
        refund_status = str(refund_status)
        if platform_id == 1:
            return refund_status
        elif platform_id == 2:
            if refund_status == "1":
                return RefundStatus.WAIT_SELLER_AGREE.name
            elif refund_status == "3":
                return RefundStatus.SUCCESS.name
            elif refund_status == "4":
                return RefundStatus.SELLER_REFUSE_BUYER.name
            else:
                return RefundStatus.NO_REFUND.name

    @classmethod
    def mask_telephone_middle(self, phone_str):
        """
        :description:根据手机号长度返回首尾明文,中间掩码格式
        :param phone_str: 待处理的手机号
        :return: 处理后的手机号
        """
        value, status = SevenHelper.to_int(phone_str, return_status=True)
        if len(phone_str) == 11 and status == True:
            return phone_str[:3] + '*' * 4 + phone_str[-4:]
        else:
            return phone_str[:-4] + '****'

    @classmethod
    def mask_telephone_first(self, phone_str):
        """
        :description:根据手机号长度返回中间明文,首尾掩码格式
        :param phone_str: 待处理的手机号
        :return: 处理后的手机号
        """
        value, status = SevenHelper.to_int(phone_str, return_status=True)
        if status and len(phone_str) == 11:
            return '*' * 3 + phone_str[3:-4] + '*' * 4
        elif phone_str.startswith('+'):
            return f'+{"*" * (len(phone_str) - 5)}{phone_str[-4:]}'
        else:
            return f'{"*" * (len(phone_str) - 4)}{phone_str[-4:]}'

    @classmethod
    def convert_sync_platform_info(self, business_id, one_id, total_integral, old_integral, change_integral, level_id=None, level_valid_date=None):
        """
        :description:合成同步平台需要的信息
        :param business_id: 商家标识
        :param one_id: 老会员的one_id
        :param total_integral: 总积分
        :param old_integral: 历史积分
        :param change_integral: 变动积分
        :param level_id: 等级id
        :param level_valid_date: 等级有效期
        :return: 
        """
        sync_member_info, sync_integral_log = "", ""
        if level_id and level_valid_date:
            level_valid_date = str(level_valid_date)
            sync_member_info = SevenHelper.json_dumps({
                "business_id": business_id,
                "one_id": one_id,
                "version":  TimeHelper.get_now_timestamp(True),
                "point": total_integral,
                "level": level_id,
                "level_expire_time": TimeHelper.format_time_to_timestamp(level_valid_date, out_ms=True)
            })
        if change_integral > 0:
            sync_integral_log = SevenHelper.json_dumps({
                "business_id": business_id,
                "one_id": one_id,
                "operate_type": 1,
                "channel": 100,
                "biz_scene": 100,
                "point_type": 1,
                "raw_quantity":change_integral,
                "serial_no": SevenHelper.create_order_id(),
                "change_time": TimeHelper.get_now_timestamp(True),
                "old_total_point": old_integral,
                "total_point": total_integral
            })
        return sync_member_info, sync_integral_log

    @classmethod
    def get_platform_name(self, platform_id):
        """
        :description:获取平台名称
        :param platform_id: 平台标识
        :return: 
        """
        if platform_id == 1:
            return '淘宝平台'
        elif platform_id == 2:
            return '抖音平台'
        elif platform_id == 3:
            return '京东平台'
        elif platform_id == 4:
            return '微信平台'
        else:
            return '未知平台'
