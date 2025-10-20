import threading
import time
import json

from framework.agent import BaseAgentV2
from framework.logger import FileLogger
from framework.message import BaseMessageHandler, Message


class RequestDispatcherV2:
    def __init__(self, dispatcher_name: str, message_handler: BaseMessageHandler, balancer_url: str, agent_class: BaseAgentV2):
        self.dispatcher_name = dispatcher_name
        self.message_handler = message_handler
        self.logger = FileLogger(f"logs/DispatcherV2_{self.dispatcher_name}.log")

        self.logger.log(f"init balancer url: {balancer_url}")
        self.balancer_url = balancer_url
        self.logger.log(f"init agent class")
        self.agent = agent_class(agent_name=dispatcher_name)
        self.current_url_index = 0
        self.lock = threading.Lock()


    def send(self, message: Message, target_name: str):
        self.logger.log(f"{self.dispatcher_name}V2 sending message to {target_name}. "
                        f"id={message.get_id()}, "
                        f"service_name={message.get_service_name()}, "
                        f"msg_type={message.get_msg_type()}")

        self.message_handler.add_target_mapping(target_name=target_name)
        self.message_handler.send(message=message, target_name=target_name)

    # Deprecated
    def decide(self):
        with self.lock:
            current_url = self.llm_urls[self.current_url_index]
            self.logger.log(f"'[decide]' switched to llm url: {current_url}")
            self.current_url_index = (self.current_url_index + 1) % len(self.llm_urls)
            return current_url

    def handle_message(self, msg):
        llm_url = self.balancer_url
        msg.add_action_timing("start_run")

        # start_time = msg.get_start_timestamp()
        start_time = time.time()
        metadata = {"agent_name": self.dispatcher_name, "start_time": start_time, "msg_id": msg.get_id()}

        result, target_name = self.agent.run(input_data=msg.get_origin_data(), llm_url=llm_url, metadata=metadata)
        msg.add_action_timing("end_run")

        msg.set_origin_data(data=result)

        self.send(message=msg, target_name=target_name)

    def start(self):
        print(f"{self.dispatcher_name} start...")
        self.logger.log(f"DispatcherV2 '{self.dispatcher_name}' start")
        while True:
            time.sleep(0.1)

            msg_list = self.message_handler.recv()
            for msg in msg_list:
                self.logger.log(f"{self.dispatcher_name}V2 received message "
                    f"id={msg.get_id()}, "
                    f"service_name={msg.get_service_name()}, "
                    f"msg_type={msg.get_msg_type()}")

                if msg.get_msg_type() == "request":
                    thread = threading.Thread(target=self.handle_message, args=(msg,))
                    thread.start()

                else:
                    self.logger.log(f"some message is not request: "
                    f"id={msg.get_id()}, "
                    f"service_name={msg.get_service_name()}, "
                    f"msg_type={msg.get_msg_type()}", level="ERROR")