import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.workflow import Workflow
from framework.agent import BaseAgent, BaseAgentV2

class AgentA(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("init agentA")

    def _run_impl(self, input_data):
        print("running")
        return "test", "NextAgent"

    def _load_impl(self, device):
        # ...
        print("loading")

class AgentB(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("init agentB")

    def _run_impl(self, input_data):
        print("running")
        return "test", "NextAgent"

    def _load_impl(self, device):
        # ...
        print("loading")

class AgentC(BaseAgentV2):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("init agentC")

    def _run_impl(self, input_data):
        print("running")
        return "test", "NextAgent"


workflow = Workflow()

workflow.add_agent(agent_name="Agent1", agent_class=AgentA)
workflow.add_agent(agent_name="Agent2", agent_class=AgentB)

workflow.add_service(service="Service1", entry_agent_name="Agent1", request_keys=["text"])
workflow.add_service(service="Service2", entry_agent_name="Agent2", request_keys=["image"])

workflow.add_agent_llm(agent_name="Agent3", agent_class=AgentC, use_model="llama3")
workflow.add_engine(engine_type="vllm", model="llama3", dtype="bfloat16", max_num_seqs=8, instances=2)

print(workflow)
