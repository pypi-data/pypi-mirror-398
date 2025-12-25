# -*- coding: utf-8 -*-
"""
:Author: HuangJianYi
:Date: 2020-05-12 20:11:48
@LastEditTime: 2025-12-23 15:04:31
@LastEditors: HuangJianYi
:description: 
"""
from datetime import timedelta
from seven_cloudapp_frame.libs.common import *
from seven_cloudapp_frame.libs.customize.seven_helper import *
from seven_cloudapp_frame.libs.customize.safe_helper import SafeHelper
from hk_cdp.models.db_models.member.member_asset_model import *
from hk_cdp.models.db_models.member.member_asset_log_model import *
from hk_cdp.models.db_models.member.member_asset_valid_model import *
from hk_cdp.models.db_models.member.member_asset_only_model import *
from hk_cdp.models.cdp_model import CacheKey
from seven_cloudapp_frame.models.seven_model import *
from seven_cloudapp_frame.models.frame_base_model import *
import hashlib


class AssetBaseModel():
    """
    :description: 资产管理业务模型,主要管理会员资产
    """

    def __init__(self, context=None, logging_error=None, logging_info=None, db_config_dict=None):
        self.context = context
        self.logging_link_error = logging_error
        self.logging_link_info = logging_info
        self.db_config_dict = db_config_dict


    def get_member_asset_id_md5(self, one_id, asset_type, asset_object_id):
        """
        :description: 生成资产id_md5
        :param one_id：用户one_id
        :param asset_type：资产类型(1-积分 2-成长值)
        :param asset_object_id：对象标识
        :return: 用户资产唯一标识
        :last_editors: HuangJianYi
        """
        if not one_id or not asset_type:
            return 0
        string_to_hash = f"{one_id}_{asset_type}_{asset_object_id}"
        return hashlib.md5(string_to_hash.encode()).hexdigest()

    def get_asset_check_code(self, one_id, asset_value, sign_key):
        """
        :description: 生成资产校验码
        :param one_id：用户one_id
        :param asset_value：当前资产值
        :param sign_key：签名key,目前使用business_id作为签名key
        :return: 用户资产校验码
        :last_editors: HuangJianYi
        """
        if not one_id or not asset_value:
            return ""
        return CryptoHelper.md5_encrypt(f"{one_id}_{asset_value}_{sign_key}")

    def check_and_reset_asset(self, member_asset_dict: dict, business_id: str):
        """
        :description:检查并重置资产值（如果校验失败）
        :param member_asset_dict: 会员资产字典
        :param business_id: 商家标识
        """
        if member_asset_dict and share_config.get_value("is_check_asset", True) == True:
            if SafeHelper.authenticat_app_id(member_asset_dict["business_id"], business_id) == False:
                member_asset_dict["asset_value"] = 0
            else:
                asset_check_code = self.get_asset_check_code(member_asset_dict["id_md5"], member_asset_dict["asset_value"], business_id)
                if asset_check_code != member_asset_dict["asset_check_code"]:
                    member_asset_dict["asset_value"] = 0
        return member_asset_dict

    def update_member_asset(self,
                            business_id,
                            store_id,
                            one_id,
                            user_id,
                            asset_type,
                            asset_value,
                            operate_type,
                            business_type,
                            source_type,
                            source_object_id,
                            source_object_name,
                            log_title,
                            asset_object_id='',
                            remark='',
                            operate_user_id='',
                            operate_user_name='',
                            valid_end_date=None,
                            scheme_id=0,
                            only_info_dict=None):
        """
        :description: 变更资产
        :param business_id：商家标识
        :param store_id：店铺标识
        :param one_id：用户one_id
        :param user_id：客户ID
        :param asset_type：资产类型(1-积分 2-成长值)
        :param asset_value：变动的资产值，比如原本是100现在变成80，应该传入-20,原本是100现在变成120，应该传入20
        :param operate_type：变更类型 （0-发放 1-消费 2-过期 3-作废）
        :param business_type：业务类型(0-初始化 1-订单赠送 2-退单扣减 3-人工调整 4-互动 5-官方直发)
        :param source_type：来源类型(1-好客会员 2-忠诚度管理 3-淘宝会员通 4-抖音会员通 5-京东会员通)                                   
        :param source_object_id：来源对象标识(订单奖励来源为订单号) 
        :param source_object_name：来源对象名称(比如来源类型是任务则对应任务名称)
        :param log_title：资产流水标题
        :param asset_object_id：资产对象标识
        :param remark：备注
        :param operate_user_id:操作用户标识
        :param operate_user_name:操作用户名称
        :param valid_end_date：有效期结束时间（时间格式，不传或默认时间，则表示永久有效）
        :param scheme_id：体系标识，必传
        :param only_info_dict：唯一信息字典，用于幂等性判断，{"only_type": 1, "only_id": "唯一类型(1-请求 2-订单)"}
        :return: 返回实体InvokeResultData
        :last_editors: HuangJianYi
        """

        invoke_result_data = InvokeResultData()

        if not one_id or not asset_type or not asset_value or not scheme_id:
            invoke_result_data.success = False
            invoke_result_data.error_code = "param_error"
            invoke_result_data.error_message = "参数不能为空或等于0"
            return invoke_result_data

        asset_value = int(asset_value)
        member_asset_id_md5 = self.get_member_asset_id_md5(one_id, asset_type, asset_object_id)
        if member_asset_id_md5 == 0:
            invoke_result_data.success = False
            invoke_result_data.error_code = "error"
            invoke_result_data.error_message = "修改失败"
            return invoke_result_data

        db_transaction = DbTransaction(db_config_dict=self.db_config_dict, context=self.context)
        member_asset_model = MemberAssetModel(db_config_dict=self.db_config_dict, db_transaction=db_transaction, context=self.context, sub_table=str(asset_type))
        member_asset_log_model = MemberAssetLogModel(db_config_dict=self.db_config_dict, db_transaction=db_transaction, context=self.context, sub_table=str(asset_type))
        member_asset_valid_model = MemberAssetValidModel(db_config_dict=self.db_config_dict, db_transaction=db_transaction, context=self.context, sub_table=str(asset_type))
        member_asset_only_model = MemberAssetOnlyModel(db_config_dict=self.db_config_dict, db_transaction=db_transaction, context=self.context, sub_table=str(asset_type))

        acquire_lock_name = f"memberasset:{member_asset_id_md5}"
        acquire_lock_status, identifier = SevenHelper.redis_acquire_lock(acquire_lock_name)
        if acquire_lock_status == False:
            invoke_result_data.success = False
            invoke_result_data.error_code = "acquire_lock"
            invoke_result_data.error_message = "系统繁忙,请稍后再试"
            return invoke_result_data

        try:
            now_datetime = SevenHelper.get_now_datetime()
            old_user_asset_id = 0
            history_asset_value = 0

            member_asset = member_asset_model.get_entity("id_md5=%s", params=[member_asset_id_md5])
            if member_asset:
                if member_asset.asset_value + asset_value < 0:
                    invoke_result_data.success = False
                    invoke_result_data.error_code = "no_enough"
                    invoke_result_data.error_message = "变更后的资产不能为负数"
                    return invoke_result_data
                if member_asset.asset_value + asset_value > 2147483647:
                    invoke_result_data.success = False
                    invoke_result_data.error_code = "no_enough"
                    invoke_result_data.error_message = "变更后的资产不能大于整形的最大值"
                    return invoke_result_data

                old_user_asset_id = member_asset.id
                history_asset_value = member_asset.asset_value
            else:
                if asset_value < 0:
                    invoke_result_data.success = False
                    invoke_result_data.error_code = "no_enough"
                    invoke_result_data.error_message = "资产不能为负数"
                    return invoke_result_data
                member_asset = MemberAsset()
                member_asset.id_md5 = member_asset_id_md5
                member_asset.business_id = business_id
                member_asset.one_id = one_id
                member_asset.asset_type = asset_type
                member_asset.asset_object_id = asset_object_id
                member_asset.create_date = now_datetime

            member_asset.asset_value += asset_value
            member_asset.asset_check_code = self.get_asset_check_code(member_asset_id_md5, member_asset.asset_value, business_id)
            if asset_value > 0:
                member_asset.total_incr_value += asset_value
            else:
                member_asset.total_decr_value += abs(asset_value)

            member_asset.modify_date = now_datetime

            member_asset_log = MemberAssetLog()
            member_asset_log.business_id = business_id
            member_asset_log.scheme_id = scheme_id
            member_asset_log.change_no = SevenHelper.create_order_id()  # 18位随机
            member_asset_log.one_id = one_id
            member_asset_log.user_id = user_id
            member_asset_log.log_title = log_title
            member_asset_log.asset_type = asset_type
            member_asset_log.asset_object_id = asset_object_id
            member_asset_log.store_id = store_id
            member_asset_log.business_type = business_type
            member_asset_log.source_type = source_type
            member_asset_log.source_object_id = source_object_id
            member_asset_log.source_object_name = source_object_name
            member_asset_log.operate_type = operate_type
            member_asset_log.operate_value = asset_value
            member_asset_log.surplus_value = asset_value if operate_type == 0 else 0  # 剩余积分(初始值为获取到的值)(仅发放时需要)
            member_asset_log.history_value = history_asset_value
            member_asset_log.remark = remark
            member_asset_log.operate_user_id = operate_user_id
            member_asset_log.operate_user_name = operate_user_name
            member_asset_log.valid_end_date = valid_end_date
            if valid_end_date and valid_end_date not in ["2900-01-01 00:00:00", "2900-01-01 00:00:00.000"]:
                member_asset_log.valid_type = 2
            else:
                member_asset_log.valid_type = 1
            member_asset_log.create_date = now_datetime

            update_asset_log_list = []
            if operate_type in [1, 3]: # 只有消费和作废需要，更新剩余值
                asset_log_list = member_asset_log_model.get_list(where="one_id=%s AND asset_type=1 AND operate_type=0 AND surplus_value>0", params=[one_id], order_by="valid_end_date ASC,create_date ASC")
                operate_value = asset_value
                for asset_log in asset_log_list:
                    if asset_log.surplus_value >= operate_value:
                        asset_log.history_value = asset_log.surplus_value  # 历史值为当前剩余值
                        asset_log.surplus_value -= operate_value  # 剩余值减少
                        update_asset_log_list.append(asset_log)
                        break
                    else:
                        asset_log.history_value = asset_log.surplus_value  # 历史值为当前剩余值
                        operate_value -= asset_log.surplus_value  # 操作值减少
                        asset_log.surplus_value = 0  # 剩余值为0
                        update_asset_log_list.append(asset_log)

                if only_info_dict:
                    member_asset_only = MemberAssetOnly()
                    member_asset_only.change_no = member_asset_log.change_no
                    member_asset_only.only_type = only_info_dict.get("only_type", 2)
                    member_asset_only.only_id = only_info_dict.get("only_id", '')
                    member_asset_only.create_date = now_datetime
            # 开始事务
            db_transaction.begin_transaction()
            if update_asset_log_list:
                member_asset_log_model.update_list(update_asset_log_list, field_list='history_value,surplus_value')
            if old_user_asset_id != 0:
                member_asset_model.update_entity(member_asset, "asset_value,asset_check_code,modify_date,total_incr_value,total_decr_value")
            else:
                member_asset_model.add_entity(member_asset)
            member_asset_log_model.add_entity(member_asset_log)
            if only_info_dict:
                member_asset_only_model.add_entity(member_asset_only)
            if member_asset_log.valid_type == 2:
                member_asset_valid = MemberAssetValid()
                member_asset_valid.change_no = member_asset_log.change_no
                member_asset_valid.valid_end_day = (TimeHelper.format_time_to_datetime(valid_end_date) + timedelta(days=1)).strftime("%Y%m%d")
                member_asset_valid.remark = member_asset_log.log_title
                member_asset_valid.create_date = now_datetime
                member_asset_valid_model.add_entity(member_asset_valid)

            # 执行事务
            result, message = db_transaction.commit_transaction(return_detail_tuple=True)
            if result == False:
                error_title = f"【变更资产】异常信息：{message},info:{SevenHelper.json_dumps(member_asset_log)}"
                if self.context:
                    self.context.logging_link_error(error_title)
                elif self.logging_link_error:
                    self.logging_link_error(error_title)
                invoke_result_data.success = False
                invoke_result_data.error_code = "fail"
                invoke_result_data.error_message = "系统繁忙,请稍后再试"
                return invoke_result_data

            member_asset_model.delete_dependency_key(CacheKey.member_asset(one_id))

            invoke_result_data.data = {"member_asset": member_asset.__dict__}

        except Exception as ex:
            if self.context:
                self.context.logging_link_error("【变更资产】" + traceback.format_exc())
            elif self.logging_link_error:
                self.logging_link_error("【变更资产】" + traceback.format_exc())
            invoke_result_data.success = False
            invoke_result_data.error_code = "exception"
            invoke_result_data.error_message = "系统繁忙,请稍后再试"
        finally:
            SevenHelper.redis_release_lock(acquire_lock_name, identifier)

        return invoke_result_data

    def get_member_asset_list(self, one_ids, business_id, asset_type=0):
        """
        :description: 获取用户资产列表
        :param one_ids：用户one_id 多个逗号,分隔
        :param business_id：商家标识
        :param asset_type：资产类型(1-积分 2-成长值)
        :return: 返回list
        :last_editors: HuangJianYi
        """
        if not one_ids:
            return []
        condition_where = ConditionWhere()
        params = []
        if one_ids:
            if isinstance(one_ids, str):
                condition_where.add_condition(f"one_id in ({one_ids})")
            elif isinstance(one_ids, list):
                condition_where.add_condition(SevenHelper.get_condition_by_int_list("one_id", one_ids))
            else:
                condition_where.add_condition("one_id=%s")
                params.append(one_ids)
        if asset_type != 0:
            condition_where.add_condition("asset_type=%s")
            params.append(asset_type)
        member_asset_model = MemberAssetModel(db_config_dict=self.db_config_dict, sub_table=str(asset_type), context=self.context)
        member_asset_dict_list = member_asset_model.get_dict_list(condition_where.to_string(), params=params)
        if len(member_asset_dict_list) > 0:
            for member_asset_dict in member_asset_dict_list:
                member_asset_dict = self.check_and_reset_asset(member_asset_dict, business_id)
        return member_asset_dict_list

    def get_member_asset(self, business_id, one_id, asset_type, asset_object_id="", is_cache=False):
        """
        :description: 获取具体的资产
        :param business_id：商家标识
        :param one_id：用户one_id
        :param asset_type：资产类型(1-积分 2-成长值)
        :param asset_object_id：资产对象标识,没有传空
        :param is_cache：是否缓存
        :return: 返回单条字典
        :last_editors: HuangJianYi
        """
        if not one_id or not asset_type:
            return None
        member_asset_model = MemberAssetModel(db_config_dict=self.db_config_dict, sub_table=str(asset_type), context=self.context)
        member_asset_id_md5 = self.get_member_asset_id_md5(one_id, asset_type, asset_object_id)
        if is_cache:
            member_asset_dict = member_asset_model.get_cache_dict("id_md5=%s", limit="1", params=[member_asset_id_md5], dependency_key=CacheKey.member_asset(one_id))
        else:
            member_asset_dict = member_asset_model.get_dict("id_md5=%s", limit="1", params=[member_asset_id_md5])
        member_asset_dict = self.check_and_reset_asset(member_asset_dict, business_id)
        return member_asset_dict

    def get_asset_log_list(self,
                           asset_type=0,
                           page_size=20,
                           page_index=0,
                           one_id='',
                           asset_object_id="",
                           start_date="",
                           end_date="",
                           source_type=0,
                           source_object_id=None,
                           field="*",
                           operate_type=-1,
                           business_type=-1,
                           page_count_mode="total"):
        """
        :description: 获取用户资产流水记录
        :param asset_type：资产类型(1-积分 2-成长值)
        :param page_size：条数
        :param page_index：页数
        :param one_id：用户one_id
        :param asset_object_id：资产对象标识
        :param start_date：开始时间
        :param end_date：结束时间
        :param source_type：来源类型(1-好客会员 2-忠诚度管理 3-淘宝会员通 4-抖音会员通 5-京东会员通)
        :param source_object_id：来源对象标识(比如来源类型是任务则对应任务类型)
        :param field：查询字段
        :param operate_type：变更类型 （-1全部0-发放 1-消费 2-过期 3-作废）
        :param business_type：业务类型(0-初始化 1-订单赠送 2-退单扣减 3-人工调整 4-互动 5-会员绑定 6-会员合并 7-官方直发 8-过期)
        :param page_count_mode: 分页计数模式 total-计算总数(默认) next-计算是否有下一页(bool) none-不计算
        :param module_id: 模块标识
        :return: 
        :last_editors: HuangJianYi
        """
        page_list = []

        condition_where = ConditionWhere()
        params = []
        if asset_type != 0:
            condition_where.add_condition("asset_type=%s")
            params.append(asset_type)
        if one_id != 0:
            condition_where.add_condition("one_id=%s")
            params.append(one_id)
        if asset_object_id:
            condition_where.add_condition("asset_object_id=%s")
            params.append(asset_object_id)
        if start_date:
            condition_where.add_condition("create_date>=%s")
            params.append(start_date)
        if end_date:
            condition_where.add_condition("create_date<=%s")
            params.append(end_date)
        if business_type != -1:
            condition_where.add_condition("business_type=%s")
            params.append(business_type)
        if source_type:
            if type(source_type) == str:
                condition_where.add_condition(SevenHelper.get_condition_by_int_list("source_type", [int(item) for item in source_type.split(",")]))
            elif type(source_type) == list:
                condition_where.add_condition(SevenHelper.get_condition_by_int_list("source_type", source_type))
            else:
                condition_where.add_condition("source_type=%s")
                params.append(source_type)
        if operate_type != -1:
            condition_where.add_condition("operate_type=%s")
            params.append(operate_type)
        if source_object_id:
            if type(source_object_id) == str:
                condition_where.add_condition(SevenHelper.get_condition_by_str_list("source_object_id", source_object_id.split(",")))
            elif type(source_object_id) == list:
                condition_where.add_condition(SevenHelper.get_condition_by_str_list("source_object_id", source_object_id))
            else:
                condition_where.add_condition("source_object_id=%s")
                params.append(source_object_id)
        member_asset_log_model = MemberAssetLogModel(db_config_dict=self.db_config_dict,sub_table=str(asset_type),context=self.context)
        page_list = member_asset_log_model.get_dict_page_list(field, page_index, page_size, condition_where.to_string(), order_by="id desc", params=params, page_count_mode=page_count_mode)
        result = None
        if page_count_mode in ['total', 'next']:
            result = page_list[1]
            page_list = page_list[0]
        if len(page_list) > 0:
            for item in page_list:
                item["create_day"] = TimeHelper.format_time_to_datetime(str(item["create_date"])).strftime('%Y-%m-%d')
        if page_count_mode in ['total', 'next']:
            return page_list, result
        return page_list

    def add_asset_log(self,
                      business_id,
                      one_id,
                      user_id,
                      asset_type,
                      asset_value,
                      asset_object_id,
                      store_id,
                      source_type,
                      source_object_id,
                      source_object_name,
                      log_title,
                      operate_type,
                      business_type,
                      history_asset_value=0,
                      remark="",
                      operate_user_id='',
                      operate_user_name='',
                      valid_end_date=None):
        """
        :description: 添加资产流水
        :param business_id：商家标识
        :param one_id：用户one_id
        :param user_id：客户ID
        :param asset_type：资产类型(1-积分 2-成长值)
        :param asset_value：变动的资产值，算好差值传入
        :param asset_object_id：资产对象标识
        :param source_type：来源类型(1-好客会员 2-忠诚度管理 3-淘宝会员通 4-抖音会员通 5-京东会员通)
        :param source_object_id：来源对象标识(比如来源类型是任务则对应任务类型)
        :param source_object_name：来源对象名称(比如来源类型是任务则对应任务名称)
        :param log_title：资产流水标题
        :param operate_type:变更类型 （0-发放 1-消费 2-过期 3-作废）
        :param business_type：业务类型(0-初始化 1-订单赠送 2-退单扣减 3-人工调整 4-互动 5-会员绑定 6-会员合并 7-官方直发 8-过期)
        :param operate_user_id:操作用户标识
        :param operate_user_name:操作用户名称
        :param remark:备注
        :param valid_end_date:有效期结束时间（时间格式，不传或默认时间，则表示永久有效）
        :return: 返回实体InvokeResultData
        :last_editors: HuangJianYi
        """
        asset_value = int(asset_value)
        member_asset_log_model = MemberAssetLogModel(db_config_dict=self.db_config_dict, sub_table=str(asset_type), context=self.context)
        member_asset_log = MemberAssetLog()
        member_asset_log.business_id = business_id
        member_asset_log.change_no = SevenHelper.create_order_id()
        member_asset_log.one_id = one_id
        member_asset_log.user_id = user_id
        member_asset_log.log_title = log_title
        member_asset_log.asset_type = asset_type
        member_asset_log.asset_object_id = asset_object_id
        member_asset_log.store_id = store_id
        member_asset_log.business_type = business_type
        member_asset_log.source_type = source_type
        member_asset_log.source_object_id = source_object_id
        member_asset_log.source_object_name = source_object_name
        member_asset_log.operate_type = operate_type
        member_asset_log.operate_value = asset_value
        member_asset_log.surplus_value = asset_value
        if valid_end_date and valid_end_date != "1970-01-01 00:00:00":
            member_asset_log.valid_end_date = valid_end_date
            member_asset_log.valid_type = 2
        else:
            member_asset_log.valid_type = 1
        member_asset_log.history_value = history_asset_value
        member_asset_log.remark = remark
        member_asset_log.operate_user_id = operate_user_id
        member_asset_log.operate_user_name = operate_user_name
        member_asset_log.create_date = SevenHelper.get_now_datetime()
        member_asset_log_model.add_entity(member_asset_log)
