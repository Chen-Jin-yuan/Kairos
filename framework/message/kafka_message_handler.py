from kafka import KafkaProducer, KafkaConsumer
import pickle

from .base_message_handler import BaseMessageHandler
from .message import Message

class KafkaMessageHandler(BaseMessageHandler):
    def __init__(self):
        super().__init__()

    def initialize(self, bootstrap_servers: str, consumer_target_name: str, group_id: str = "default_group"):
        """
        初始化通信管道，设置所需的资源或连接。
        初始化消费者（监听端口）
        """
        # 创建Kafka消费者
        consumer_topic = self._generate_channel_from_target(consumer_target_name)
        self.consumer = KafkaConsumer(
            consumer_topic,
            bootstrap_servers=bootstrap_servers,
            fetch_max_bytes=50 * 1024 * 1024,
            group_id=group_id,
            key_deserializer=lambda k: k.decode('utf-8'),
            value_deserializer=lambda v: pickle.loads(v)
        )

        # 创建Kafka生产者
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            max_request_size=50 * 1024 * 1024,
            key_serializer=lambda k: k.encode('utf-8'),
            value_serializer=lambda v: pickle.dumps(v)
        )

    def _generate_channel_from_target(self, target_name: str):
        """
        根据 target_name 生成对应的 target_channel，具体实现由子类提供。
        
        :param target_name: 目标名称
        :return: 对应的 target_channel
        """
        return f"{target_name}_topic"

    def send(self, message: Message, target_name: str):
        """
        发送消息的方法，查找 target_name 的 channel 并发送消息。
        
        :param message: 要发送的消息
        :param target_name: 目标名称，自动映射到 channel
        """
        target_topic = self.target_map.get(target_name)
        if not target_topic:
            raise ValueError(f"Target name '{target_name}' not found in target map.")

        message.add_action_timing(f"send to {target_name}")

        message.add_action_timing(f"start_send to {target_name}")
        self.producer.flush() 
        message.add_action_timing(f"end_send to {target_name}")
        self.producer.send(target_topic, key="", value=message)

    def recv(self):
        """
        接收消息的方法，使用消费者接收消息。
        
        :return: 接收到的消息
        """
        res = []

        messages = self.consumer.poll(timeout_ms=10)

        for topic_partition, records in messages.items():
            for message in records:
                key = message.key
                value = message.value

                value.add_action_timing(f"recv")
                res.append(value)

        self.consumer.commit()

        return res

    def close(self):
        """
        定义管道如何优雅关闭
        """
        self.producer.close() # 关闭生产者
        self.consumer.close() # 关闭消费者