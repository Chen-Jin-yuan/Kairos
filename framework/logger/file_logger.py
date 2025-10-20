import os
import time

class FileLogger:
    def __init__(self, log_file_path: str):
        """
        初始化日志记录器，将日志写入指定的文件。

        :param log_file_path: 日志文件路径
        """
        self.log_file_path = log_file_path
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    def log(self, message, level="INFO"):
        """
        将日志信息写入文件。

        :param message: 日志消息
        :param level: 日志级别，例如 "INFO", "WARNING", "ERROR"
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        log_message = f"{timestamp} - {level} - {message}\n"
        
        with open(self.log_file_path, "a") as log_file:
            log_file.write(log_message)
        
    def clear_log_file(self):
        """
        清空日志文件内容。
        """
        with open(self.log_file_path, "w") as log_file:
            log_file.truncate(0)