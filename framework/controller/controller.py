import multiprocessing
import time
import threading

from framework.dispatcher import RequestDispatcher
from framework.dispatcher import RRDecisionModel
from framework.message import KafkaMessageHandler
from framework.message import Message
from framework.logger import FileLogger

class Controller:
    def __init__(self, node_name, workflow, message_handler, init_device_map):
        self.node_name = node_name
        self.workflow = workflow
        self.message_handler = message_handler
        self.init_device_map = init_device_map
        self.agent_counts = {agent_name: 0 for agent_name in workflow.agents.keys()}
        self.dispatcher_processes = []
        self.agent_processes = {}
        self.agent_cpu_cache_processes = {}
        self.exit_event = multiprocessing.Event()
        self.logger = FileLogger(f"logs/{self.node_name}.log")
        print(f"Controller '{self.node_name}' log file: logs/{self.node_name}.log")
        self.logger.log(f"Controller '{self.node_name}' initialized")

    def send(self, message, target_name):
        self.logger.log(f"{self.node_name} sending message to {target_name}. "
                        f"id={message.get_id()}, "
                        f"service_name={message.get_service_name()}, "
                        f"msg_type={message.get_msg_type()}")

        self.message_handler.add_target_mapping(target_name=target_name)
        self.message_handler.send(message=message, target_name=target_name)

    def set_ready(self, agent_name, replica_number):
        full_name = f"{agent_name}_{replica_number}"
        flag_msg = Message(id=9999, service_name=f"flag", msg_type="event")
        flag_msg.set_origin_data(data={f"{full_name}": "ready"})

        self.send(message=flag_msg, target_name=agent_name)
        self.logger.log(f"{full_name} status set to ready")

    def set_down(self, agent_name, replica_number):
        full_name = f"{agent_name}_{replica_number}"

        flag_msg = Message(id=7777, service_name=f"flag", msg_type="event")
        flag_msg.set_origin_data(data={f"{full_name}": "down"})
        flush_msg = Message(id=8888, service_name=f"flag", msg_type="flush")

        time.sleep(0.1)
        self.send(message=flag_msg, target_name=agent_name)
        self.logger.log(f"{full_name} status set to down")
        time.sleep(0.1)
        self.send(message=flush_msg, target_name=agent_name)
        time.sleep(0.1)
        self.send(message=flush_msg, target_name=agent_name)

    def launch_all_dispatchers(self):
        for agent_name in self.workflow.agents.keys():
            dispatcher_process = multiprocessing.Process(target=start_dispatcher, args=(agent_name,))
            dispatcher_process.start()
            self.dispatcher_processes.append(dispatcher_process)
            self.logger.log(f"start dispatcher '{agent_name}'")

    def launch_all_agents(self, device_map):
        for agent_name, agent_class in self.workflow.agents.items():
            init_launch_number = self.workflow.get_agent_count(agent_name=agent_name)

            for i in range(init_launch_number):
                replica_number = self.agent_counts[agent_name]
                full_name = f"{agent_name}_{replica_number}"
                device = device_map[full_name]
                self.agent_counts[agent_name] += 1

                agent_process = multiprocessing.Process(target=start_agent_replica, args=(agent_name, replica_number, agent_class, device))
                agent_process.start()
                self.agent_processes[full_name] = agent_process

                self.logger.log(f"Start agent replica '{full_name}' on '{device}'.")

    def load_agent_to_cpu(self, agent_name):
        replica_number = self.agent_counts[agent_name]
        self.agent_counts[agent_name] += 1
        full_name = f"{agent_name}_{replica_number}"

        agent_class = self.workflow.agents[agent_name]

        event = multiprocessing.Event()
        event_init = multiprocessing.Event()
        queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=start_agent_replica_to_cpu,
            args=(agent_name, replica_number, agent_class, event, event_init, queue)
        )
        process.start()

        self.agent_cpu_cache_processes[full_name] = {
            "process": process,
            "event": event,
            "event_init": event_init,
            "queue": queue,
            "agent_name": agent_name,
            "replica_number": replica_number
        }

        self.logger.log(f"Agent {full_name} loaded to CPU.")

    def launch_agent_from_cpu(self, agent_name, replica_number, device):
        full_name = f"{agent_name}_{replica_number}"
        self.logger.log(f"Agent {full_name} launch_agent_from_cpu.")

        if full_name in self.agent_cpu_cache_processes:
            agent = self.agent_cpu_cache_processes.pop(full_name)
            agent_process = agent["process"]
            event = agent["event"]
            queue = agent["queue"]
            event_init = agent["event_init"]

            event_init.wait()

            queue.put({"device": device})
            event.set()

            self.agent_processes[full_name] = agent_process

            self.logger.log(f"Agent {full_name} moving to {device}.")

    def stop_agent_replica(self, agent_name, replica_number):
        full_name = f"{agent_name}_{replica_number}"
        self.logger.log(f"Stopping agent process {full_name}...")
        
        if full_name in self.agent_processes:

            self.set_down(agent_name, replica_number)

            process = self.agent_processes[full_name]
            process.terminate()
            process.join()
            del self.agent_processes[full_name]
            self.logger.log(f"Agent process {full_name} terminated.")
        else:
            self.logger.log(f"Agent process {full_name} not found.")

    def stop_all(self):
        self.logger.log("Stopping all processes...")
        for p in self.dispatcher_processes:
            p.terminate()
            p.join()
            self.logger.log(f"Dispatcher process {p.pid} terminated.")

        for full_name, p in self.agent_processes.items():
            p.terminate()
            p.join()
            self.logger.log(f"Agent process {full_name} {p.pid} terminated.")
            
    def listen_for_exit(self):
        while True:
            user_input = input("Type 'exit' to stop all processes: ")
            if user_input.strip().lower() == 'exit':
                self.exit_event.set()
                break
            time.sleep(0.5)

    def launch_all(self):
        self.logger.log("launch_all...")

        self.launch_all_dispatchers()
        
        time.sleep(10)
        self.launch_all_agents(device_map=self.init_device_map)

        exit_thread = threading.Thread(target=self.listen_for_exit)
        exit_thread.start()

        self.exit_event.wait()

        self.stop_all()

        exit_thread.join()

        self.message_handler.close()

        print(f"Controller {self.node_name} exit!")


def start_agent_replica(agent_name, replica_number, agent_class, device):
    full_name = f"{agent_name}_{replica_number}"
        
    kafka_msg_handler = KafkaMessageHandler()
    kafka_msg_handler.initialize(bootstrap_servers="[kafka_ip]:[kafka_port]", consumer_target_name=full_name)

    agent_instance = agent_class(agent_name=agent_name, agent_number=replica_number, message_handler=kafka_msg_handler)

    agent_instance.load(device)
    agent_instance.start()

def start_agent_replica_to_cpu(agent_name, replica_number, agent_class, event, event_init, queue):
    event_init.set()

    full_name = f"{agent_name}_{replica_number}"
        
    kafka_msg_handler = KafkaMessageHandler()
    kafka_msg_handler.initialize(bootstrap_servers="[kafka_ip]:[kafka_port]", consumer_target_name=full_name)

    agent_instance = agent_class(agent_name=agent_name, agent_number=replica_number, message_handler=kafka_msg_handler)

    agent_instance.load("cpu")

    event.wait()  

    if not queue.empty():
        params = queue.get()

    device = params["device"]
    agent_instance.move_to(device)

    agent_instance.start()

def start_dispatcher(agent_name):
    kafka_msg_handler = KafkaMessageHandler()
    kafka_msg_handler.initialize(bootstrap_servers="[kafka_ip]:[kafka_port]", consumer_target_name=agent_name)

    rr_decision_model = RRDecisionModel()
    dispatcher = RequestDispatcher(dispatcher_name=agent_name, decision_model=rr_decision_model, message_handler=kafka_msg_handler)
    dispatcher.start()