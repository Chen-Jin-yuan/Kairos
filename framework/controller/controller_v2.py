import multiprocessing
import time
import threading

from framework.message import KafkaMessageHandler
from framework.dispatcher_v2 import RequestDispatcherV2
from framework.balancer import LoadBalancerServer

from framework.logger import FileLogger
from framework.engine import start_vllm_engine
from framework.engine import start_vllm_engine_remote

class ControllerV2:
    def __init__(self, node_name, workflow, init_device_map, balancer_mode="balancing"):
        self.node_name = node_name
        self.workflow = workflow
        self.init_device_map = init_device_map
        
        self.engine_port = 8000
        self.engine_urls = {}
        self.engine_processes = []
        self.dispatcher_processes = []
        self.agents_use_model = {}

        self.balancer_mode = balancer_mode
        self.balancer_port = 8080
        self.balancer_process = None
        self.balancer_url = f"http://{self.node_name}:{self.balancer_port}/generate"

        self.logger = FileLogger(f"logs/{self.node_name}_v2.log")
        print(f"ControllerV2 '{self.node_name}' log file: logs/{self.node_name}_v2.log")
        self.logger.log(f"ControllerV2 '{self.node_name}' initialized")

    def launch_engines(self):
        for engine in self.workflow.engines:
            self.logger.log(f"get engine setting: '{engine}'")
            engine_type = engine["engine_type"]
            model = engine["model"]
            dtype = engine["dtype"]
            max_num_seqs = engine["max_num_seqs"]
            enable_chunked_prefill = engine["enable_chunked_prefill"]
            tensor_parallel_size = engine["tensor_parallel_size"]
            gpu_memory_utilization = engine["gpu_memory_utilization"]
            serving_type = engine["serving_type"]
            instances = engine["instances"]
            for i in range(instances):
                if engine_type == "vllm":
                    # 获取端口
                    port = self.engine_port
                    self.engine_port += 1
                    # 从 init_device_map 获取设备
                    cuda_visible_devices = self.init_device_map[model][serving_type][i]

                    engine_process = multiprocessing.Process(target=start_vllm_engine, args=(port, model, dtype, max_num_seqs, cuda_visible_devices,
                                enable_chunked_prefill, tensor_parallel_size, gpu_memory_utilization))
                    engine_process.start()
                    self.engine_processes.append(engine_process)

                    url = f"http://{self.node_name}:{port}/generate"

                    if model not in self.engine_urls:
                        self.engine_urls[model] = {}

                    if serving_type not in self.engine_urls[model]:
                        self.engine_urls[model][serving_type] = []

                    self.engine_urls[model][serving_type].append(url)

                    self.logger.log((
                        f"start engine 'port'={port}, "
                        f"'model'={model}, "
                        f"'dtype'={dtype}, "
                        f"'max_num_seqs'={max_num_seqs}, "
                        f"'cuda_visible_devices'={cuda_visible_devices}, "
                        f"'enable_chunked_prefill'={enable_chunked_prefill}, "
                        f"'tensor_parallel_size'={tensor_parallel_size}, "
                        f"'gpu_memory_utilization'={gpu_memory_utilization}, "
                        f"'serving_type'={serving_type}, "
                        f"'url'={url}"
                    ))

                #################################### for remote ####################################
                if engine_type == "vllm_remote":
                    host = "xxx-01" # host
                    # 获取端口
                    port = self.engine_port
                    self.engine_port += 1
                    # 从 init_device_map 获取设备
                    cuda_visible_devices = self.init_device_map[model][serving_type][i]

                    engine_process = multiprocessing.Process(target=start_vllm_engine_remote, args=(host, port, model, dtype, max_num_seqs, cuda_visible_devices,
                                enable_chunked_prefill, tensor_parallel_size, gpu_memory_utilization))
                    engine_process.start()
                    self.engine_processes.append(engine_process)

                    url = f"http://{host}:{port}/generate"

                    if model not in self.engine_urls:
                        self.engine_urls[model] = {}

                    if serving_type not in self.engine_urls[model]:
                        self.engine_urls[model][serving_type] = []

                    self.engine_urls[model][serving_type].append(url)

                    self.logger.log((
                        f"start engine 'port'={port}, "
                        f"'model'={model}, "
                        f"'dtype'={dtype}, "
                        f"'max_num_seqs'={max_num_seqs}, "
                        f"'cuda_visible_devices'={cuda_visible_devices}, "
                        f"'enable_chunked_prefill'={enable_chunked_prefill}, "
                        f"'tensor_parallel_size'={tensor_parallel_size}, "
                        f"'gpu_memory_utilization'={gpu_memory_utilization}, "
                        f"'serving_type'={serving_type}, "
                        f"'url'={url}"
                    ))
                #################################### for remote ####################################

    def launch_balancer(self):
        self.balancer_process = multiprocessing.Process(target=start_balancer, args=(self.node_name, self.engine_urls, self.agents_use_model, "0.0.0.0", self.balancer_port, None, self.balancer_mode))
        self.balancer_process.start()
        self.logger.log(f"start balancer 'port'={self.balancer_port} 'llm_urls'={self.engine_urls} 'agents_info'={self.agents_use_model}")

    def launch_all_dispatchers_with_agent(self):
        """启动所有 dispatcher 进程。"""
        for agent_name, agent_info in self.workflow.agents_llm.items():
            agent_class = agent_info["agent_class"]
            use_model = agent_info["use_model"]
            self.agents_use_model[agent_name] = use_model
            dispatcher_process = multiprocessing.Process(target=start_dispatcher, args=(agent_name, self.balancer_url, agent_class))
            dispatcher_process.start()
            self.dispatcher_processes.append(dispatcher_process)
            self.logger.log(f"start dispatcher with agent '{agent_name}'")

    def stop_all(self):
        """停止所有 dispatcher 和 agent 进程。"""
        self.logger.log("Stopping all processes...")
        for p in self.dispatcher_processes:
            p.terminate()
            p.join()
            self.logger.log(f"Dispatcher process {p.pid} terminated.")

        for e in self.engine_processes:
            e.terminate()
            e.join()
            self.logger.log(f"Engine process {e.pid} terminated.")

        self.balancer_process.terminate()
        self.balancer_process.join()
        self.logger.log(f"Balancer process {self.balancer_process.pid} terminated.")

            
    def listen_for_exit(self):
        """监听输入 exit 命令并退出所有进程。"""
        try:
            while True:
                input("Press CTRL+C to quit")

        except KeyboardInterrupt:
            # 停止所有进程
            self.stop_all()
            print(f"ControllerV2 {self.node_name} exit!")


    def launch_all(self):
        """按顺序启动所有 dispatcher 和 agent 副本，并等待退出命令。"""
        self.logger.log("launch_all...")

        self.launch_engines()

        # 启动所有 dispatcher
        self.launch_all_dispatchers_with_agent()
        
        self.launch_balancer()

        # 启动监听输入的线程
        self.listen_for_exit()



def start_dispatcher(agent_name, balancer_url, agent_class):
    """启动指定代理的 dispatcher 进程。"""
    kafka_msg_handler = KafkaMessageHandler()
    kafka_msg_handler.initialize(bootstrap_servers="[kafka_ip]:[kafka_port]", consumer_target_name=agent_name)

    dispatcher = RequestDispatcherV2(dispatcher_name=agent_name, message_handler=kafka_msg_handler, balancer_url=balancer_url, agent_class=agent_class)
    dispatcher.start()


def start_balancer(node_name, llm_urls, agents_use_model, host, port, root_path, balancer_mode):
    balancer_server = LoadBalancerServer(
        node_name=node_name,
        llm_urls=llm_urls,
        agents_use_model=agents_use_model,
        host=host,
        port=port,
        root_path=root_path,
        mode=balancer_mode
    )
    balancer_server.start_server()