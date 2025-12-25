#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class TtRdsItemModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TtRdsItemModel, self).__init__(TtRdsItem, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class TtRdsItem:
    def __init__(self):
        super(TtRdsItem, self).__init__()
        self.id = 0  # 主键id
        self.product_id = ""  # 商品id
        self.product_status = 0  # 在线状态
        self.check_status = 0  # 审核状态
        self.draft_status = 0  # 草稿状态
        self.product_type = 0  # 商品类型
        self.shop_id = 0  # 店铺id
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
            'id', 'product_id', 'product_status', 'check_status', 'draft_status',
            'product_type', 'shop_id', 'create_time', 'update_time', 'ddp_created',
            'ddp_modified', 'ddp_response', 'version', 'digest', 'version_update_time'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "tt_rds_item_tb"
