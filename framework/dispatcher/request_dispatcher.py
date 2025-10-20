import threading
import time

from framework.logger import FileLogger
from framework.message import BaseMessageHandler, Message
from .base_decision_model import BaseDecisionModel
from .agent_replica_queue import AgentReplicaQueue
from .status import AgentReplicaStatus


class RequestDispatcher:
    def __init__(self, dispatcher_name: str, decision_model: BaseDecisionModel, message_handler: BaseMessageHandler):
        self.dispatcher_name = dispatcher_name
        self.decision_model = decision_model
        self.message_handler = message_handler
        self.logger = FileLogger(f"logs/{self.dispatcher_name}.log")
        
        self.buffer_queue = []
        self.agent_replicas = {}
        self.lock = threading.Lock()
        self.buffer_thread = threading.Thread(target=self.process_buffer)
        self.buffer_thread.start()


    def register_agent_replica(self, replica_name):
        self.message_handler.add_target_mapping(replica_name)
        agent_replica_queue = AgentReplicaQueue(replica_name=replica_name, message_handler=self.message_handler, logger=self.logger)
        self.agent_replicas[replica_name] = {"queue": agent_replica_queue}
        self.logger.log(f"register {replica_name} queue")


    def unregister_agent_replica(self, replica_name):
        agent_replica_queue = self.agent_replicas.pop(replica_name, None)
        if agent_replica_queue:
            agent_replica_queue["queue"].stop()
        self.logger.log(f"unregister {replica_name} queue")


    def update_agent_replica_status(self, replica_name, status):
        if replica_name in self.agent_replicas:
            self.agent_replicas[replica_name]["queue"].set_status(status)


    def process_buffer(self):
        while True:
            with self.lock:
                self.decision_model.decide(self.agent_replicas, self.buffer_queue, self.logger)
            
            time.sleep(0.1)
                


    def receive_request(self, message: Message):
        with self.lock:
            self.buffer_queue.append(message)

    def start(self):
        print(f"{self.dispatcher_name} start...")
        self.logger.log(f"Dispatcher '{self.dispatcher_name}' start")
        while True:
            time.sleep(0.1)

            msg_list = self.message_handler.recv()
            for msg in msg_list:
                self.logger.log(f"{self.dispatcher_name} received message "
                    f"id={msg.get_id()}, "
                    f"service_name={msg.get_service_name()}, "
                    f"msg_type={msg.get_msg_type()}")

                if msg.get_msg_type() == "event":
                    origin_data = msg.get_origin_data()

                    for replica_name, operation in origin_data.items():
                        if operation == "ready":
                            if replica_name not in self.agent_replicas:
                                self.register_agent_replica(replica_name)
                            else:
                                self.update_agent_replica_status(replica_name, AgentReplicaStatus.READY)
                                
                        elif operation == "down":
                            if replica_name in self.agent_replicas:
                                self.unregister_agent_replica(replica_name)

                elif msg.get_msg_type() == "request":
                    self.receive_request(message=msg)