import pynvml
import time
from threading import Thread, Event
import matplotlib.pyplot as plt
import os

from framework.logger import CSVLogger

class Watcher:
    def __init__(self, interval=5, log_file_path='logs/gpu_usage_log.csv', output_dir='logs'):
        """
        初始化 Watcher 实例。
        """
        pynvml.nvmlInit()
        self.device_count = pynvml.nvmlDeviceGetCount()
        self.interval = interval
        self.stop_event = Event()
        self.thread = Thread(target=self._monitor_gpu)

        headers = []
        for i in range(self.device_count):
            headers.extend([
                f"GPU {i} Total Memory (MiB)",
                f"GPU {i} Used Memory (MiB)",
                f"GPU {i} Free Memory (MiB)",
                f"GPU {i} Utilization (%)"
            ])

        self.logger = CSVLogger(headers=headers, log_file_path=log_file_path)

        self.total_memory = []
        for i in range(self.device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            self.total_memory.append(info.total / 1024**2)

        self.used_memory_data = [[] for _ in range(self.device_count)]
        self.utilization_data = [[] for _ in range(self.device_count)]
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _monitor_gpu(self):
        while not self.stop_event.is_set():
            t1 = time.time()
            self._log_gpu_usage()
            t2 = time.time()
            if t2 - t1 < self.interval:
                time.sleep(self.interval - (t2 - t1))
    
    def _log_gpu_usage(self):
        row_data = []
        for i in range(self.device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)


            row_data.extend([
                info.total / 1024**2,
                info.used / 1024**2,
                info.free / 1024**2,
                utilization.gpu
            ])

            self.used_memory_data[i].append(info.used / 1024**2)
            self.utilization_data[i].append(utilization.gpu)

        self.logger.log(row_data)
        self._save_plots()

    def _save_plots(self):
        plt.figure(figsize=(10, 5))
        for i in range(self.device_count):
            plt.plot(self.used_memory_data[i], label=f'GPU {i} Used Memory (MiB)')
            plt.axhline(y=self.total_memory[i], color='r', linestyle='--', label=f'GPU {i} Total Memory')
        
        plt.title(f'GPU Memory Usage Over Time (interval={self.interval})')
        plt.xlabel('Step')
        plt.ylabel('Memory Used (MiB)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'gpu_memory.png'))
        plt.close()

        plt.figure(figsize=(10, 5))
        for i in range(self.device_count):
            plt.plot(self.utilization_data[i], label=f'GPU {i} Utilization (%)')
        plt.axhline(y=100, color='r', linestyle='--', label='100% Utilization')
        
        plt.title(f'GPU Utilization Over Time (interval={self.interval})')
        plt.xlabel('Step')
        plt.ylabel('Utilization (%)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'gpu_utilization.png'))
        plt.close()

    def start(self):
        """启动 GPU 监控线程。"""
        print("start GPU watcher...")
        self.thread.start()
    
    def stop(self):
        """停止 GPU 监控线程并等待其结束。"""
        print("stop GPU watcher...")
        self.stop_event.set()
        self.thread.join()
        pynvml.nvmlShutdown()
        print("watcher stop!")
