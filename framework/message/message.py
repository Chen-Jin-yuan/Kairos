from datetime import datetime
import time

class Message:
    def __init__(self, id: int, service_name: str, msg_type: str):
        """
        初始化Message类。
        """
        self.id = id
        self.service_name = service_name
        self.origin_data = None
        self.action_timing = []
        self.start_time = None
        self.end_time = None
        self.msg_type = msg_type
        self.start_timestamp = None

    def get_id(self):
        """
        获取消息的ID。
        """
        return self.id

    def get_service_name(self):
        """
        获取消息的服务名称。
        """
        return self.service_name

    def get_msg_type(self):
        """
        获取消息类型。
        """
        return self.msg_type

    def add_action_timing(self, action_name: str):
        """
        按顺序记录消息在某动作的时间戳。
        """
        self.action_timing.append({
            "action_name": action_name,
            "timestamp": datetime.now()
        })

    def get_action_timing(self):
        """
        获取动作时间数据。
        """
        return self.action_timing

    def set_origin_data(self, data: dict):
        """
        设置用于智能体运行的原始数据，必须为字典类型。
        """
        if not isinstance(data, dict):
            raise ValueError("Origin data must be a dictionary.")
        self.origin_data = data

    def get_origin_data(self):
        """
        获取用于智能体运行的原始数据。
        """
        return self.origin_data

    def set_start_time(self):
        """
        设置开始时间为当前时间。
        """
        self.start_time = datetime.now()
        self.start_timestamp = time.time()

    def set_end_time(self):
        """
        设置结束时间为当前时间。
        """
        self.end_time = datetime.now()

    def get_duration_seconds(self):
        """
        获取开始时间和结束时间之间的秒数。
        """
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            return duration
        return None

    def get_start_timestamp(self):
        """
        获取起始时间戳
        """
        return self.start_timestamp