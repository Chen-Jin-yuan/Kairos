import requests
import json
from abc import ABC, abstractmethod

from framework.logger import FileLogger

default_temperature = 0
default_top_p = 1
default_top_k = -1
default_max_tokens = 1024

class BaseAgentV2(ABC):
    def __init__(self, agent_name: str):
        """
        初始化Agent。
        """
        self.agent_name = agent_name
        self.agent_full_name = f"{self.agent_name}_v2"
    
        self.logger = FileLogger(f"logs/{self.agent_full_name}.log")
        print(f"Agent '{self.agent_full_name}' log file: logs/{self.agent_full_name}.log")
        self.logger.log(f"Agent '{self.agent_full_name}' initialized")


    @abstractmethod
    def _run_impl(self, input_data, llm_url, metadata):
        """
        用户实现的运行逻辑。
        """
        pass


    def run(self, input_data, llm_url, metadata):
        self.logger.log(f"{self.agent_full_name} starting '_run_impl', with llm url: '{llm_url}'")
        try:
            res, target_name = self._run_impl(input_data, llm_url, metadata)
            self.logger.log(f"{self.agent_full_name} run completed successfully, msg send to '{target_name}'\n\tinput={input_data}\n\toutput={res}")
            return res, target_name
        except Exception as e:
            self.logger.log(f"Error during [run]: {e}", level="ERROR")
            print(f"Error occurred during [run]. Please check the log file: logs/{self.agent_full_name}.log")
            exit(1)

    def load(self, device):
        pass

    # 用户在 run_impl 内调用
    def generate(self, prompt, llm_url, metadata):
        headers = {
            "Content-Type": "application/json"
        }
        # default setting
        data = {
            "prompt": prompt,
            "stream": False,
            "temperature": default_temperature,
            "top_p": default_top_p,
            "top_k": default_top_k,
            "max_tokens": default_max_tokens,
            "metadata": metadata
        }
        json_data = json.dumps(data)
        try:
            response = requests.post(llm_url, data=json_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result['text'][0]
            else:
                self.logger.log(f"Error during [generate]. error code: {response.status_code}, info: {response.text}", level="ERROR")
                return None
        except requests.RequestException as e:
            self.logger.log(f"Error during [generate]: {e}", level="ERROR")
            return None
