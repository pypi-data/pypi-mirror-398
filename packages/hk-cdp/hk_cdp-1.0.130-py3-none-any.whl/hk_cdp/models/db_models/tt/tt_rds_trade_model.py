#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class TtRdsTradeModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TtRdsTradeModel, self).__init__(TtRdsTrade, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class TtRdsTrade:
    def __init__(self):
        super(TtRdsTrade, self).__init__()
        self.id = 0  # 主键id
        self.order_id = ""  # 订单id
        self.order_status = 0  # 订单状态
        self.order_type = 0  # 订单类型
        self.shop_id = 0  # 店铺id
        self.doudian_open_id = ""  # 加密用户id串
        self.create_time = 0  # 订单创建时间
        self.update_time = 0  # 订单更新时间
        self.ddp_created = ""  # 数据推送创建时间
        self.ddp_modified = ""  # 数据推送更新时间
        self.ddp_response = {}  # API返回的整个JSON字符串
        self.version = 0  # 版本号
        self.digest = ""  # 业务摘要
        self.version_update_time = 0  # 版本更新时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'order_id', 'order_status', 'order_type', 'shop_id',
            'doudian_open_id', 'create_time', 'update_time', 'ddp_created',
            'ddp_modified', 'ddp_response', 'version', 'digest', 'version_update_time'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "tt_rds_trade_tb"
