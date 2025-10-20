import os
import csv
from datetime import datetime

class CSVLogger:
    def __init__(self, headers, log_file_path):
        """
        初始化CSVLogger。
        
        :param headers: CSV文件的表头列表
        :param log_file_path: CSV文件的路径
        """
        self.headers = ['Timestamp'] + headers  # 添加时间戳列
        self.log_file_path = log_file_path
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # 如果文件不存在，则写入表头
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)

    def log(self, data):
        """
        将一行数据写入CSV文件。
        
        :param data: 数据列表，长度应与表头一致
        """

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row = [timestamp] + data
        
        # 追加写入数据
        with open(self.log_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)