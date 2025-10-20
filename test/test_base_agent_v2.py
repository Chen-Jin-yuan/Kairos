import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.agent import BaseAgentV2


class TestAgent(BaseAgentV2):
    def __init__(self, agent_name):
        super().__init__(agent_name)

    def _run_impl(self, input_data, llm_url):
        prompt = input_data.get("prompt")
        result = self.generate(prompt, llm_url)
        return result, "NextAgent"



if __name__ == "__main__":
    agent = TestAgent(agent_name="TestAgent")

    llm_url = "http://127.0.0.1:8080/generate"

    input_data = {
        "prompt": "Tell me about an ancient invention:"
    }

    result, target_name = agent.run(input_data, llm_url)
    print(result)
    print(target_name)
