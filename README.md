# Kairos
**Kairos** is a multi-agent orchestration system that optimizes the end-to-end latency for multi-agent applications. Kairos consists of a *workflow-aware priority scheduler* and a *memory-aware time-slot dispatcher*. 

The scheduler utilizes a lightweight workflow orchestrator to collect agent-specific data online, based on which it decides the serving priority of the requests to reduce the overall queuing. The dispatcher dispatches the requests among LLM instances based on their memory demands to avoid GPU overloading.

# Dependency
## Environment
* Python 3.10.14
* CUDA 12.8

## Kafka
1. Install the Python module
* `pip install kafka-python`
2. Go to the `docker/kafka` directory and run the Kafka container
* start: `docker-compose up -d`
* stop: `docker-compose down`
3. Verify Kafka setup
* `docker exec -it {container id} /bin/bash`
* `kafka-topics.sh --describe --bootstrap-server {kafka_ip}:{kafka_port}`

## vLLM
To install vLLM, please refer to the official installation guide: https://docs.vllm.ai/en/stable/getting_started/installation/gpu.html

# Key Workflow
* First, build Agents: Each agent is implemented by extending BaseAgentV2. The agent defines how to process input, invoke the LLM via the designated API, and determine the next agent in the workflow.

<details>
<summary>▶️ Click to view code</summary>

```python3
from framework.agent import BaseAgentV2

PROMPT = """You're an assistant.

## YOUR TASK
Solve problems based on user input.

## Output Format
The process of solving the problem and the final answer.

## Input
{input}

## Output:
"""

class TestAgent(BaseAgentV2):
    def __init__(self, agent_name):
        super().__init__(agent_name)

    def _run_impl(self, input_data, llm_url, metadata):
        # Retrieve user input
        user_input = input_data.get("input")
        prompt = PROMPT.format(input=user_input)
    
        # Call the LLM through the 'generate' API
        result = self.generate(prompt, llm_url, metadata)
    
        if result.startswith(prompt):
            result = result[len(prompt):].lstrip()
    
        # Determine the next agent (Frontend if this is the last stage)
        next_agent = "Frontend"
        
        # Return result and next agent
        return {"result": result}, next_agent
```
</details>

* Then, start the Backend: After the agents are defined, they are imported and added to the backend workflow. Each agent is equipped with a request handler to serve high-concurrency requests using multithreading. The LLM engines are launched based on the workflow configuration, which may take some time to fully start up.
<details open>
<summary>▶️ Click to view code</summary>

```python3
from framework.controller import ControllerV2
from framework.workflow import Workflow
import TestAgent1, TestAgent2
import multiprocessing

if __name__ == "__main__":
    # Use 'spawn' start method for multiprocessing
    multiprocessing.set_start_method("spawn")

    # Define LLM engine configuration
    workflow = Workflow()
    workflow.add_engine(engine_type="vllm", model="Meta-Llama-3-8B", dtype="", max_num_seqs="",
                            enable_chunked_prefill="", tensor_parallel_size="", gpu_memory_utilization="", instances="", serving_type="normal")
    
    # Register agents
    workflow.add_agent_llm(agent_name="TestAgent1", agent_class=TestAgent1, use_model="Meta-Llama-3-8B")
    workflow.add_agent_llm(agent_name="TestAgent2", agent_class=TestAgent2, use_model="Meta-Llama-3-8B")
    
    # Launch the controller
    controller = ControllerV2(node_name="node_x", workflow=workflow,
                            init_device_map={"Meta-Llama-3-8B": {"normal": [[1], [2]]}})
    controller.launch_all()
```
</details>

* Finally, start the Frontend: The frontend is configured by defining the message handler, workflow, and dataset. Once the backend is fully running, the frontend can be launched to send requests to the backend.
<details open>
<summary>▶️ Click to view code</summary>

```python3
from framework.frontend import Frontend
from framework.frontend import AgentscopeDataset
from framework.message import KafkaMessageHandler
from framework.workflow import Workflow
from framework.trace import get_trace_file


if __name__ == "__main__":
    # Initialize Kafka message handler for communication
    kafka_msg_handler = KafkaMessageHandler()
    kafka_msg_handler.initialize(bootstrap_servers="[kafka_ip]:[kafka_port]", consumer_target_name="Frontend")
    
    # Define workflow service entry point and input fields
    workflow = Workflow()
    workflow.add_service(service="service", entry_agent_name="entry_agent_name", request_keys=["request_keys"])
    
    # Define dataset
    dataset = AgentscopeDataset("math_dataset", "history_dataset")

    # Configure the frontend
    frontend = Frontend(message_handler=kafka_msg_handler, workflow=workflow, dataset=dataset)
    # Get trace and start
    trace_file_path = get_trace_file(rate="")
    frontend.start_generate(trace_csv_file_path=trace_file_path, sample_interval=1, scale_factor=1)
```
</details>