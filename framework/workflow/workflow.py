from framework.agent import BaseAgent
from typing import List

class Workflow:
    def __init__(self):
        self.agents = {}
        self.agents_count = {}
        self.services = {}
        self.engines = []
        self.agents_llm = {}

    def add_agent(self, agent_name: str, agent_class: BaseAgent, agent_number: int = 1):
        """添加代理到工作流中。

        参数:
        - agent_name (str): 代理的名称。
        - agent_class (class): 代理的类。
        """
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"Agent class '{agent_class.__name__}' must be a subclass of BaseAgent.")
        self.agents[agent_name] = agent_class
        self.agents_count[agent_name] = agent_number

    def get_agent_count(self, agent_name: str):
        return self.agents_count.get(agent_name, None)

    def add_service(self, service: str, entry_agent_name: str, request_keys: List[str]):
        """添加服务到工作流中。

        参数:
        - service (str): 服务的名称。
        - entry_agent_name (str): 入口代理的名称。
        - request_keys (List[str]): 入口请求参数的键。
        """
        self.services[service] = {
            "entry_agent_name": entry_agent_name,
            "request_keys": request_keys
        }

    def add_engine(self, engine_type: str, model: str, dtype: str, max_num_seqs: int, 
                    enable_chunked_prefill: bool, tensor_parallel_size: int, gpu_memory_utilization: float, instances: int, serving_type: str="normal"):
        self.engines.append({
            "engine_type": engine_type,
            "model": model,
            "dtype": dtype,
            "max_num_seqs": max_num_seqs,
            "enable_chunked_prefill": enable_chunked_prefill,
            "tensor_parallel_size": tensor_parallel_size,
            "gpu_memory_utilization": gpu_memory_utilization,
            "instances": instances,
            "serving_type": serving_type
        })

    def add_agent_llm(self, agent_name: str, agent_class: BaseAgent, use_model: str):
        self.agents_llm[agent_name] = {"agent_class": agent_class, "use_model": use_model}

    def __repr__(self):
        return f"Workflow(\n\tAgents={self.agents}\n\tAgents Count={self.agents_count}\n\tServices={self.services}\n\tEngines={self.engines}\n\tAgents_LLM={self.agents_llm}\n)"