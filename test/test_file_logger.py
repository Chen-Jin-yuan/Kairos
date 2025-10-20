import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.logger import FileLogger
import time


logger = FileLogger(log_file_path="test_logs/agent.log")


logger.log("This is an info message.")
time.sleep(1)
logger.log("This is a warning message.", level="WARNING")
time.sleep(1)
logger.log("This is an error message.", level="ERROR")
