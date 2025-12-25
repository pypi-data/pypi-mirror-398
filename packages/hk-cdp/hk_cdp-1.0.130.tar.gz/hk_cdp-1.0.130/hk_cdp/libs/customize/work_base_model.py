from datetime import timedelta
from seven_cloudapp_frame.libs.common import *
from seven_cloudapp_frame.libs.customize.seven_helper import *
from hk_cdp.models.db_models.queue.queue_work_log_model import *

class WorkBaseModel():
    """
    :description: 队列作业日志业务模型
    """

    def __init__(self, context=None, logging_error=None, logging_info=None, db_config_dict=None, sub_table=None):
        self.context = context
        self.logging_link_error = logging_error
        self.logging_link_info = logging_info
        self.db_config_dict = db_config_dict
        self.sub_table = sub_table

    def add_queue_work_log(self, log_id, queue_name, queue_value, is_success=1, result_info='执行成功'):
        """
        :description: 添加队列日志
        :param log_id：日志标识
        :param queue_name：队列名称
        :param queue_value：队列值
        :param is_success：是否成功 1-是 0-否
        :param result_info：结果信息
        :return: 
        :last_editors: HuangJianYi
        """
        try:
            queue_work_log_model = QueueWorkLogModel(db_config_dict=self.db_config_dict, sub_table=self.sub_table, context=self.context)
            queue_work_log = QueueWorkLog()
            queue_work_log.log_id = log_id
            queue_work_log.queue_name = queue_name
            queue_work_log.queue_value = queue_value
            queue_work_log.is_success = is_success
            queue_work_log.result_info = result_info
            queue_work_log.create_date = TimeHelper.get_now_format_time()
            queue_work_log_model.add_entity(queue_work_log)
        except Exception as ex:
            if self.context:
                self.context.logging_link_error("【添加队列日志】" + traceback.format_exc())
            elif self.logging_link_error:
                self.logging_link_error("【添加队列日志】" + traceback.format_exc())
