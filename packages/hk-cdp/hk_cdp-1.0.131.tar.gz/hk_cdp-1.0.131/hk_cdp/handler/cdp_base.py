# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-12-13 11:45:32
@LastEditTime: 2025-01-13 15:49:22
@LastEditors: HuangJianYi
@Description: 
"""
from seven_cloudapp_frame.handlers.frame_base import *

from seven_cloudapp_frame.libs.customize.seven_helper import *


class TiktokSpiBaseHandler(FrameBaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def response_json_success(self, data=None, desc='success'):
        """
        :Description: 通用成功返回json结构
        :param desc: 返回结果描述
        :param data: 返回结果对象，即为数组，字典
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJingCan
        """
        return self.response_common(0, desc, data, {"is_success": 1})

    def response_json_error(self, code=200007, desc='系统服务错误或者异常，请稍后重试', data=None):
        """
        :Description: 通用错误返回json结构
        :param desc: 错误描述
        :param data: 错误编码
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJingCan
        """
        return self.response_common(code, desc, data, {"is_success": 0})

    def response_json_error_params(self, desc='params error'):
        """
        :Description: 通用参数错误返回json结构
        :param desc: 返错误描述
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJingCan
        """
        return self.response_common(1, desc)

    def response_common(self, code, desc="", data=None, log_extra_dict=None):
        """
        :Description: 输出公共json模型
        :param code: 返回结果标识
        :param desc: 返回结果描述
        :param data: 返回结果对象，即为数组，字典
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJingCan
        """
        if hasattr(data, '__dict__'):
            data = data.__dict__

        rep_dic = {}
        rep_dic['code'] = code
        rep_dic['message'] = desc
        rep_dic['data'] = data

        return self.http_response(SevenHelper.json_dumps(rep_dic), log_extra_dict)

    def response_json_error_sign(self):
        """
        :Description: 签名验证失败错误返回json结构
        :param desc: 返错误描述
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: HuangJingCan
        """
        return self.response_common(100001, '签名验证失败', None, {"is_success": 0})