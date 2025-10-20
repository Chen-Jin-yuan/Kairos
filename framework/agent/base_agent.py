import time
import torch
from abc import ABC, abstractmethod

from framework.message import BaseMessageHandler
from framework.message import Message
from framework.logger import FileLogger

class BaseAgent(ABC):
    def __init__(self, agent_name: str, agent_number: int = 0, message_handler: BaseMessageHandler = None):
        """
        初始化Agent。
        """
        self.agent_name = agent_name
        self.agent_number = agent_number
        self.agent_full_name = f"{self.agent_name}_{self.agent_number}"
        self.message_handler = message_handler
        self.current_device = None
        self.model_list = []
        self.logger = FileLogger(f"logs/{self.agent_full_name}.log")
        print(f"Agent '{self.agent_full_name}' log file: logs/{self.agent_full_name}.log")
        self.logger.log(f"Agent '{self.agent_full_name}' initialized")

        self.flag_msg = Message(id=9999, service_name=f"flag", msg_type="event")
        self.flag_msg.set_origin_data(data={f"{self.agent_full_name}": "ready"})
        self.flush_msg = Message(id=8888, service_name=f"flag", msg_type="flush")

    @abstractmethod
    def _run_impl(self, input_data):
        """
        用户实现的运行逻辑。
        """
        pass

    @abstractmethod
    def _load_impl(self, device):
        """
        用户实现的加载逻辑。
        """
        pass

    def run(self, input_data):
        self.logger.log(f"{self.agent_full_name} starting '_run_impl'")
        try:
            res, target_name = self._run_impl(input_data)
            self.logger.log(f"{self.agent_full_name} run completed successfully, msg send to '{target_name}'")
            return res, target_name
        except Exception as e:
            self.logger.log(f"Error during [run]: {e}", level="ERROR")
            print(f"Error occurred during [run]. Please check the log file: logs/{self.agent_full_name}.log")
            exit(1)

    def load(self, device):
        self.logger.log(f"{self.agent_full_name} starting '_load_impl'")
        try:
            self._load_impl(device)
            self.logger.log(f"{self.agent_full_name} loaded successfully to {device}.")
            self.current_device = device
        except Exception as e:
            self.logger.log(f"Error during [load]: {e}", level="ERROR")
            print(f"Error occurred during [load]. Please check the log file: logs/{self.agent_full_name}.log")
            exit(1)

    def send(self, message: Message, target_name: str):
        """通过消息处理器发送消息。"""
        self.logger.log(f"{self.agent_full_name} sending message to {target_name}. "
                        f"id={message.get_id()}, "
                        f"service_name={message.get_service_name()}, "
                        f"msg_type={message.get_msg_type()}")

        self.message_handler.add_target_mapping(target_name=target_name)

        self.logger.log("start send")
        self.message_handler.send(message=message, target_name=target_name)
        self.logger.log("end send")

    def recv(self):
        """
        接收消息。
        """
        msg_list = self.message_handler.recv()
        return msg_list

    def move_to(self, device):
        """
        将智能体移动到目标位置。
        """
        self.logger.log(f"{self.agent_full_name} moving to {device}")
        for model in self.model_list:
            model.to(device)
        torch.cuda.empty_cache()
        self.current_device = device
        self.logger.log(f"{self.agent_full_name} move to {device} done")

    def set_ready(self):
        """
        设置智能体状态标志。
        """
        time.sleep(0.1)
        self.send(message=self.flag_msg, target_name=self.agent_name)
        self.logger.log(f"{self.agent_full_name} status set to ready")
        # 刷新kafka
        time.sleep(0.1)
        self.send(message=self.flush_msg, target_name=self.agent_name)
        time.sleep(0.1)
        self.send(message=self.flush_msg, target_name=self.agent_name)
        
    def set_message_handler(self, new_handler: BaseMessageHandler):
        """动态更换 message_handler"""
        self.message_handler = new_handler
        self.logger.log(f"{self.agent_full_name} message handler changing")
        
    def start(self):
        print(f"{self.agent_full_name} start...")
        self.logger.log(f"Agent '{self.agent_full_name}' start")
        self.set_ready()
        
        while True:
            msg_list = self.recv()
            for msg in msg_list:
                # 在日志中记录每条接收到的消息的详细信息
                self.logger.log(f"{self.agent_full_name} received message "
                    f"id={msg.get_id()}, "
                    f"service_name={msg.get_service_name()}, "
                    f"msg_type={msg.get_msg_type()}")

                # 处理框架事务
                if msg.get_msg_type() == "event":
                    print("doing event...")

                # 处理用户请求
                elif msg.get_msg_type() == "request":
                    msg.add_action_timing("start_run")
                    result, target_name = self.run(input_data=msg.get_origin_data())
                    msg.add_action_timing("end_run")
                    msg.set_origin_data(data=result)

                    self.send(message=msg, target_name=target_name)

                    self.set_ready()