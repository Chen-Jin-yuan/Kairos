import time
from contextlib import contextmanager, asynccontextmanager
from framework.logger import CSVLogger

class TimeRecorder:
    def __init__(self, headers, log_file_path):
        """初始化计时记录器并配置 CSV 日志记录器。"""
        self.headers = headers + ["Duration (s)"]
        self.csv_logger = CSVLogger(headers=self.headers, log_file_path=log_file_path)

    @contextmanager
    def measure_time_sync(self, **kwargs):
        """
        同步上下文管理器，记录同步代码的执行时间。
        kwargs 参数应与 headers 中的字段匹配。
        """
        start_time = time.perf_counter()  # 记录开始时间
        yield
        end_time = time.perf_counter()  # 记录结束时间
        elapsed_time = end_time - start_time

        log_data = {**kwargs, "Duration (s)": elapsed_time}
        self.csv_logger.log([log_data.get(header, "") for header in self.headers])

    @asynccontextmanager
    async def measure_time_async(self, **kwargs):
        """
        异步上下文管理器，记录异步代码的执行时间。
        kwargs 参数应与 headers 中的字段匹配。
        """
        start_time = time.perf_counter()  # 记录开始时间
        yield
        end_time = time.perf_counter()  # 记录结束时间
        elapsed_time = end_time - start_time

        log_data = {**kwargs, "Duration (s)": elapsed_time}
        self.csv_logger.log([log_data.get(header, "") for header in self.headers])