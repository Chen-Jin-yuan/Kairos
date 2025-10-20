import sys
import os
import time
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.utils import TimeRecorder


if __name__ == "__main__":
    headers = ["Model_Name", "Action_Name", "User", "Others"]
    time_recorder = TimeRecorder(headers=headers, log_file_path="logs/time_recoder_log.csv")

    with time_recorder.measure_time_sync(Model_Name="llama3", Action_Name="sync", User="user", Others=123.4):
        time.sleep(2.5)

    async def async_task():
        async with time_recorder.measure_time_async(Model_Name="llama3", Action_Name="async", Others="xxx", User="user1"):
            await asyncio.sleep(2.5)

    asyncio.run(async_task())