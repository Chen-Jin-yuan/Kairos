import threading
import requests
import time
import json
import os
import datetime
from queue import Queue
from framework.message import BaseMessageHandler
from framework.message import Message
from framework.workflow import Workflow
from framework.trace import RequestGenerator
from .base_dataset import BaseDataset

class Frontend:
    def __init__(self, message_handler: BaseMessageHandler, workflow: Workflow, dataset: BaseDataset, colo_datasets=None):
        self.lab_mark = ""
        self.message_handler = message_handler
        self.workflow = workflow
        self.dataset = dataset
        self.colo_datasets = colo_datasets
        self.recv_thread = None
        self.process_thread = None
        self.stop_event = threading.Event()
        self.message_queue = Queue()
        print("caching data...")
        if self.colo_datasets is None:
            self.dataset.cache_data()
        else:
            datasets_len = len(self.colo_datasets)
            print(f"colocation datasets len: {datasets_len}")
            for i in range(datasets_len):
                self.colo_datasets[i].cache_data()


    def recv_messages(self):
        """Listen for incoming messages and process them."""
        print("start listening...")
        while not self.stop_event.is_set():
            msg_list = self.message_handler.recv()
            for msg in msg_list:
                msg.set_end_time()

                print("\nrecv msg:", msg.get_id(), msg.get_service_name(), msg.get_msg_type())
                for a in msg.get_action_timing():
                    print(a)
                print(msg.get_origin_data())
                print("duration:", msg.get_duration_seconds(), "\n")

                self.message_queue.put(msg)

    def process_messages(self):
        """Process messages from the queue and append action_timing to a JSON file."""
        print("start processing...")
        records = []
        if os.path.exists(f"data/msg_data_{self.lab_mark}.json"):
            with open(f"data/msg_data_{self.lab_mark}.json", "r") as json_file:
                records = json.load(json_file)

        t1 = time.time()
        while not self.stop_event.is_set():
            if not self.message_queue.empty():
                msg = self.message_queue.get()

                action_timing = msg.get_action_timing()

                for action in action_timing:
                    if isinstance(action.get("timestamp"), datetime.datetime):
                        action["timestamp"] = action["timestamp"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                duration = msg.get_duration_seconds()
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                json_data = {
                    "msg_id": msg.get_id(),
                    "service": msg.get_service_name(),
                    "action_timing": action_timing,
                    "duration": duration,
                    "timestamp": timestamp,
                }

                records.append(json_data)
                print(f"Processed and saved msg_id={msg.get_id()} service={msg.get_service_name()} at {timestamp}\n")

            t2 = time.time()
            if t2 - t1 > 5:
                with open(f"data/msg_data_{self.lab_mark}.json", "w") as json_file:
                    json.dump(records, json_file, indent=4)
                print("[write msg]")
                t1 = time.time()

    def start_receiving(self):
        """Start the message receiving thread using self.message_handler."""
        if self.recv_thread is None or not self.recv_thread.is_alive():
            self.recv_thread = threading.Thread(target=self.recv_messages)
            self.recv_thread.start()

    def start_processing(self):
        """Start the message processing thread."""
        if self.process_thread is None or not self.process_thread.is_alive():
            self.process_thread = threading.Thread(target=self.process_messages)
            self.process_thread.start()

    def stop_receiving(self):
        """Stop the message receiving thread."""
        if self.recv_thread is not None and self.recv_thread.is_alive():
            self.stop_event.set()  # 停止接收消息
            self.recv_thread.join()
            print("Receiving thread stopped.")

        if self.process_thread is not None:
            self.process_thread.join()
            print("Processing thread stopped.")


    def send_request(self, service_name: str, msg_id: int):
        service_info = self.workflow.services[service_name]
        data = self.dataset.get_data_by_service_name(service_name=service_name, batch_size=1)
        target_name = service_info['entry_agent_name']
        request_keys = service_info['request_keys']


        assert set(data.keys()) == set(request_keys)
        self.message_handler.add_target_mapping(target_name=target_name)

        msg = Message(id=msg_id, service_name=service_name, msg_type="request")
        msg.set_origin_data(data=data)
        msg.set_start_time()
        self.message_handler.send(message=msg, target_name=target_name)
        print(f"send msg id={msg_id} service={service_name} to {target_name}")


    def start(self, rate, request_num):
        self.start_receiving()
        self.start_processing()

        for i in range(request_num):
            for service_name in self.workflow.services.keys():
                self.send_request(service_name=service_name, msg_id=i)
                time.sleep(rate)

        input("input anything to exit...")
        self.stop_receiving()


    def start_generate(self, trace_csv_file_path, sample_interval, scale_factor):
        self.start_receiving()
        self.start_processing()

        service_names = list(self.workflow.services.keys())

        assert len(service_names) == 1, f"Expected exactly one service in the workflow, but found {len(service_names)} services."
        service_name = service_names[0]

        service_info = self.workflow.services[service_name]
        entry_agent_name = service_info['entry_agent_name']

        print("+++++++++++++++++ init RequestGenerator +++++++++++++++++")
        print(f"service_name: {service_name}\nentry_agent_name: {entry_agent_name}\ntrace_csv_file_path: {trace_csv_file_path}\nsample_interval: {sample_interval}")

        self.request_generator = RequestGenerator(csv_file_path=trace_csv_file_path, sample_interval=sample_interval, scale_factor=scale_factor,
                                    service_name=service_name, entry_agent_name=entry_agent_name, message_handler=self.message_handler)

        data_len = self.request_generator.get_data_len()
        print(f"trace sampled len: {data_len}")

        request_keys = service_info['request_keys']
        data_perpared = []
        for i in range(data_len):
            data = self.dataset.get_data_by_service_name(service_name=service_name)
            assert set(data.keys()) == set(request_keys)
            data_perpared.append(data)
        
        assert data_len == len(data_perpared)

        self.request_generator.start_generate(data_list=data_perpared)
        
        input("input anything to exit...")
        self.stop_receiving()


