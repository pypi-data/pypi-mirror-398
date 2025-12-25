# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-08-15 14:29:08
@LastEditTime: 2025-01-22 10:55:37
@LastEditors: HuangJianYi
@Description: 
"""
import hashlib
import hmac
import json

class TiktokSpiHelper:

    @classmethod
    def check_sign(self, context, sign, app_key, app_secret, timestamp, param_json=None, sign_method=None):
        """
        验证签名
        :param sign: 签名
        :param app_key: 应用key
        :param app_secret: 应用秘钥
        :param timestamp: 时间戳
        :param param_json: 请求参数
        :param sign_method: 签名方式，默认md5
        :return: 验证结果
        """
        try:
            if not param_json:
                json_params = json.loads(context.request.body)
                if json_params:
                    # 使用sorted()函数对字典的键进行排序
                    sorted_keys = sorted(json_params.keys())
                    # 创建排序后的字典
                    sorted_dict = {key: json_params[key] for key in sorted_keys}
                    # 将字典转换为没有空格的 JSON 字符串
                    param_json = json.dumps(sorted_dict, ensure_ascii=False, separators=(',', ':'))

            check_sign = self.spi_sign(app_key, app_secret, timestamp, param_json, sign_method)
            if sign != check_sign:
                return False
            else:
                return True

        except Exception as ex:
            print("check_sign:" + str(ex))
            return False

    @classmethod
    def spi_sign(self, app_key, app_secret, timestamp, param_json, sign_method):
        """
        生成签名
        :param app_key: 应用key
        :param app_secret: 应用秘钥
        :param timestamp: 时间戳
        :param param_json: 请求参数
        :param sign_method: 签名方式，默认md5
        :return: 签名
        """
        if param_json:
            # param_json = param_json.replace(" ", "+")
            sign_pattern = f"{app_secret}app_key{app_key}param_json{param_json}timestamp{timestamp}{app_secret}"
        else:
            sign_pattern = f"{app_secret}app_key{app_key}timestamp{timestamp}{app_secret}"
        print(sign_pattern)
        if sign_method == "hmac-sha256":
            return self.string_to_hmac(sign_pattern, app_secret)
        return self.string_to_md5(sign_pattern)

    @classmethod
    def string_to_md5(self, plain_text):
        try:
            md5code = hashlib.md5(plain_text.encode('utf-8')).hexdigest()
            return md5code
        except Exception as e:
            print(str(e))

    @classmethod
    def string_to_hmac(self, plain_text, app_secret):
        try:
            secret = app_secret.encode('utf-8')
            key_spec = secret
            mac = hmac.new(key_spec, msg=plain_text.encode('utf-8'), digestmod=hashlib.sha256)
            digest = mac.digest()
            return ''.join(f'{b:02x}' for b in digest)
        except Exception as e:
            print(str(e))


    # @classmethod
    # def xiaohongshu_spi_sign(self, app_key, app_secret, timestamp, version, method):
    #     """
    #     生成签名（小红书）
    #     :param app_key: 应用key
    #     :param app_secret: 应用秘钥
    #     :param timestamp: 时间戳
    #     :param param_json: 请求参数
    #     :param sign_method: 签名方式，默认md5
    #     :return: 签名
    #     """
    #     sign_pattern = f"{method}?appId={app_key}&timestamp={timestamp}&version={version}{app_secret}"
    #     return self.string_to_md5(sign_pattern)
