# -*- coding: utf-8 -*-
"""
@Author: 彩虹库处理类
@Date: 2024-10-22 13:43:02
@LastEditTime: 2025-04-17 15:24:10
@LastEditors: HuangJianYi
@Description: 彩虹库处理类 
"""
from seven_cloudapp_frame.handlers.frame_base import *


class RainbowHelper:
    """
    :description: 彩虹库处理类
    """
    def __init__(self,context=None,logging_error=None,logging_info=None):
        self.context = context
        self.logging_link_error = logging_error
        self.logging_link_info = logging_info

    def get_clear_text_phone(self, store_id, mix_mobile, is_cache=True):
        """
        :description: 获取明文手机号
        :param store_id: 店铺标识
        :param mix_mobile: 密文手机号
        :param is_cache: 是否使用缓存
        :return: invoke_result_data
        :last_editors: HuangJianYi
        """
        redis_key = f"tmall_member_clear_text_phone:mix_mobile_{mix_mobile}"
        invoke_result_data = InvokeResultData()
        try:
            redis_init = SevenHelper.redis_init()
            phone = ""
            if is_cache:
                phone = redis_init.get(redis_key)
            if not phone:
                rainbow_url = share_config.get_value("rainbow_url", "") + f"?store={store_id}&code={mix_mobile}"
                result = requests.get(url=rainbow_url)
                result_data = SevenHelper.json_loads(result.text) if result and result.reason == 'OK' else {}
                if not result_data or result_data.get("desc","") != "success":
                    invoke_result_data.success = False
                    invoke_result_data.error_message = result_data.get("desc", "彩虹库接口异常")
                    return invoke_result_data
                phone = result_data["data"]
                if phone:
                    redis_init.set(redis_key, str(phone), ex=3600)
            invoke_result_data.data = phone
        except Exception as ex:
            if self.context:
                self.context.logging_link_error("【获取明文手机号异常】" + traceback.format_exc())
            elif self.logging_link_error:
                self.logging_link_error("【获取明文手机号异常】" + traceback.format_exc())
            invoke_result_data.success = False
            invoke_result_data.error_message = "获取手机号异常"
        return invoke_result_data
