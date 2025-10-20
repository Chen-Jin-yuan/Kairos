from abc import ABC, abstractmethod
from .message import Message

class BaseMessageHandler(ABC):
    def __init__(self):
        # 存储 target_name 到实际 target_channel 的映射
        # 用于指定发送目标
        self.target_map = {}

    @abstractmethod
    def initialize(self, **kwargs):
        """
        初始化通信管道，设置所需的资源或连接。
        初始化消费者（监听端口）
        
        :param kwargs: 额外的关键字参数，可用于初始化时的配置。
        """
        pass


    def add_target_mapping(self, target_name: str):
        """
        添加 target_name 与 target_channel 的映射。
        
        :param target_name: 目标名称，用于上层调用
        """
        target_channel = self._generate_channel_from_target(target_name)
        self.target_map[target_name] = target_channel

    def add_target_mappings(self, target_list: list):
        """
        接收一个 target 列表，构建 target_map 映射。
        
        :param target_list: 要建立映射的 target 列表，格式为 [target_name, ...]
        """
        for target_name in target_list:
            self.add_target_mapping(target_name)

    @abstractmethod
    def _generate_channel_from_target(self, target_name: str):
        """
        根据 target_name 生成对应的 target_channel，具体实现由子类提供。
        
        :param target_name: 目标名称
        :return: 对应的 target_channel
        """
        pass

    @abstractmethod
    def send(self, message: Message, target_name: str):
        """
        发送消息的方法，查找 target_name 的 channel 并发送消息。
        
        :param message: 要发送的消息
        :param target_name: 目标名称，自动映射到 channel
        """
        pass

    @abstractmethod
    def recv(self):
        """
        接收消息的方法，使用消费者接收消息。
        
        :return: 接收到的消息
        """
        pass

    @abstractmethod
    def close(self):
        """
        定义管道如何优雅关闭
        """
        pass