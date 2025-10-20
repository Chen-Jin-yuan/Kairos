import csv
import time
import math
from datetime import datetime

from framework.message import BaseMessageHandler
from framework.message import Message


class RequestGenerator:
    def __init__(self, csv_file_path: str, sample_interval: int, scale_factor: int, service_name: str, entry_agent_name: str, message_handler: BaseMessageHandler, colo_servcie_entry_agent_names=None):
        self.csv_file_path = csv_file_path
        self.sample_interval = sample_interval
        self.scale_factor = scale_factor
        self.service_name = service_name
        self.entry_agent_name = entry_agent_name
        self.message_handler = message_handler
        self.raw_data = None
        self.sampled_data = None
        self.intervals = None
        self.colo_servcie_entry_agent_names = colo_servcie_entry_agent_names

        self.read_csv_to_list()
        self.sample_data()
        self.calculate_intervals()

    # 读取数据
    def read_csv_to_list(self):
        data = []
        with open(self.csv_file_path, mode='r', newline='') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data.append(row)
        self.raw_data = data

    # 采样数据
    def sample_data(self):
        self.sampled_data = self.raw_data[::self.sample_interval]
        self.sampled_data = [data for data in self.sampled_data for _ in range(self.scale_factor)]

    def get_data_len(self):
        return len(self.sampled_data)

    # 计算请求时间间隔
    def calculate_intervals(self):
        timestamps = [row['TIMESTAMP'] for row in self.sampled_data]

        intervals = []
        for i in range(len(timestamps) - 1):
            current_time = datetime.strptime(timestamps[i], '%Y-%m-%d %H:%M:%S.%f0')
            next_time = datetime.strptime(timestamps[i + 1], '%Y-%m-%d %H:%M:%S.%f0')
            interval = (next_time - current_time).total_seconds()
            intervals.append(interval)

        self.intervals = intervals

    def send_request(self, msg_id, data):
        # 构建消息
        msg = Message(id=msg_id, service_name=self.service_name, msg_type="request")
        msg.set_origin_data(data=data)
        msg.set_start_time()
        # 把消息发送至入口 Agent
        self.message_handler.send(message=msg, target_name=self.entry_agent_name)
        print(f"send msg id={msg_id} service={self.service_name} to {self.entry_agent_name}")

    def start_generate(self, data_list):
        # 添加映射
        self.message_handler.add_target_mapping(target_name=self.entry_agent_name)

        for i in range(len(data_list)):
            t_start = time.perf_counter()
            data = data_list[i]
            self.send_request(msg_id=i, data=data)
            t_end = time.perf_counter()

            t_send = t_end - t_start

            if i < len(self.intervals):
                if self.intervals[i] > t_send:
                    time.sleep(self.intervals[i] - t_send)

    def start_generate_test(self):
        data_len = self.get_data_len()
        print("data: ", data_len)
        t_generate_start = time.time()
        for i in range(data_len):
            t_start = time.perf_counter()
            print(f"test send {i}")
            t_end = time.perf_counter()

            t_send = t_end - t_start

            if i < len(self.intervals):
                if self.intervals[i] > t_send:
                    time.sleep(self.intervals[i] - t_send)
        t_generate_end = time.time()
        print("total use: ", t_generate_end-t_generate_start)


    def send_request_colocation(self, msg_id, data, service_name, entry_agent_name):
        # 构建消息
        msg = Message(id=msg_id, service_name=service_name, msg_type="request")
        msg.set_origin_data(data=data)
        msg.set_start_time()
        # 把消息发送至入口 Agent
        self.message_handler.send(message=msg, target_name=entry_agent_name)
        print(f"send msg id={msg_id} service={service_name} to {entry_agent_name}")


