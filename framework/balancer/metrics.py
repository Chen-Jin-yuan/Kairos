import requests
import time
import threading

from framework.logger import FileLogger
from .balancer_setting import METRICS_INTERVAL

class Metrics:
    def __init__(self, llm_url, interval):
        node, port = self._parse_node_and_port(llm_url)
        self.llm_metrics_url = f"http://{node}:{port}/metrics"
        self.interval = interval

        # GPU KV-cache usage. 1 means 100 percent usage.
        self.gpu_cache_usage = 0
        # Number of requests currently running on GPU.
        self.num_running = 0
        # Number of requests waiting to be processed.
        self.num_waiting = 0
        # Number of requests swapped to CPU.
        self.num_swapped = 0
        self.time_in_queue_requests_sum = 0

        self.num_waiting_history = []
        self.gpu_cache_usage_threshold = 1

        self.logger = FileLogger(f"logs/metrics_{node}_{port}.log")
        self.logger.clear_log_file()
        self.logger.log(f"Metrics is looking at '{self.llm_metrics_url}' with interval {self.interval} s")

        self.monitoring_thread = threading.Thread(target=self.start_watch)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def _parse_node_and_port(self, url):
        node = None
        port = None

        scheme_end = url.find('://')

        rest = url[scheme_end + 3:]
        path_start = rest.find('/')
        netloc = rest[:path_start]

        if ':' in netloc:
            node, port_str = netloc.split(':')
            port = int(port_str)

        return node, port

    def extract_metrics(self, text):
        lines = text.split('\n')
        for line in lines:
            if line.startswith('vllm:gpu_cache_usage_perc'):
                parts = line.split()
                if len(parts) == 2:
                    self.gpu_cache_usage = float(parts[1])
            elif line.startswith('vllm:num_requests_running'):
                parts = line.split()
                if len(parts) == 2:
                    self.num_running = float(parts[1])
            elif line.startswith('vllm:num_requests_waiting'):
                parts = line.split()
                if len(parts) == 2:
                    self.num_waiting = float(parts[1])
            elif line.startswith('vllm:num_requests_swapped'):
                parts = line.split()
                if len(parts) == 2:
                    self.num_swapped = float(parts[1])
            elif line.startswith('vllm:time_in_queue_requests_sum'):
                parts = line.split()
                if len(parts) == 2:
                    self.time_in_queue_requests_sum = float(parts[1])

    def fetch_metrics(self):
        try:
            response = requests.get(self.llm_metrics_url)
            response.raise_for_status()
            metrics_output = response.text
            self.extract_metrics(metrics_output)
        except requests.RequestException as e:
            pass
        except Exception as e:
            self.logger.log(f"An unknown error occurred: {e}", "ERROR")

    def get_metrics(self):
        return {
            "gpu_cache_usage": self.gpu_cache_usage,
            "num_running": self.num_running,
            "num_waiting": self.num_waiting,
            "num_swapped": self.num_swapped,
            "time_in_queue_requests_sum": self.time_in_queue_requests_sum
        }

    def update_threshold(self):
        non_zero_count = sum(1 for num in self.num_waiting_history if num != 0)
        self.gpu_cache_usage_threshold = 1 - non_zero_count * 0.005
    
    def start_watch(self):
        try:
            while True:
                t_start = time.perf_counter()
                self.fetch_metrics()

                self.num_waiting_history.append(self.num_waiting)
                if len(self.num_waiting_history) > 10:
                    self.num_waiting_history.pop(0)

                self.update_threshold()

                t_end = time.perf_counter()
                t_send = t_end - t_start

                log_msg = f"Metrics: 'GPU cache usage' {self.gpu_cache_usage * 100:.3f}%, 'Running requests' {self.num_running}, 'Waiting requests' {self.num_waiting}, 'Swapped requests' {self.num_swapped}, 'Time in queue requests sum' {self.time_in_queue_requests_sum:.3f}. Took {t_send:.3f} s, Threshold: {self.gpu_cache_usage_threshold:.3f}"
                self.logger.log(log_msg)

                if self.interval > t_send:
                    time.sleep(self.interval - t_send)
        except KeyboardInterrupt:
            self.logger.log("Stopped by (Ctrl+C).")


class MetricsManager:
    def __init__(self, llm_urls):
        self.metrics_instances = {}
        for llm_url in llm_urls:
            metrics = Metrics(llm_url, METRICS_INTERVAL)
            self.metrics_instances[llm_url] = metrics

    def get_llm_metrics(self, llm_url):
        metrics = self.metrics_instances[llm_url]
        return metrics.get_metrics()

    def get_llm_metrics_sync(self, llm_url):
        # return llm metrics, sync get_llm_metrics
        pass
    
    def get_all_metrics(self):
        all_metrics = {}
        for llm_url, metrics in self.metrics_instances.items():
            all_metrics[llm_url] = metrics.get_metrics()
        return all_metrics


