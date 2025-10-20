import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.agent import BaseAgent


class MyAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run_impl(self, input_data):
        print("running")
        return "testing", "NextAgent"

    def _load_impl(self, device):
        # ...
        print("loading")


# 示例使用
if __name__ == "__main__":
    agent = MyAgent(agent_name="Agent1", message_handler=None)
    agent.load("cuda:0")
    res, target_name = agent.run(input_data="")
    print(res, target_name)
    print(agent.current_device)
    agent.send("Hello, other agents!")
    agent.recv()
    agent.move_to("cuda:1")
    agent.set_flag("flag1")
    agent.set_message_handler(None)
    print(agent.current_device)