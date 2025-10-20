import time
import threading

from framework.logger import FileLogger
from .balancer_setting import PREDICT_INTERVAL, MAX_TOKENS, Decode_slop, Bias_factor


class Request:
    def __init__(self, msg_id, prompt_length, predicted_time):
        self.msg_id = msg_id
        self.prompt_length = prompt_length
        self.predicted_time = predicted_time
        self.interval_starts = []


class MemoryPerceptor:
    def __init__(self, llm_url, metrics, interval_length=0.1):
        node, port = self._parse_node_and_port(llm_url)

        self.interval_length = interval_length
        self.intervals = {}
        self.msg_map = {}
        self.lock = threading.Lock()

        self.log_interval = interval_length
        self.logger = FileLogger(f"logs/mem_pred_{node}_{port}.log")
        self.logger.clear_log_file()
        self.logger.log(f"MemoryPerceptor is logging with interval {self.log_interval} s")


        self.metrics = metrics

        self.bias_tokens = 0

        self.pred_max_tokens = 0

        self.monitoring_thread = threading.Thread(target=self.start_log)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def try_add_request(self, msg_id, prompt_length, predicted_time):
        self.pred_max_tokens = 0
        new_request = Request(msg_id, prompt_length, predicted_time)

        with self.lock:
            new_intervals = {k: v.copy() for k, v in self.intervals.items()}

            current_time = time.time()
            start_time = current_time - (current_time % self.interval_length)
            end_time = start_time + new_request.predicted_time

            overflow = False

            interval_start = start_time
            while interval_start < end_time:
                interval_start = round(interval_start, 1)

                if interval_start not in new_intervals:
                    new_intervals[interval_start] = []

                new_intervals[interval_start].append(new_request)
                new_request.interval_starts.append(interval_start)

                k = len(new_intervals[interval_start])
                S_k = self.get_slope(k)
                total_memory = sum(req.get_cumulative_memory_usage(interval_start, S_k*self.interval_length) for req in new_intervals[interval_start])
                total_memory += self.bias_tokens
                self.pred_max_tokens = max(self.pred_max_tokens, total_memory)

                # print(interval_start, total_memory)
                if total_memory > MAX_TOKENS:
                    overflow = True
                    break

                interval_start += self.interval_length
            
            if overflow:
                return False
            else:
                self.intervals = new_intervals
                self.msg_map[msg_id] = new_request
                return True
    
    def remove_request(self, msg_id):
        with self.lock:
            if msg_id not in self.msg_map:
                return

            request = self.msg_map.pop(msg_id)

            for interval_start in request.interval_starts:
                if interval_start in self.intervals:
                    self.intervals[interval_start].remove(request)
                    if not self.intervals[interval_start]:
                        del self.intervals[interval_start]

            request.interval_starts.clear()

    def get_slope(self, k):
        # by k
        return Decode_slop

    def cal_bias(self, predict_tokens):
        metrics = self.metrics.get_metrics()
        gpu_cache_usage = metrics["gpu_cache_usage"]
        real_tokens = gpu_cache_usage * MAX_TOKENS
        if real_tokens > predict_tokens:
            self.bias_tokens = real_tokens - predict_tokens
            self.bias_tokens = self.bias_tokens * Bias_factor
        else:
            self.bias_tokens = real_tokens - predict_tokens
            self.bias_tokens = self.bias_tokens * (2-Bias_factor)
        
        return gpu_cache_usage

    def print_intervals(self):
        with self.lock:
            print("=" * 50)
            print("Interval Summary:")
            print("=" * 50)

            for interval_start, requests in sorted(self.intervals.items()):
                prompt_sum = sum(req.prompt_length for req in requests)
                request_count = len(requests)

                S_k = self.get_slope(request_count)
                print(f"Interval Start: {interval_start:.2f}")
                print(f"  Prompt Length Sum: {prompt_sum:.2f}%")
                print(f"  Request Count: {request_count}")
                print(f"  Total mem: {sum(req.get_cumulative_memory_usage(interval_start, S_k*self.interval_length) for req in requests)}")
                print("-" * 50)
            
            print("=" * 50)

    def start_log(self):
        try:
            while True:
                t_start = time.perf_counter()

                total_mem = 0
                current_time = time.time()
                start_time = current_time - (current_time % self.interval_length)
                interval_start = round(start_time, 1)
                requests = self.intervals.get(interval_start, None)

                if requests:
                    request_count = len(requests)
                    S_k = self.get_slope(request_count)
                    total_mem = sum(req.get_cumulative_memory_usage(interval_start, S_k*self.interval_length) for req in requests)
                
                self.cal_bias(total_mem)
    
                t_end = time.perf_counter()
                t_use = t_end - t_start


                if self.log_interval > t_use:
                    time.sleep(self.log_interval - t_use)
        except KeyboardInterrupt:
            self.logger.log("Stopped by (Ctrl+C).")


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



class MemoryPerceptorManager:
    def __init__(self, metrics_manager):
        self.metrics_manager = metrics_manager
        self.mem_pred_instances = {}
        for llm_url, metrics in metrics_manager.metrics_instances.items():
            mem_pred = MemoryPerceptor(llm_url, metrics, PREDICT_INTERVAL)
            self.mem_pred_instances[llm_url] = mem_pred

    def try_add_request(self, urls, msg_id, prompt_length, predicted_time):
        available_llms = []

        for llm_url in urls:
            metrics = self.metrics_manager.get_llm_metrics_sync(llm_url)
            if metrics["waiting"] is True:
                continue

            mem_pred = self.mem_pred_instances[llm_url]

            can_add = mem_pred.try_add_request(msg_id, prompt_length, predicted_time)
            if can_add:
                pred_max_tokens = mem_pred.pred_max_tokens
                available_llms.append((llm_url, pred_max_tokens))

        if available_llms:
            available_llms.sort(key=lambda x: x[1])
            selected_llm = available_llms[0][0]

            for llm_url, _ in available_llms[1:]:
                self.remove_request(msg_id, llm_url)
            return selected_llm
        return None

    def remove_request(self, msg_id, url):
        self.mem_pred_instances[url].remove_request(msg_id)

    def print_info(self):
        for url, mem_pred in self.mem_pred_instances.items():
            print("*"*50, url, "*"*50)
            mem_pred.print_intervals()